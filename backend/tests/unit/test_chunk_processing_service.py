"""
Unit tests for the ChunkProcessingService.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4

from app.services.chunk_processing_service import ChunkProcessingService, get_chunk_processing_service
from app.models.chunk import Chunk


class TestChunkProcessingService:
    """Test suite for ChunkProcessingService."""

    @patch('app.services.chunk_processing_service.get_vector_service')
    @patch('app.services.chunk_processing_service.get_embedding_service')
    @patch('app.services.chunk_processing_service.SemanticChunker')
    def test_initialization_semantic(self, mock_semantic_chunker, mock_embedding, mock_vector):
        """Test initialization with semantic chunker."""
        mock_embedding.return_value = Mock()
        mock_vector.return_value = Mock()
        mock_semantic_chunker.return_value = Mock()

        service = ChunkProcessingService(use_semantic=True)

        assert service.use_semantic is True
        assert service.semantic_chunker is not None
        mock_semantic_chunker.assert_called_once_with(
            min_chunk_size=256,
            max_chunk_size=768
        )

    @patch('app.services.chunk_processing_service.settings')
    @patch('app.services.chunk_processing_service.get_vector_service')
    @patch('app.services.chunk_processing_service.get_embedding_service')
    @patch('app.services.chunk_processing_service.TextChunker')
    def test_initialization_basic(self, mock_text_chunker, mock_embedding, mock_vector, mock_settings):
        """Test initialization with basic chunker."""
        mock_settings.chunk_size = 512
        mock_settings.chunk_overlap = 50
        mock_embedding.return_value = Mock()
        mock_vector.return_value = Mock()
        mock_text_chunker.return_value = Mock()

        service = ChunkProcessingService(use_semantic=False)

        assert service.use_semantic is False
        assert service.basic_chunker is not None
        mock_text_chunker.assert_called_once_with(
            chunk_size=512,
            chunk_overlap=50
        )

    @pytest.mark.asyncio
    @patch('app.services.chunk_processing_service.get_vector_service')
    @patch('app.services.chunk_processing_service.get_embedding_service')
    @patch('app.services.chunk_processing_service.SemanticChunker')
    async def test_process_note_success(self, mock_semantic_chunker, mock_embedding, mock_vector):
        """Test successful note processing."""
        # Mock services
        mock_embedding_service = Mock()
        mock_embedding_service.embed_batch.return_value = [[0.1, 0.2], [0.3, 0.4]]
        mock_embedding.return_value = mock_embedding_service

        mock_vector_service = AsyncMock()
        mock_vector_service.delete_chunks_by_source = AsyncMock()
        mock_vector_service.add_batch_embeddings = AsyncMock()
        mock_vector.return_value = mock_vector_service

        # Mock semantic chunker
        mock_chunk1 = Mock()
        mock_chunk1.content = "First chunk content"
        mock_chunk1.metadata = Mock()
        mock_chunk1.metadata.token_count = 50
        mock_chunk1.metadata.content_type = "narrative"
        mock_chunk1.metadata.heading_hierarchy = []
        mock_chunk1.metadata.section_title = None
        mock_chunk1.metadata.has_code = False
        mock_chunk1.metadata.semantic_density = 0.7

        mock_chunk2 = Mock()
        mock_chunk2.content = "Second chunk content"
        mock_chunk2.metadata = Mock()
        mock_chunk2.metadata.token_count = 60
        mock_chunk2.metadata.content_type = "narrative"
        mock_chunk2.metadata.heading_hierarchy = []
        mock_chunk2.metadata.section_title = None
        mock_chunk2.metadata.has_code = False
        mock_chunk2.metadata.semantic_density = 0.8

        mock_chunker_instance = Mock()
        mock_chunker_instance.split_text.return_value = [mock_chunk1, mock_chunk2]
        mock_semantic_chunker.return_value = mock_chunker_instance

        service = ChunkProcessingService(use_semantic=True)

        # Mock database
        mock_db = AsyncMock()
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.add = Mock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        mock_db.delete = AsyncMock()

        # Process note
        note_id = str(uuid4())
        result = await service.process_note(
            db=mock_db,
            note_id=note_id,
            content="Test note content"
        )

        # Verify chunking was called
        mock_chunker_instance.split_text.assert_called_once_with("Test note content")

        # Verify embeddings were generated
        mock_embedding_service.embed_batch.assert_called_once()

        # Verify chunks were added to database
        assert mock_db.add.call_count == 2

        # Verify vector service was called
        mock_vector_service.add_batch_embeddings.assert_called_once()

    @pytest.mark.asyncio
    @patch('app.services.chunk_processing_service.get_vector_service')
    @patch('app.services.chunk_processing_service.get_embedding_service')
    @patch('app.services.chunk_processing_service.SemanticChunker')
    async def test_process_note_no_chunks(self, mock_semantic_chunker, mock_embedding, mock_vector):
        """Test note processing when no chunks are generated."""
        mock_embedding.return_value = Mock()
        mock_vector_service = AsyncMock()
        mock_vector_service.delete_chunks_by_source = AsyncMock()
        mock_vector.return_value = mock_vector_service

        # Mock semantic chunker returning empty list
        mock_chunker_instance = Mock()
        mock_chunker_instance.split_text.return_value = []
        mock_semantic_chunker.return_value = mock_chunker_instance

        service = ChunkProcessingService(use_semantic=True)

        # Mock database
        mock_db = AsyncMock()
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        # Process note
        result = await service.process_note(
            db=mock_db,
            note_id=str(uuid4()),
            content=""
        )

        assert result == []

    @pytest.mark.asyncio
    @patch('app.services.chunk_processing_service.settings')
    @patch('app.services.chunk_processing_service.get_vector_service')
    @patch('app.services.chunk_processing_service.get_embedding_service')
    @patch('app.services.chunk_processing_service.TextChunker')
    async def test_process_note_basic_chunker(self, mock_text_chunker, mock_embedding, mock_vector, mock_settings):
        """Test note processing with basic chunker."""
        mock_settings.chunk_size = 512
        mock_settings.chunk_overlap = 50

        # Mock services
        mock_embedding_service = Mock()
        mock_embedding_service.embed_batch.return_value = [[0.1, 0.2]]
        mock_embedding.return_value = mock_embedding_service

        mock_vector_service = AsyncMock()
        mock_vector_service.delete_chunks_by_source = AsyncMock()
        mock_vector_service.add_batch_embeddings = AsyncMock()
        mock_vector.return_value = mock_vector_service

        # Mock basic chunker
        mock_chunker_instance = Mock()
        mock_chunker_instance.split_text.return_value = ["Chunk text"]
        mock_chunker_instance.count_tokens.return_value = 50
        mock_text_chunker.return_value = mock_chunker_instance

        service = ChunkProcessingService(use_semantic=False)

        # Mock database
        mock_db = AsyncMock()
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.add = Mock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        # Process note
        result = await service.process_note(
            db=mock_db,
            note_id=str(uuid4()),
            content="Test content"
        )

        # Verify basic chunker was used
        mock_chunker_instance.split_text.assert_called_once_with("Test content")
        assert mock_db.add.call_count == 1

    @pytest.mark.asyncio
    @patch('app.services.chunk_processing_service.settings')
    @patch('app.services.chunk_processing_service.get_vector_service')
    @patch('app.services.chunk_processing_service.get_embedding_service')
    @patch('app.services.chunk_processing_service.TextChunker')
    async def test_process_note_basic_chunker_no_chunks(self, mock_text_chunker, mock_embedding, mock_vector, mock_settings):
        """Test note processing with basic chunker returning no chunks."""
        mock_settings.chunk_size = 512
        mock_settings.chunk_overlap = 50

        mock_embedding.return_value = Mock()
        mock_vector_service = AsyncMock()
        mock_vector_service.delete_chunks_by_source = AsyncMock()
        mock_vector.return_value = mock_vector_service

        # Mock basic chunker returning empty list
        mock_chunker_instance = Mock()
        mock_chunker_instance.split_text.return_value = []
        mock_text_chunker.return_value = mock_chunker_instance

        service = ChunkProcessingService(use_semantic=False)

        # Mock database
        mock_db = AsyncMock()
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        # Process note
        result = await service.process_note(
            db=mock_db,
            note_id=str(uuid4()),
            content=""
        )

        assert result == []

    @pytest.mark.asyncio
    @patch('app.services.chunk_processing_service.settings')
    @patch('app.services.chunk_processing_service.get_vector_service')
    @patch('app.services.chunk_processing_service.get_embedding_service')
    @patch('app.services.chunk_processing_service.TextChunker')
    async def test_process_document_basic_chunker_no_chunks(self, mock_text_chunker, mock_embedding, mock_vector, mock_settings):
        """Test document processing with basic chunker returning no chunks."""
        mock_settings.chunk_size = 512
        mock_settings.chunk_overlap = 50

        mock_embedding.return_value = Mock()
        mock_vector_service = AsyncMock()
        mock_vector_service.delete_chunks_by_source = AsyncMock()
        mock_vector.return_value = mock_vector_service

        # Mock basic chunker returning empty list
        mock_chunker_instance = Mock()
        mock_chunker_instance.split_text.return_value = []
        mock_text_chunker.return_value = mock_chunker_instance

        service = ChunkProcessingService(use_semantic=False)

        # Mock database
        mock_db = AsyncMock()
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        # Process document
        result = await service.process_document(
            db=mock_db,
            document_id=str(uuid4()),
            content=""
        )

        assert result == []

    @pytest.mark.asyncio
    @patch('app.services.chunk_processing_service.settings')
    @patch('app.services.chunk_processing_service.get_vector_service')
    @patch('app.services.chunk_processing_service.get_embedding_service')
    @patch('app.services.chunk_processing_service.TextChunker')
    async def test_process_document_basic_chunker(self, mock_text_chunker, mock_embedding, mock_vector, mock_settings):
        """Test document processing with basic chunker."""
        mock_settings.chunk_size = 512
        mock_settings.chunk_overlap = 50

        # Mock services
        mock_embedding_service = Mock()
        mock_embedding_service.embed_batch.return_value = [[0.1, 0.2]]
        mock_embedding.return_value = mock_embedding_service

        mock_vector_service = AsyncMock()
        mock_vector_service.delete_chunks_by_source = AsyncMock()
        mock_vector_service.add_batch_embeddings = AsyncMock()
        mock_vector.return_value = mock_vector_service

        # Mock basic chunker
        mock_chunker_instance = Mock()
        mock_chunker_instance.split_text.return_value = ["Document chunk"]
        mock_chunker_instance.count_tokens.return_value = 60
        mock_text_chunker.return_value = mock_chunker_instance

        service = ChunkProcessingService(use_semantic=False)

        # Mock database
        mock_db = AsyncMock()
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.add = Mock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        # Process document
        document_id = str(uuid4())
        result = await service.process_document(
            db=mock_db,
            document_id=document_id,
            content="Test document content"
        )

        # Verify basic chunker was used
        mock_chunker_instance.split_text.assert_called_once_with("Test document content")
        assert mock_db.add.call_count == 1

        # Verify metadata has document type
        call_args = mock_vector_service.add_batch_embeddings.call_args
        metadatas = call_args[1]["metadatas"]
        assert metadatas[0]["source_type"] == "document"
        assert metadatas[0]["source_id"] == document_id

    @pytest.mark.asyncio
    @patch('app.services.chunk_processing_service.get_vector_service')
    @patch('app.services.chunk_processing_service.get_embedding_service')
    @patch('app.services.chunk_processing_service.SemanticChunker')
    async def test_process_document_success(self, mock_semantic_chunker, mock_embedding, mock_vector):
        """Test successful document processing."""
        # Mock services
        mock_embedding_service = Mock()
        mock_embedding_service.embed_batch.return_value = [[0.1, 0.2]]
        mock_embedding.return_value = mock_embedding_service

        mock_vector_service = AsyncMock()
        mock_vector_service.delete_chunks_by_source = AsyncMock()
        mock_vector_service.add_batch_embeddings = AsyncMock()
        mock_vector.return_value = mock_vector_service

        # Mock semantic chunker
        mock_chunk = Mock()
        mock_chunk.content = "Document chunk content"
        mock_chunk.metadata = Mock()
        mock_chunk.metadata.token_count = 50
        mock_chunk.metadata.content_type = "narrative"
        mock_chunk.metadata.heading_hierarchy = []
        mock_chunk.metadata.section_title = "Introduction"
        mock_chunk.metadata.has_code = False
        mock_chunk.metadata.semantic_density = 0.7

        mock_chunker_instance = Mock()
        mock_chunker_instance.split_text.return_value = [mock_chunk]
        mock_semantic_chunker.return_value = mock_chunker_instance

        service = ChunkProcessingService(use_semantic=True)

        # Mock database
        mock_db = AsyncMock()
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.add = Mock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        # Process document
        document_id = str(uuid4())
        result = await service.process_document(
            db=mock_db,
            document_id=document_id,
            content="Test document content"
        )

        # Verify chunking was called
        mock_chunker_instance.split_text.assert_called_once_with("Test document content")

        # Verify vector service was called with document metadata
        call_args = mock_vector_service.add_batch_embeddings.call_args
        metadatas = call_args[1]["metadatas"]
        assert metadatas[0]["source_type"] == "document"
        assert metadatas[0]["source_id"] == document_id

    @pytest.mark.asyncio
    @patch('app.services.chunk_processing_service.get_vector_service')
    @patch('app.services.chunk_processing_service.get_embedding_service')
    @patch('app.services.chunk_processing_service.SemanticChunker')
    async def test_delete_existing_chunks_note(self, mock_semantic_chunker, mock_embedding, mock_vector):
        """Test deleting existing chunks for a note."""
        mock_embedding.return_value = Mock()

        mock_vector_service = AsyncMock()
        mock_vector_service.delete_chunks_by_source = AsyncMock()
        mock_vector.return_value = mock_vector_service

        mock_semantic_chunker.return_value = Mock()

        service = ChunkProcessingService(use_semantic=True)

        # Mock database with existing chunks
        mock_chunk1 = Mock(spec=Chunk)
        mock_chunk1.id = uuid4()
        mock_chunk2 = Mock(spec=Chunk)
        mock_chunk2.id = uuid4()

        mock_db = AsyncMock()
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [mock_chunk1, mock_chunk2]
        mock_db.execute.return_value = mock_result
        mock_db.delete = AsyncMock()
        mock_db.commit = AsyncMock()

        note_id = str(uuid4())
        await service._delete_existing_chunks(mock_db, note_id, "note")

        # Verify vector service delete was called
        mock_vector_service.delete_chunks_by_source.assert_called_once_with(note_id, "note")

        # Verify database deletes
        assert mock_db.delete.call_count == 2
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    @patch('app.services.chunk_processing_service.get_vector_service')
    @patch('app.services.chunk_processing_service.get_embedding_service')
    @patch('app.services.chunk_processing_service.SemanticChunker')
    async def test_delete_existing_chunks_document(self, mock_semantic_chunker, mock_embedding, mock_vector):
        """Test deleting existing chunks for a document."""
        mock_embedding.return_value = Mock()

        mock_vector_service = AsyncMock()
        mock_vector_service.delete_chunks_by_source = AsyncMock()
        mock_vector.return_value = mock_vector_service

        mock_semantic_chunker.return_value = Mock()

        service = ChunkProcessingService(use_semantic=True)

        # Mock database with existing chunk
        mock_chunk = Mock(spec=Chunk)
        mock_chunk.id = uuid4()

        mock_db = AsyncMock()
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [mock_chunk]
        mock_db.execute.return_value = mock_result
        mock_db.delete = AsyncMock()
        mock_db.commit = AsyncMock()

        document_id = str(uuid4())
        await service._delete_existing_chunks(mock_db, document_id, "document")

        # Verify vector service delete was called
        mock_vector_service.delete_chunks_by_source.assert_called_once_with(document_id, "document")

        # Verify database delete
        mock_db.delete.assert_called_once()

    @pytest.mark.asyncio
    @patch('app.services.chunk_processing_service.get_vector_service')
    @patch('app.services.chunk_processing_service.get_embedding_service')
    @patch('app.services.chunk_processing_service.SemanticChunker')
    async def test_delete_existing_chunks_no_chunks(self, mock_semantic_chunker, mock_embedding, mock_vector):
        """Test deleting when no existing chunks."""
        mock_embedding.return_value = Mock()
        mock_vector_service = AsyncMock()
        mock_vector.return_value = mock_vector_service
        mock_semantic_chunker.return_value = Mock()

        service = ChunkProcessingService(use_semantic=True)

        # Mock database with no chunks
        mock_db = AsyncMock()
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result
        mock_db.delete = AsyncMock()

        await service._delete_existing_chunks(mock_db, str(uuid4()), "note")

        # Verify nothing was deleted
        mock_db.delete.assert_not_called()
        mock_vector_service.delete_chunks_by_source.assert_not_called()

    @patch('app.services.chunk_processing_service.ChunkProcessingService')
    def test_get_chunk_processing_service(self, mock_service_class):
        """Test service factory function."""
        mock_instance = Mock()
        mock_service_class.return_value = mock_instance

        service = get_chunk_processing_service()

        assert service == mock_instance
        mock_service_class.assert_called_once()

    @pytest.mark.asyncio
    @patch('app.services.chunk_processing_service.get_vector_service')
    @patch('app.services.chunk_processing_service.get_embedding_service')
    @patch('app.services.chunk_processing_service.SemanticChunker')
    async def test_process_note_with_metadata(self, mock_semantic_chunker, mock_embedding, mock_vector):
        """Test that chunk metadata is properly stored."""
        # Mock services
        mock_embedding_service = Mock()
        mock_embedding_service.embed_batch.return_value = [[0.1, 0.2]]
        mock_embedding.return_value = mock_embedding_service

        mock_vector_service = AsyncMock()
        mock_vector_service.delete_chunks_by_source = AsyncMock()
        mock_vector_service.add_batch_embeddings = AsyncMock()
        mock_vector.return_value = mock_vector_service

        # Mock semantic chunk with all metadata
        mock_chunk = Mock()
        mock_chunk.content = "Test content"
        mock_chunk.metadata = Mock()
        mock_chunk.metadata.token_count = 50
        mock_chunk.metadata.content_type = "code"
        mock_chunk.metadata.heading_hierarchy = ["H1", "H2"]
        mock_chunk.metadata.section_title = "Code Section"
        mock_chunk.metadata.has_code = True
        mock_chunk.metadata.semantic_density = 0.9

        mock_chunker_instance = Mock()
        mock_chunker_instance.split_text.return_value = [mock_chunk]
        mock_semantic_chunker.return_value = mock_chunker_instance

        service = ChunkProcessingService(use_semantic=True)

        # Mock database
        mock_db = AsyncMock()
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.add = Mock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        # Process note
        await service.process_note(
            db=mock_db,
            note_id=str(uuid4()),
            content="Test content"
        )

        # Verify metadata was included in add_batch_embeddings call
        call_args = mock_vector_service.add_batch_embeddings.call_args
        metadatas = call_args[1]["metadatas"]

        assert metadatas[0]["content_type"] == "code"
        assert metadatas[0]["section_title"] == "Code Section"
        assert metadatas[0]["has_code"] is True
        assert metadatas[0]["semantic_density"] == 0.9

    @pytest.mark.asyncio
    @patch('app.services.chunk_processing_service.get_vector_service')
    @patch('app.services.chunk_processing_service.get_embedding_service')
    @patch('app.services.chunk_processing_service.SemanticChunker')
    async def test_process_note_metadata_none_values(self, mock_semantic_chunker, mock_embedding, mock_vector):
        """Test that None metadata values are excluded."""
        # Mock services
        mock_embedding_service = Mock()
        mock_embedding_service.embed_batch.return_value = [[0.1, 0.2]]
        mock_embedding.return_value = mock_embedding_service

        mock_vector_service = AsyncMock()
        mock_vector_service.delete_chunks_by_source = AsyncMock()
        mock_vector_service.add_batch_embeddings = AsyncMock()
        mock_vector.return_value = mock_vector_service

        # Mock semantic chunk with None metadata values
        mock_chunk = Mock()
        mock_chunk.content = "Test content"
        mock_chunk.metadata = Mock()
        mock_chunk.metadata.token_count = 50
        mock_chunk.metadata.content_type = None
        mock_chunk.metadata.heading_hierarchy = []
        mock_chunk.metadata.section_title = None
        mock_chunk.metadata.has_code = None
        mock_chunk.metadata.semantic_density = None

        mock_chunker_instance = Mock()
        mock_chunker_instance.split_text.return_value = [mock_chunk]
        mock_semantic_chunker.return_value = mock_chunker_instance

        service = ChunkProcessingService(use_semantic=True)

        # Mock database
        mock_db = AsyncMock()
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.add = Mock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        # Process note
        await service.process_note(
            db=mock_db,
            note_id=str(uuid4()),
            content="Test content"
        )

        # Verify None values are excluded from metadata
        call_args = mock_vector_service.add_batch_embeddings.call_args
        metadatas = call_args[1]["metadatas"]

        assert "content_type" not in metadatas[0]
        assert "section_title" not in metadatas[0]
        assert "has_code" not in metadatas[0]
        assert "semantic_density" not in metadatas[0]
        # Required fields should still be present
        assert "token_count" in metadatas[0]
        assert "chunk_index" in metadatas[0]

    @pytest.mark.asyncio
    @patch('app.services.chunk_processing_service.get_vector_service')
    @patch('app.services.chunk_processing_service.get_embedding_service')
    @patch('app.services.chunk_processing_service.SemanticChunker')
    async def test_process_document_empty_chunks(self, mock_semantic_chunker, mock_embedding, mock_vector):
        """Test document processing when semantic chunker returns no chunks."""
        # Mock services
        mock_embed_service = Mock()
        mock_embedding.return_value = mock_embed_service

        mock_vector_service = AsyncMock()
        mock_vector.return_value = mock_vector_service

        # Mock semantic chunker to return empty list
        mock_chunker_instance = Mock()
        mock_chunker_instance.split_text.return_value = []
        mock_semantic_chunker.return_value = mock_chunker_instance

        # Mock database properly
        mock_db = AsyncMock()
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        # Create service with semantic chunker
        service = ChunkProcessingService(use_semantic=True)

        document_id = uuid4()

        # Process document with empty content
        result = await service.process_document(
            db=mock_db,
            document_id=document_id,
            content=""
        )

        # Should return empty list
        assert result == []
        # Verify no embeddings were added
        mock_vector_service.add_batch_embeddings.assert_not_called()
