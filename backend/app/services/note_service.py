"""
Service layer for note CRUD operations.
"""
import logging
import re
import json
from typing import Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.note import Note
from app.schemas.note import NoteCreate, NoteUpdate
from app.services.chunk_processing_service import get_chunk_processing_service
from app.services.vector_service import get_vector_service
from app.services.tag_service import TagService

logger = logging.getLogger(__name__)

# Regex to extract wiki links from Lexical JSON content
WIKI_LINK_PATTERN = re.compile(r'\[\[([^\]]+)\]\]')


class NoteService:
    """Service for managing notes."""

    @staticmethod
    async def create_note(db: AsyncSession, note_data: NoteCreate) -> Note:
        """
        Create a new note and process it for embeddings.

        Args:
            db: Database session
            note_data: Note creation data

        Returns:
            Created note
        """
        note = Note(
            title=note_data.title,
            content=note_data.content,
        )

        # Handle tags
        if note_data.tag_names:
            tags = await TagService.get_or_create_tags(db, note_data.tag_names)
            note.tags_rel = tags

        db.add(note)
        await db.commit()
        await db.refresh(note, ["tags_rel"])

        # Process note for chunking and embeddings
        try:
            chunk_service = get_chunk_processing_service()
            await chunk_service.process_note(db, str(note.id), note.content)
            logger.info(f"Processed chunks for new note {note.id}")
        except Exception as e:
            logger.error(f"Failed to process chunks for note {note.id}: {e}")
            # Don't fail the note creation if chunking fails

        return note

    @staticmethod
    async def get_note(db: AsyncSession, note_id: str) -> Optional[Note]:
        """
        Get a note by ID.

        Args:
            db: Database session
            note_id: Note ID

        Returns:
            Note if found, None otherwise
        """
        result = await db.execute(
            select(Note)
            .where(Note.id == note_id)
            .options(selectinload(Note.tags_rel))
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_notes(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        tag_names: Optional[list[str]] = None,
    ) -> tuple[list[Note], int]:
        """
        List notes with pagination and optional tag filtering.

        Args:
            db: Database session
            skip: Number of notes to skip
            limit: Maximum number of notes to return
            tag_names: Optional list of tag names to filter by (AND logic)

        Returns:
            Tuple of (notes list, total count)
        """
        # Build base query
        query = select(Note).options(selectinload(Note.tags_rel))

        # Apply tag filtering if provided
        if tag_names:
            # Normalize tag names
            normalized_names = [name.strip().lower() for name in tag_names if name.strip()]

            if normalized_names:
                # Join with tags and filter
                from app.models.tag import Tag
                from app.models.note_tag import NoteTag

                for tag_name in normalized_names:
                    # Create subquery for this tag
                    tag_subquery = (
                        select(NoteTag.note_id)
                        .join(Tag, Tag.id == NoteTag.tag_id)
                        .where(Tag.name == tag_name)
                    )
                    query = query.where(Note.id.in_(tag_subquery))

        # Get total count with same filters
        count_query = select(func.count(Note.id))
        if tag_names and normalized_names:
            from app.models.tag import Tag
            from app.models.note_tag import NoteTag

            for tag_name in normalized_names:
                tag_subquery = (
                    select(NoteTag.note_id)
                    .join(Tag, Tag.id == NoteTag.tag_id)
                    .where(Tag.name == tag_name)
                )
                count_query = count_query.where(Note.id.in_(tag_subquery))

        count_result = await db.execute(count_query)
        total = count_result.scalar_one()

        # Get notes
        result = await db.execute(
            query
            .order_by(Note.updated_at.desc())
            .offset(skip)
            .limit(limit)
        )
        notes = list(result.scalars().all())

        return notes, total

    @staticmethod
    async def update_note(
        db: AsyncSession,
        note_id: str,
        note_data: NoteUpdate,
    ) -> Optional[Note]:
        """
        Update a note and reprocess embeddings if content changed.

        Args:
            db: Database session
            note_id: Note ID
            note_data: Note update data

        Returns:
            Updated note if found, None otherwise
        """
        result = await db.execute(
            select(Note)
            .where(Note.id == note_id)
            .options(selectinload(Note.tags_rel))
        )
        note = result.scalar_one_or_none()

        if not note:
            return None

        # Update only provided fields
        update_data = note_data.model_dump(exclude_unset=True)
        content_changed = "content" in update_data

        # Handle tag updates separately
        if "tag_names" in update_data:
            tag_names = update_data.pop("tag_names")
            if tag_names is not None:
                # Replace all tags
                tags = await TagService.get_or_create_tags(db, tag_names)
                note.tags_rel = tags

        for field, value in update_data.items():
            setattr(note, field, value)

        await db.commit()
        await db.refresh(note)

        # Eagerly load the tags_rel relationship
        await db.execute(select(Note).where(Note.id == note.id).options(selectinload(Note.tags_rel)))
        await db.refresh(note, ["tags_rel"])

        # Reprocess chunks if content changed
        if content_changed:
            try:
                chunk_service = get_chunk_processing_service()
                await chunk_service.process_note(db, str(note.id), note.content)
                logger.info(f"Reprocessed chunks for updated note {note.id}")
            except Exception as e:
                logger.error(f"Failed to reprocess chunks for note {note.id}: {e}")
                # Don't fail the update if chunking fails

        return note

    @staticmethod
    async def delete_note(db: AsyncSession, note_id: str) -> bool:
        """
        Delete a note and all its associated chunks.

        This will:
        1. Delete chunk embeddings from ChromaDB
        2. Delete the note from PostgreSQL (chunks cascade delete automatically)

        Args:
            db: Database session
            note_id: Note ID

        Returns:
            True if deleted, False if not found
        """
        result = await db.execute(select(Note).where(Note.id == note_id))
        note = result.scalar_one_or_none()

        if not note:
            return False

        # Delete chunk embeddings from ChromaDB first
        try:
            vector_service = get_vector_service()
            await vector_service.delete_chunks_by_source(
                source_id=note_id,
                source_type="note",
            )
            logger.info(f"Deleted vector embeddings for note {note_id}")
        except Exception as e:
            logger.error(f"Failed to delete vector embeddings for note {note_id}: {e}")
            # Continue with deletion even if vector cleanup fails

        # Delete note from PostgreSQL (chunks will cascade delete)
        await db.delete(note)
        await db.commit()
        logger.info(f"Deleted note {note_id} and its chunks")
        return True

    @staticmethod
    def extract_wiki_links_from_content(content: str) -> set[str]:
        """
        Extract wiki link titles from note content.
        Handles both plain text [[links]] and Lexical JSON format.

        Args:
            content: Note content (plain text or Lexical JSON)

        Returns:
            Set of wiki link titles (case-insensitive, normalized)
        """
        wiki_links = set()

        try:
            # Try to parse as Lexical JSON
            data = json.loads(content)

            # Extract wiki links from Lexical nodes recursively
            def extract_links_recursive(node):
                links = set()
                if isinstance(node, dict):
                    # Check if this is a wikilink node
                    if node.get("type") == "wikilink":
                        note_title = node.get("noteTitle", "")
                        if note_title:
                            links.add(note_title.strip().lower())

                    # Also check text nodes for [[...]] patterns (fallback)
                    elif node.get("type") == "text":
                        text = node.get("text", "")
                        matches = WIKI_LINK_PATTERN.findall(text)
                        links.update(m.strip().lower() for m in matches)

                    # Recursively process children
                    children = node.get("children", [])
                    for child in children:
                        links.update(extract_links_recursive(child))

                elif isinstance(node, list):
                    for item in node:
                        links.update(extract_links_recursive(item))

                return links

            # Extract all wiki links from the parsed JSON
            # Lexical JSON has a root key containing the editor state
            if isinstance(data, dict):
                root = data.get("root", data)  # Handle both with and without root key
                wiki_links = extract_links_recursive(root)

        except (json.JSONDecodeError, KeyError, TypeError):
            # Not JSON, treat as plain text
            matches = WIKI_LINK_PATTERN.findall(content)
            wiki_links.update(m.strip().lower() for m in matches)

        return wiki_links

    @staticmethod
    async def get_backlinks(db: AsyncSession, note_id: str) -> list[Note]:
        """
        Find all notes that link to the specified note.

        Args:
            db: Database session
            note_id: Target note ID

        Returns:
            List of notes that contain wiki links to the target note
        """
        # First, get the target note to know its title
        target_note = await NoteService.get_note(db, note_id)
        if not target_note:
            return []

        target_title_lower = target_note.title.strip().lower()
        logger.info(f"Finding backlinks for note {note_id}, target title: '{target_title_lower}'")

        # Get all notes
        result = await db.execute(
            select(Note)
            .where(Note.id != note_id)  # Exclude the target note itself
            .order_by(Note.updated_at.desc())
        )
        all_notes = list(result.scalars().all())
        logger.info(f"Checking {len(all_notes)} notes for backlinks")

        # Filter notes that contain links to the target note
        backlink_notes = []
        for note in all_notes:
            wiki_links = NoteService.extract_wiki_links_from_content(note.content)
            logger.info(f"Note {note.id} ({note.title[:50]}...) has wiki links: {wiki_links}")
            # Check if any wiki link matches the target note title
            # Use our matching logic: exact, starts with, or contains
            for link_title in wiki_links:
                if (
                    link_title == target_title_lower
                    or target_title_lower.startswith(link_title)
                    or link_title in target_title_lower
                ):
                    logger.info(f"  -> MATCH! '{link_title}' matches '{target_title_lower}'")
                    backlink_notes.append(note)
                    break

        logger.info(f"Found {len(backlink_notes)} backlinks")
        return backlink_notes

    @staticmethod
    async def get_related_notes(
        db: AsyncSession,
        note_id: str,
        limit: int = 5,
    ) -> list[tuple[Note, float]]:
        """
        Find semantically related notes using vector similarity.

        Args:
            db: Database session
            note_id: Target note ID
            limit: Maximum number of related notes to return

        Returns:
            List of tuples (note, similarity_score) sorted by relevance
        """
        from app.services.embedding_service import get_embedding_service
        from app.services.vector_service import get_vector_service
        from collections import defaultdict

        # Get the target note
        target_note = await NoteService.get_note(db, note_id)
        if not target_note:
            return []

        # Generate embedding for the note's content
        try:
            embedding_service = get_embedding_service()
            # Use the full note content for semantic search
            note_embedding = embedding_service.embed_text(target_note.content)
        except Exception as e:
            logger.error(f"Failed to generate embedding for note {note_id}: {e}")
            return []

        # Search for similar chunks in the vector database
        try:
            vector_service = get_vector_service()
            results = await vector_service.search_similar_chunks(
                query_embedding=note_embedding,
                n_results=limit * 3,  # Get more results to aggregate by note
                source_type="note",  # Only search notes, not documents
            )
        except Exception as e:
            logger.error(f"Failed to search similar chunks: {e}")
            return []

        # Aggregate similarity scores by note_id
        note_scores = defaultdict(list)
        for i, chunk_id in enumerate(results["ids"][0]):
            metadata = results["metadatas"][0][i]
            source_id = metadata.get("source_id")
            distance = results["distances"][0][i]

            # Skip the note itself
            if source_id == note_id:
                continue

            # Convert distance to similarity (lower distance = higher similarity)
            # ChromaDB uses L2 distance, convert to similarity score (0-1)
            similarity = 1 / (1 + distance)
            note_scores[source_id].append(similarity)

        # Calculate average similarity for each note
        note_similarities = [
            (source_id, sum(scores) / len(scores))
            for source_id, scores in note_scores.items()
        ]

        # Sort by similarity (highest first) and limit
        note_similarities.sort(key=lambda x: x[1], reverse=True)
        top_note_ids = [note_id for note_id, _ in note_similarities[:limit]]

        # Fetch the actual note objects
        if not top_note_ids:
            return []

        result = await db.execute(
            select(Note)
            .where(Note.id.in_(top_note_ids))
            .options(selectinload(Note.tags_rel))
        )
        notes_dict = {note.id: note for note in result.scalars().all()}

        # Return notes in order of similarity with scores
        related_notes = []
        for note_id, score in note_similarities[:limit]:
            if note_id in notes_dict:
                related_notes.append((notes_dict[note_id], score))

        logger.info(f"Found {len(related_notes)} related notes for {note_id}")
        return related_notes
