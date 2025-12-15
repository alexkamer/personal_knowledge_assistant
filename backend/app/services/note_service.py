"""
Service layer for note CRUD operations.
"""
import logging
from typing import Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.note import Note
from app.schemas.note import NoteCreate, NoteUpdate
from app.services.chunk_processing_service import get_chunk_processing_service

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
            tags=note_data.tags,
        )
        db.add(note)
        await db.commit()
        await db.refresh(note)

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
        result = await db.execute(select(Note).where(Note.id == note_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def list_notes(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[Note], int]:
        """
        List notes with pagination.

        Args:
            db: Database session
            skip: Number of notes to skip
            limit: Maximum number of notes to return

        Returns:
            Tuple of (notes list, total count)
        """
        # Get total count
        count_result = await db.execute(select(func.count(Note.id)))
        total = count_result.scalar_one()

        # Get notes
        result = await db.execute(
            select(Note)
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
        result = await db.execute(select(Note).where(Note.id == note_id))
        note = result.scalar_one_or_none()

        if not note:
            return None

        # Update only provided fields
        update_data = note_data.model_dump(exclude_unset=True)
        content_changed = "content" in update_data

        for field, value in update_data.items():
            setattr(note, field, value)

        await db.commit()
        await db.refresh(note)

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
        Delete a note.

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

        await db.delete(note)
        await db.commit()
        return True
