"""
Service layer for note CRUD operations.
"""
import logging
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
