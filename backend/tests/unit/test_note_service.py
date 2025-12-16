"""
Unit tests for the Note service.
"""
import pytest
from unittest.mock import patch, AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.note_service import NoteService
from app.schemas.note import NoteCreate, NoteUpdate
from app.models.note import Note


class TestNoteService:
    """Test suite for NoteService."""

    @pytest.mark.asyncio
    @patch('app.services.note_service.get_chunk_processing_service')
    async def test_create_note_basic(self, mock_chunk_service, test_db: AsyncSession):
        """Test creating a basic note."""
        # Mock chunk processing
        mock_chunk_instance = AsyncMock()
        mock_chunk_service.return_value = mock_chunk_instance

        note_data = NoteCreate(
            title="Test Note",
            content="This is a test note",
        )

        note = await NoteService.create_note(test_db, note_data)

        assert note.id is not None
        assert note.title == "Test Note"
        assert note.content == "This is a test note"

        # Verify chunk processing was called
        mock_chunk_instance.process_note.assert_called_once()

    @pytest.mark.asyncio
    @patch('app.services.note_service.TagService.get_or_create_tags')
    @patch('app.services.note_service.get_chunk_processing_service')
    async def test_create_note_with_tags(
        self, mock_chunk_service, mock_tag_service, test_db: AsyncSession
    ):
        """Test creating a note with tags."""
        # Mock services
        mock_chunk_instance = AsyncMock()
        mock_chunk_service.return_value = mock_chunk_instance
        mock_tag_service.return_value = []

        note_data = NoteCreate(
            title="Tagged Note",
            content="Content",
            tag_names=["tag1", "tag2"],
        )

        note = await NoteService.create_note(test_db, note_data)

        assert note.id is not None
        assert note.title == "Tagged Note"

        # Verify tags were processed
        mock_tag_service.assert_called_once_with(test_db, ["tag1", "tag2"])

    @pytest.mark.asyncio
    @patch('app.services.note_service.get_chunk_processing_service')
    async def test_create_note_chunk_processing_failure(
        self, mock_chunk_service, test_db: AsyncSession
    ):
        """Test that note creation succeeds even if chunk processing fails."""
        # Mock chunk processing to raise an error
        mock_chunk_instance = AsyncMock()
        mock_chunk_instance.process_note.side_effect = Exception("Chunk processing failed")
        mock_chunk_service.return_value = mock_chunk_instance

        note_data = NoteCreate(
            title="Test Note",
            content="Content",
        )

        # Should not raise an exception
        note = await NoteService.create_note(test_db, note_data)

        assert note.id is not None
        assert note.title == "Test Note"

    @pytest.mark.asyncio
    @patch('app.services.note_service.get_chunk_processing_service')
    async def test_get_note(self, mock_chunk_service, test_db: AsyncSession):
        """Test getting a note by ID."""
        # Mock chunk processing
        mock_chunk_instance = AsyncMock()
        mock_chunk_service.return_value = mock_chunk_instance

        # Create a note first
        note_data = NoteCreate(title="Test", content="Content")
        created = await NoteService.create_note(test_db, note_data)

        # Get it back
        note = await NoteService.get_note(test_db, str(created.id))

        assert note is not None
        assert note.id == created.id
        assert note.title == "Test"

    @pytest.mark.asyncio
    async def test_get_note_not_found(self, test_db: AsyncSession):
        """Test getting a non-existent note."""
        note = await NoteService.get_note(test_db, "nonexistent-id")

        assert note is None

    @pytest.mark.asyncio
    @patch('app.services.note_service.get_chunk_processing_service')
    async def test_list_notes_empty(self, mock_chunk_service, test_db: AsyncSession):
        """Test listing notes when database is empty."""
        notes, total = await NoteService.list_notes(test_db)

        assert notes == []
        assert total == 0

    @pytest.mark.asyncio
    @patch('app.services.note_service.get_chunk_processing_service')
    async def test_list_notes(self, mock_chunk_service, test_db: AsyncSession):
        """Test listing notes."""
        # Mock chunk processing
        mock_chunk_instance = AsyncMock()
        mock_chunk_service.return_value = mock_chunk_instance

        # Create multiple notes
        for i in range(3):
            note_data = NoteCreate(title=f"Note {i}", content=f"Content {i}")
            await NoteService.create_note(test_db, note_data)

        notes, total = await NoteService.list_notes(test_db)

        assert len(notes) == 3
        assert total == 3

    @pytest.mark.asyncio
    @patch('app.services.note_service.get_chunk_processing_service')
    async def test_list_notes_pagination(self, mock_chunk_service, test_db: AsyncSession):
        """Test listing notes with pagination."""
        # Mock chunk processing
        mock_chunk_instance = AsyncMock()
        mock_chunk_service.return_value = mock_chunk_instance

        # Create 5 notes
        for i in range(5):
            note_data = NoteCreate(title=f"Note {i}", content=f"Content {i}")
            await NoteService.create_note(test_db, note_data)

        # Get first 2
        notes, total = await NoteService.list_notes(test_db, skip=0, limit=2)

        assert len(notes) == 2
        assert total == 5

        # Get next 2
        notes, total = await NoteService.list_notes(test_db, skip=2, limit=2)

        assert len(notes) == 2
        assert total == 5

    @pytest.mark.asyncio
    @patch('app.services.note_service.get_chunk_processing_service')
    async def test_update_note(self, mock_chunk_service, test_db: AsyncSession):
        """Test updating a note."""
        # Mock chunk processing
        mock_chunk_instance = AsyncMock()
        mock_chunk_service.return_value = mock_chunk_instance

        # Create note
        note_data = NoteCreate(title="Original", content="Original content")
        note = await NoteService.create_note(test_db, note_data)

        # Update it
        update_data = NoteUpdate(
            title="Updated",
            content="Updated content",
        )
        updated = await NoteService.update_note(test_db, str(note.id), update_data)

        assert updated is not None
        assert updated.title == "Updated"
        assert updated.content == "Updated content"

        # Verify chunk reprocessing was called
        # process_note should be called twice: once for create, once for update
        assert mock_chunk_instance.process_note.call_count == 2

    @pytest.mark.asyncio
    @patch('app.services.note_service.get_chunk_processing_service')
    async def test_update_note_partial(self, mock_chunk_service, test_db: AsyncSession):
        """Test partial update of a note."""
        # Mock chunk processing
        mock_chunk_instance = AsyncMock()
        mock_chunk_service.return_value = mock_chunk_instance

        # Create note
        note_data = NoteCreate(title="Original", content="Original content")
        note = await NoteService.create_note(test_db, note_data)

        # Update only title
        update_data = NoteUpdate(title="New Title")
        updated = await NoteService.update_note(test_db, str(note.id), update_data)

        assert updated is not None
        assert updated.title == "New Title"
        assert updated.content == "Original content"  # Should remain unchanged

    @pytest.mark.asyncio
    async def test_update_note_not_found(self, test_db: AsyncSession):
        """Test updating a non-existent note."""
        update_data = NoteUpdate(title="New Title")
        updated = await NoteService.update_note(test_db, "nonexistent-id", update_data)

        assert updated is None

    @pytest.mark.asyncio
    @patch('app.services.note_service.get_vector_service')
    @patch('app.services.note_service.get_chunk_processing_service')
    async def test_delete_note(
        self, mock_chunk_service, mock_vector_service, test_db: AsyncSession
    ):
        """Test deleting a note."""
        # Mock services
        mock_chunk_instance = AsyncMock()
        mock_chunk_service.return_value = mock_chunk_instance
        mock_vector_instance = AsyncMock()
        mock_vector_service.return_value = mock_vector_instance

        # Create note
        note_data = NoteCreate(title="To Delete", content="Content")
        note = await NoteService.create_note(test_db, note_data)

        # Delete it
        deleted = await NoteService.delete_note(test_db, str(note.id))

        assert deleted is True

        # Verify it's gone
        result = await NoteService.get_note(test_db, str(note.id))
        assert result is None

        # Verify vector chunks were deleted
        mock_vector_instance.delete_chunks_by_source.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_note_not_found(self, test_db: AsyncSession):
        """Test deleting a non-existent note."""
        deleted = await NoteService.delete_note(test_db, "nonexistent-id")

        assert deleted is False

