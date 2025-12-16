"""
Unit tests for the RAGService.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4

from app.services.rag_service import RAGService, RetrievedChunk, get_rag_service


class TestRetrievedChunk:
    """Test suite for RetrievedChunk class."""

    def test_initialization_minimal(self):
        """Test RetrievedChunk with minimal required fields."""
        chunk = RetrievedChunk(
            chunk_id="chunk-123",
            content="Test content",
            distance=0.5,
            source_type="note",
            source_id="note-456",
            source_title="Test Note",
            chunk_index=0
        )

        assert chunk.chunk_id == "chunk-123"
        assert chunk.content == "Test content"
        assert chunk.distance == 0.5
        assert chunk.source_type == "note"
        assert chunk.source_id == "note-456"
        assert chunk.source_title == "Test Note"
        assert chunk.chunk_index == 0
        assert chunk.content_type is None
        assert chunk.section_title is None
        assert chunk.has_code is None
        assert chunk.semantic_density is None

    def test_initialization_with_metadata(self):
        """Test RetrievedChunk with all metadata fields."""
        chunk = RetrievedChunk(
            chunk_id="chunk-123",
            content="Test content",
            distance=0.5,
            source_type="document",
            source_id="doc-789",
            source_title="Test Doc",
            chunk_index=2,
            content_type="code",
            section_title="Implementation",
            has_code=True,
            semantic_density=0.8
        )

        assert chunk.content_type == "code"
        assert chunk.section_title == "Implementation"
        assert chunk.has_code is True
        assert chunk.semantic_density == 0.8

    def test_to_dict_minimal(self):
        """Test to_dict with minimal fields."""
        chunk = RetrievedChunk(
            chunk_id="chunk-123",
            content="Test content",
            distance=0.5,
            source_type="note",
            source_id="note-456",
            source_title="Test Note",
            chunk_index=0
        )

        result = chunk.to_dict()

        assert result["chunk_id"] == "chunk-123"
        assert result["content"] == "Test content"
        assert result["distance"] == 0.5
        assert result["source_type"] == "note"
        assert result["source_id"] == "note-456"
        assert result["source_title"] == "Test Note"
        assert result["chunk_index"] == 0
        # Optional fields should not be present
        assert "content_type" not in result
        assert "section_title" not in result
        assert "has_code" not in result
        assert "semantic_density" not in result

    def test_to_dict_with_metadata(self):
        """Test to_dict includes metadata fields when present."""
        chunk = RetrievedChunk(
            chunk_id="chunk-123",
            content="Test",
            distance=0.5,
            source_type="document",
            source_id="doc-789",
            source_title="Test Doc",
            chunk_index=0,
            content_type="list",
            section_title="Steps",
            has_code=False,
            semantic_density=0.6
        )

        result = chunk.to_dict()

        assert result["content_type"] == "list"
        assert result["section_title"] == "Steps"
        assert result["has_code"] is False
        assert result["semantic_density"] == 0.6

    def test_to_dict_has_code_none(self):
        """Test that has_code=None is not included in dict."""
        chunk = RetrievedChunk(
            chunk_id="chunk-123",
            content="Test",
            distance=0.5,
            source_type="note",
            source_id="note-456",
            source_title="Test",
            chunk_index=0,
            has_code=None
        )

        result = chunk.to_dict()

        assert "has_code" not in result


class TestRAGService:
    """Test suite for RAGService."""

    @patch('app.services.rag_service.settings')
    @patch('app.services.rag_service.get_hybrid_search_service')
    @patch('app.services.rag_service.get_reranking_service')
    @patch('app.services.rag_service.get_vector_service')
    @patch('app.services.rag_service.get_embedding_service')
    def test_initialization_default(
        self, mock_get_embedding, mock_get_vector, mock_get_reranking,
        mock_get_hybrid, mock_settings
    ):
        """Test RAG service initialization with defaults."""
        mock_settings.rerank_enabled = True

        service = RAGService()

        assert service.embedding_service is not None
        assert service.vector_service is not None
        assert service.reranking_service is not None
        assert service.hybrid_search_service is not None
        assert service.use_hybrid_search is True

    @patch('app.services.rag_service.settings')
    @patch('app.services.rag_service.get_hybrid_search_service')
    @patch('app.services.rag_service.get_reranking_service')
    @patch('app.services.rag_service.get_vector_service')
    @patch('app.services.rag_service.get_embedding_service')
    def test_initialization_no_hybrid(
        self, mock_get_embedding, mock_get_vector, mock_get_reranking,
        mock_get_hybrid, mock_settings
    ):
        """Test initialization without hybrid search."""
        mock_settings.rerank_enabled = True

        service = RAGService(use_hybrid_search=False)

        assert service.hybrid_search_service is None
        assert service.use_hybrid_search is False

    @patch('app.services.rag_service.settings')
    @patch('app.services.rag_service.get_hybrid_search_service')
    @patch('app.services.rag_service.get_reranking_service')
    @patch('app.services.rag_service.get_vector_service')
    @patch('app.services.rag_service.get_embedding_service')
    def test_initialization_no_reranking(
        self, mock_get_embedding, mock_get_vector, mock_get_reranking,
        mock_get_hybrid, mock_settings
    ):
        """Test initialization with reranking disabled."""
        mock_settings.rerank_enabled = False

        service = RAGService()

        assert service.reranking_service is None

    @patch('app.services.rag_service.get_hybrid_search_service')
    @patch('app.services.rag_service.get_reranking_service')
    @patch('app.services.rag_service.get_vector_service')
    @patch('app.services.rag_service.get_embedding_service')
    def test_infer_filters_from_query_code_keywords(
        self, mock_get_embedding, mock_get_vector, mock_get_reranking, mock_get_hybrid
    ):
        """Test filter inference for code-related queries."""
        service = RAGService()

        # Test various code keywords
        for keyword in ["code", "function", "class", "implementation"]:
            query = f"Show me {keyword} examples"
            filters = service._infer_filters_from_query(query)
            assert filters.get("has_code") is True

    @patch('app.services.rag_service.get_hybrid_search_service')
    @patch('app.services.rag_service.get_reranking_service')
    @patch('app.services.rag_service.get_vector_service')
    @patch('app.services.rag_service.get_embedding_service')
    def test_infer_filters_from_query_list_keywords(
        self, mock_get_embedding, mock_get_vector, mock_get_reranking, mock_get_hybrid
    ):
        """Test filter inference for list-related queries."""
        service = RAGService()

        query = "Show me a list of steps"
        filters = service._infer_filters_from_query(query)

        assert filters.get("content_type") == "list"

    @patch('app.services.rag_service.get_hybrid_search_service')
    @patch('app.services.rag_service.get_reranking_service')
    @patch('app.services.rag_service.get_vector_service')
    @patch('app.services.rag_service.get_embedding_service')
    def test_infer_filters_from_query_table_keywords(
        self, mock_get_embedding, mock_get_vector, mock_get_reranking, mock_get_hybrid
    ):
        """Test filter inference for table-related queries."""
        service = RAGService()

        query = "Show me data in a table"
        filters = service._infer_filters_from_query(query)

        assert filters.get("content_type") == "table"

    @patch('app.services.rag_service.get_hybrid_search_service')
    @patch('app.services.rag_service.get_reranking_service')
    @patch('app.services.rag_service.get_vector_service')
    @patch('app.services.rag_service.get_embedding_service')
    def test_infer_filters_from_query_no_matches(
        self, mock_get_embedding, mock_get_vector, mock_get_reranking, mock_get_hybrid
    ):
        """Test that queries without keywords return empty filters."""
        service = RAGService()

        query = "What is machine learning?"
        filters = service._infer_filters_from_query(query)

        assert filters == {}

    @patch('app.services.rag_service.settings')
    @patch('app.services.rag_service.get_hybrid_search_service')
    @patch('app.services.rag_service.get_reranking_service')
    @patch('app.services.rag_service.get_vector_service')
    @patch('app.services.rag_service.get_embedding_service')
    def test_rerank_chunks_no_reranking_service(
        self, mock_get_embedding, mock_get_vector, mock_get_reranking,
        mock_get_hybrid, mock_settings
    ):
        """Test that re-ranking returns original chunks when service is None."""
        mock_settings.rerank_enabled = False
        mock_get_reranking.return_value = None

        service = RAGService()

        chunks = [Mock(spec=RetrievedChunk)]
        result = service.rerank_chunks("query", chunks)

        assert result == chunks

    @patch('app.services.rag_service.settings')
    @patch('app.services.rag_service.get_hybrid_search_service')
    @patch('app.services.rag_service.get_reranking_service')
    @patch('app.services.rag_service.get_vector_service')
    @patch('app.services.rag_service.get_embedding_service')
    def test_rerank_chunks_empty_list(
        self, mock_get_embedding, mock_get_vector, mock_get_reranking,
        mock_get_hybrid, mock_settings
    ):
        """Test re-ranking with empty chunk list."""
        mock_settings.rerank_enabled = True
        mock_settings.max_final_chunks = 5

        service = RAGService()

        result = service.rerank_chunks("query", [])

        assert result == []

    @patch('app.services.rag_service.settings')
    @patch('app.services.rag_service.get_hybrid_search_service')
    @patch('app.services.rag_service.get_reranking_service')
    @patch('app.services.rag_service.get_vector_service')
    @patch('app.services.rag_service.get_embedding_service')
    def test_rerank_chunks_success(
        self, mock_get_embedding, mock_get_vector, mock_get_reranking,
        mock_get_hybrid, mock_settings
    ):
        """Test successful chunk re-ranking."""
        mock_settings.rerank_enabled = True
        mock_settings.max_final_chunks = 2

        # Mock reranking service
        mock_reranker = Mock()
        mock_reranker.rerank.return_value = [
            (1, 0.9),  # Second chunk has highest score
            (0, 0.7),  # First chunk has lower score
        ]
        mock_get_reranking.return_value = mock_reranker

        service = RAGService()

        chunk1 = RetrievedChunk(
            chunk_id="1", content="Content 1", distance=0.5,
            source_type="note", source_id="n1", source_title="Note 1",
            chunk_index=0
        )
        chunk2 = RetrievedChunk(
            chunk_id="2", content="Content 2", distance=0.3,
            source_type="note", source_id="n2", source_title="Note 2",
            chunk_index=0
        )

        chunks = [chunk1, chunk2]
        result = service.rerank_chunks("test query", chunks, top_k=2)

        assert len(result) == 2
        assert result[0].chunk_id == "2"  # Second chunk ranked first
        assert abs(result[0].distance - 0.1) < 0.01  # 1.0 - 0.9 (allow floating point imprecision)
        assert result[1].chunk_id == "1"
        assert abs(result[1].distance - 0.3) < 0.01  # 1.0 - 0.7

    @patch('app.services.rag_service.settings')
    @patch('app.services.rag_service.get_hybrid_search_service')
    @patch('app.services.rag_service.get_reranking_service')
    @patch('app.services.rag_service.get_vector_service')
    @patch('app.services.rag_service.get_embedding_service')
    def test_assemble_context_empty_chunks(
        self, mock_get_embedding, mock_get_vector, mock_get_reranking,
        mock_get_hybrid, mock_settings
    ):
        """Test context assembly with no chunks."""
        mock_settings.rerank_enabled = False
        mock_settings.max_context_tokens = 1000

        service = RAGService()

        context, citations = service.assemble_context([])

        assert context == ""
        assert citations == []

    @patch('app.services.rag_service.settings')
    @patch('app.services.rag_service.get_hybrid_search_service')
    @patch('app.services.rag_service.get_reranking_service')
    @patch('app.services.rag_service.get_vector_service')
    @patch('app.services.rag_service.get_embedding_service')
    def test_assemble_context_single_chunk(
        self, mock_get_embedding, mock_get_vector, mock_get_reranking,
        mock_get_hybrid, mock_settings
    ):
        """Test context assembly with single chunk."""
        mock_settings.rerank_enabled = False
        mock_settings.max_context_tokens = 1000

        service = RAGService()

        chunk = RetrievedChunk(
            chunk_id="chunk-1",
            content="Test content",
            distance=0.2,
            source_type="note",
            source_id="note-1",
            source_title="Test Note",
            chunk_index=0
        )

        context, citations = service.assemble_context([chunk])

        assert "[Source 1: Test Note]" in context
        assert "Test content" in context
        assert len(citations) == 1
        assert citations[0]["index"] == 1
        assert citations[0]["source_title"] == "Test Note"

    @patch('app.services.rag_service.settings')
    @patch('app.services.rag_service.get_hybrid_search_service')
    @patch('app.services.rag_service.get_reranking_service')
    @patch('app.services.rag_service.get_vector_service')
    @patch('app.services.rag_service.get_embedding_service')
    def test_assemble_context_deduplication(
        self, mock_get_embedding, mock_get_vector, mock_get_reranking,
        mock_get_hybrid, mock_settings
    ):
        """Test that context assembly deduplicates sources."""
        mock_settings.rerank_enabled = False
        mock_settings.max_context_tokens = 10000

        service = RAGService()

        # Two chunks from same source
        chunk1 = RetrievedChunk(
            chunk_id="chunk-1",
            content="First chunk from note",
            distance=0.2,
            source_type="note",
            source_id="note-1",
            source_title="Test Note",
            chunk_index=0
        )
        chunk2 = RetrievedChunk(
            chunk_id="chunk-2",
            content="Second chunk from note",
            distance=0.3,
            source_type="note",
            source_id="note-1",
            source_title="Test Note",
            chunk_index=1
        )

        context, citations = service.assemble_context([chunk1, chunk2])

        # Should only have 1 citation (deduplicated)
        assert len(citations) == 1
        assert citations[0]["source_id"] == "note-1"
        # Should keep better distance (0.2)
        assert citations[0]["distance"] == 0.2

    @patch('app.services.rag_service.settings')
    @patch('app.services.rag_service.get_hybrid_search_service')
    @patch('app.services.rag_service.get_reranking_service')
    @patch('app.services.rag_service.get_vector_service')
    @patch('app.services.rag_service.get_embedding_service')
    def test_assemble_context_token_limit(
        self, mock_get_embedding, mock_get_vector, mock_get_reranking,
        mock_get_hybrid, mock_settings
    ):
        """Test that context assembly respects token limits."""
        mock_settings.rerank_enabled = False
        mock_settings.max_context_tokens = 10  # Very small limit

        service = RAGService()

        # Create chunks that would exceed token limit
        chunks = [
            RetrievedChunk(
                chunk_id=f"chunk-{i}",
                content="x" * 100,  # 100 chars = ~25 tokens
                distance=0.1 * i,
                source_type="note",
                source_id=f"note-{i}",
                source_title=f"Note {i}",
                chunk_index=0
            )
            for i in range(5)
        ]

        context, citations = service.assemble_context(chunks, max_tokens=10)

        # Should stop early due to token limit
        assert len(citations) == 0  # First chunk already exceeds limit

    @patch('app.services.rag_service.settings')
    @patch('app.services.rag_service.get_hybrid_search_service')
    @patch('app.services.rag_service.get_reranking_service')
    @patch('app.services.rag_service.get_vector_service')
    @patch('app.services.rag_service.get_embedding_service')
    def test_assemble_context_includes_metadata(
        self, mock_get_embedding, mock_get_vector, mock_get_reranking,
        mock_get_hybrid, mock_settings
    ):
        """Test that metadata fields are included in citations."""
        mock_settings.rerank_enabled = False
        mock_settings.max_context_tokens = 1000

        service = RAGService()

        chunk = RetrievedChunk(
            chunk_id="chunk-1",
            content="Test",
            distance=0.2,
            source_type="document",
            source_id="doc-1",
            source_title="Doc",
            chunk_index=0,
            content_type="code",
            section_title="Implementation",
            has_code=True,
            semantic_density=0.8
        )

        context, citations = service.assemble_context([chunk])

        citation = citations[0]
        assert citation["content_type"] == "code"
        assert citation["section_title"] == "Implementation"
        assert citation["has_code"] is True
        assert citation["semantic_density"] == 0.8

    def test_get_rag_service(self):
        """Test that get_rag_service returns an instance."""
        service = get_rag_service()

        assert isinstance(service, RAGService)
