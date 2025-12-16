"""
Unit tests for the Document service.
"""
import pytest
from unittest.mock import patch, AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.document_service import DocumentService
from app.schemas.document import DocumentCreate
from app.models.document import Document


class TestDocumentService:
    """Test suite for DocumentService."""

    @pytest.mark.asyncio
    @patch('app.services.document_service.get_chunk_processing_service')
    async def test_create_document(self, mock_chunk_service, test_db: AsyncSession):
        """Test creating a document."""
        # Mock chunk processing
        mock_chunk_instance = AsyncMock()
        mock_chunk_service.return_value = mock_chunk_instance

        document_data = DocumentCreate(
            filename="test.pdf",
            file_path="/uploads/test.pdf",
            file_type="application/pdf",
            file_size=1024,
            content="This is test document content",
        )

        document = await DocumentService.create_document(test_db, document_data)

        assert document.id is not None
        assert document.filename == "test.pdf"
        assert document.file_path == "/uploads/test.pdf"
        assert document.file_type == "application/pdf"
        assert document.file_size == 1024
        assert document.content == "This is test document content"

        # Verify chunk processing was called
        mock_chunk_instance.process_document.assert_called_once()

    @pytest.mark.asyncio
    @patch('app.services.document_service.get_chunk_processing_service')
    async def test_create_document_with_metadata(self, mock_chunk_service, test_db: AsyncSession):
        """Test creating a document with metadata."""
        # Mock chunk processing
        mock_chunk_instance = AsyncMock()
        mock_chunk_service.return_value = mock_chunk_instance

        document_data = DocumentCreate(
            filename="report.pdf",
            file_path="/uploads/report.pdf",
            file_type="application/pdf",
            file_size=2048,
            content="Report content",
            metadata_='{"author": "John Doe", "pages": 10}',
        )

        document = await DocumentService.create_document(test_db, document_data)

        assert document.id is not None
        assert document.metadata_ == '{"author": "John Doe", "pages": 10}'

    @pytest.mark.asyncio
    @patch('app.services.document_service.get_chunk_processing_service')
    async def test_create_document_chunk_processing_failure(
        self, mock_chunk_service, test_db: AsyncSession
    ):
        """Test that document creation succeeds even if chunk processing fails."""
        # Mock chunk processing to raise an error
        mock_chunk_instance = AsyncMock()
        mock_chunk_instance.process_document.side_effect = Exception("Processing failed")
        mock_chunk_service.return_value = mock_chunk_instance

        document_data = DocumentCreate(
            filename="test.pdf",
            file_path="/uploads/test.pdf",
            file_type="application/pdf",
            file_size=1024,
            content="Content",
        )

        # Should not raise an exception
        document = await DocumentService.create_document(test_db, document_data)

        assert document.id is not None
        assert document.filename == "test.pdf"

    @pytest.mark.asyncio
    @patch('app.services.document_service.get_chunk_processing_service')
    async def test_get_document(self, mock_chunk_service, test_db: AsyncSession):
        """Test getting a document by ID."""
        # Mock chunk processing
        mock_chunk_instance = AsyncMock()
        mock_chunk_service.return_value = mock_chunk_instance

        # Create a document first
        document_data = DocumentCreate(
            filename="test.pdf",
            file_path="/uploads/test.pdf",
            file_type="application/pdf",
            file_size=1024,
            content="Content",
        )
        created = await DocumentService.create_document(test_db, document_data)

        # Get it back
        document = await DocumentService.get_document(test_db, str(created.id))

        assert document is not None
        assert document.id == created.id
        assert document.filename == "test.pdf"

    @pytest.mark.asyncio
    async def test_get_document_not_found(self, test_db: AsyncSession):
        """Test getting a non-existent document."""
        document = await DocumentService.get_document(test_db, "nonexistent-id")

        assert document is None

    @pytest.mark.asyncio
    async def test_list_documents_empty(self, test_db: AsyncSession):
        """Test listing documents when database is empty."""
        documents, total = await DocumentService.list_documents(test_db)

        assert documents == []
        assert total == 0

    @pytest.mark.asyncio
    @patch('app.services.document_service.get_chunk_processing_service')
    async def test_list_documents(self, mock_chunk_service, test_db: AsyncSession):
        """Test listing documents."""
        # Mock chunk processing
        mock_chunk_instance = AsyncMock()
        mock_chunk_service.return_value = mock_chunk_instance

        # Create multiple documents
        for i in range(3):
            document_data = DocumentCreate(
                filename=f"doc{i}.pdf",
                file_path=f"/uploads/doc{i}.pdf",
                file_type="application/pdf",
                file_size=1024 * (i + 1),
                content=f"Content {i}",
            )
            await DocumentService.create_document(test_db, document_data)

        documents, total = await DocumentService.list_documents(test_db)

        assert len(documents) == 3
        assert total == 3

    @pytest.mark.asyncio
    @patch('app.services.document_service.get_chunk_processing_service')
    async def test_list_documents_pagination(self, mock_chunk_service, test_db: AsyncSession):
        """Test listing documents with pagination."""
        # Mock chunk processing
        mock_chunk_instance = AsyncMock()
        mock_chunk_service.return_value = mock_chunk_instance

        # Create 5 documents
        for i in range(5):
            document_data = DocumentCreate(
                filename=f"doc{i}.pdf",
                file_path=f"/uploads/doc{i}.pdf",
                file_type="application/pdf",
                file_size=1024,
                content=f"Content {i}",
            )
            await DocumentService.create_document(test_db, document_data)

        # Get first 2
        documents, total = await DocumentService.list_documents(test_db, skip=0, limit=2)

        assert len(documents) == 2
        assert total == 5

        # Get next 2
        documents, total = await DocumentService.list_documents(test_db, skip=2, limit=2)

        assert len(documents) == 2
        assert total == 5

    @pytest.mark.asyncio
    @patch('app.services.document_service.get_chunk_processing_service')
    async def test_list_documents_ordered_by_created_at(
        self, mock_chunk_service, test_db: AsyncSession
    ):
        """Test that documents are listed in reverse chronological order."""
        # Mock chunk processing
        mock_chunk_instance = AsyncMock()
        mock_chunk_service.return_value = mock_chunk_instance

        # Create documents
        doc1_data = DocumentCreate(
            filename="first.pdf",
            file_path="/uploads/first.pdf",
            file_type="application/pdf",
            file_size=1024,
            content="First",
        )
        doc1 = await DocumentService.create_document(test_db, doc1_data)

        doc2_data = DocumentCreate(
            filename="second.pdf",
            file_path="/uploads/second.pdf",
            file_type="application/pdf",
            file_size=1024,
            content="Second",
        )
        doc2 = await DocumentService.create_document(test_db, doc2_data)

        documents, total = await DocumentService.list_documents(test_db)

        # Verify both documents are returned
        assert len(documents) == 2
        assert total == 2

        # Verify they're ordered by created_at descending
        assert documents[0].created_at >= documents[1].created_at

    @pytest.mark.asyncio
    @patch('app.services.document_service.get_vector_service')
    @patch('app.services.document_service.get_chunk_processing_service')
    async def test_delete_document(
        self, mock_chunk_service, mock_vector_service, test_db: AsyncSession
    ):
        """Test deleting a document."""
        # Mock services
        mock_chunk_instance = AsyncMock()
        mock_chunk_service.return_value = mock_chunk_instance
        mock_vector_instance = AsyncMock()
        mock_vector_service.return_value = mock_vector_instance

        # Create a document
        document_data = DocumentCreate(
            filename="to_delete.pdf",
            file_path="/uploads/to_delete.pdf",
            file_type="application/pdf",
            file_size=1024,
            content="Content to delete",
        )
        document = await DocumentService.create_document(test_db, document_data)

        # Delete it
        deleted = await DocumentService.delete_document(test_db, str(document.id))

        assert deleted is True

        # Verify it's gone
        result = await DocumentService.get_document(test_db, str(document.id))
        assert result is None

        # Verify vector chunks were deleted
        mock_vector_instance.delete_chunks_by_source.assert_called_once_with(
            source_id=str(document.id),
            source_type="document",
        )

    @pytest.mark.asyncio
    async def test_delete_document_not_found(self, test_db: AsyncSession):
        """Test deleting a non-existent document."""
        deleted = await DocumentService.delete_document(test_db, "nonexistent-id")

        assert deleted is False

    @pytest.mark.asyncio
    @patch('app.services.document_service.get_vector_service')
    @patch('app.services.document_service.get_chunk_processing_service')
    async def test_delete_document_vector_cleanup_failure(
        self, mock_chunk_service, mock_vector_service, test_db: AsyncSession
    ):
        """Test that document deletion continues even if vector cleanup fails."""
        # Mock services
        mock_chunk_instance = AsyncMock()
        mock_chunk_service.return_value = mock_chunk_instance
        mock_vector_instance = AsyncMock()
        mock_vector_instance.delete_chunks_by_source.side_effect = Exception("Vector cleanup failed")
        mock_vector_service.return_value = mock_vector_instance

        # Create a document
        document_data = DocumentCreate(
            filename="test.pdf",
            file_path="/uploads/test.pdf",
            file_type="application/pdf",
            file_size=1024,
            content="Content",
        )
        document = await DocumentService.create_document(test_db, document_data)

        # Delete should succeed even though vector cleanup fails
        deleted = await DocumentService.delete_document(test_db, str(document.id))

        assert deleted is True

        # Verify document is still deleted from database
        result = await DocumentService.get_document(test_db, str(document.id))
        assert result is None
