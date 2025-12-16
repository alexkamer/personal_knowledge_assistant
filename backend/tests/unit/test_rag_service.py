"""
Unit tests for the RAG service.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4

from app.services.rag_service import RAGService, RetrievedChunk


class TestRetrievedChunk:
    """Test suite for RetrievedChunk."""

    def test_initialization(self):
        """Test RetrievedChunk initialization."""
        chunk = RetrievedChunk(
            chunk_id="chunk1",
            content="Test content",
            distance=0.5,
            source_type="note",
            source_id="note1",
            source_title="Test Note",
            chunk_index=0,
        )

        assert chunk.chunk_id == "chunk1"
        assert chunk.content == "Test content"
        assert chunk.distance == 0.5
        assert chunk.source_type == "note"

    def test_to_dict(self):
        """Test converting chunk to dictionary."""
        chunk = RetrievedChunk(
            chunk_id="chunk1",
            content="Test content",
            distance=0.5,
            source_type="note",
            source_id="note1",
            source_title="Test Note",
            chunk_index=0,
            content_type="narrative",
            has_code=False,
            semantic_density=0.7,
        )

        chunk_dict = chunk.to_dict()

        assert chunk_dict["chunk_id"] == "chunk1"
        assert chunk_dict["content"] == "Test content"
        assert chunk_dict["distance"] == 0.5
        assert chunk_dict["content_type"] == "narrative"
        assert chunk_dict["has_code"] is False
        assert chunk_dict["semantic_density"] == 0.7


class TestRAGService:
    """Test suite for RAGService."""

    @patch('app.services.rag_service.get_embedding_service')
    @patch('app.services.rag_service.get_vector_service')
    @patch('app.services.rag_service.get_reranking_service')
    @patch('app.services.rag_service.get_hybrid_search_service')
    def test_initialization(self, mock_hybrid, mock_rerank, mock_vector, mock_embedding):
        """Test RAG service initialization."""
        service = RAGService(use_hybrid_search=True)

        assert service.embedding_service is not None
        assert service.vector_service is not None
        mock_embedding.assert_called_once()
        mock_vector.assert_called_once()

    @patch('app.services.rag_service.get_embedding_service')
    @patch('app.services.rag_service.get_vector_service')
    @patch('app.services.rag_service.get_reranking_service')
    @patch('app.services.rag_service.get_hybrid_search_service')
    def test_assemble_context_basic(self, mock_hybrid, mock_rerank, mock_vector, mock_embedding):
        """Test assembling context from chunks."""
        service = RAGService(use_hybrid_search=False)

        chunks = [
            RetrievedChunk(
                chunk_id="chunk1",
                content="First chunk content",
                distance=0.1,
                source_type="note",
                source_id="note1",
                source_title="Note 1",
                chunk_index=0,
            ),
            RetrievedChunk(
                chunk_id="chunk2",
                content="Second chunk content",
                distance=0.2,
                source_type="document",
                source_id="doc1",
                source_title="Document 1",
                chunk_index=0,
            ),
        ]

        context, citations = service.assemble_context(chunks, max_tokens=10000)

        assert "First chunk content" in context
        assert "Second chunk content" in context
        assert "[Source 1: Note 1]" in context
        assert "[Source 2: Document 1]" in context
        assert len(citations) == 2
        assert citations[0]["source_title"] == "Note 1"
        assert citations[1]["source_title"] == "Document 1"

    @patch('app.services.rag_service.get_embedding_service')
    @patch('app.services.rag_service.get_vector_service')
    @patch('app.services.rag_service.get_reranking_service')
    @patch('app.services.rag_service.get_hybrid_search_service')
    def test_assemble_context_empty_chunks(self, mock_hybrid, mock_rerank, mock_vector, mock_embedding):
        """Test assembling context with no chunks."""
        service = RAGService(use_hybrid_search=False)

        context, citations = service.assemble_context([], max_tokens=10000)

        assert context == ""
        assert citations == []

    @patch('app.services.rag_service.get_embedding_service')
    @patch('app.services.rag_service.get_vector_service')
    @patch('app.services.rag_service.get_reranking_service')
    @patch('app.services.rag_service.get_hybrid_search_service')
    def test_assemble_context_max_tokens_limit(self, mock_hybrid, mock_rerank, mock_vector, mock_embedding):
        """Test that context respects max token limit."""
        service = RAGService(use_hybrid_search=False)

        # Create chunks with large content
        chunks = [
            RetrievedChunk(
                chunk_id=f"chunk{i}",
                content="A" * 1000,  # ~250 tokens
                distance=0.1 * i,
                source_type="note",
                source_id=f"note{i}",
                source_title=f"Note {i}",
                chunk_index=0,
            )
            for i in range(10)
        ]

        # Set max_tokens to only fit ~2 chunks
        context, citations = service.assemble_context(chunks, max_tokens=600)

        # Should only include first 2-3 chunks before hitting limit
        assert len(citations) < len(chunks)
        assert len(citations) <= 3

    @patch('app.services.rag_service.get_embedding_service')
    @patch('app.services.rag_service.get_vector_service')
    @patch('app.services.rag_service.get_reranking_service')
    @patch('app.services.rag_service.get_hybrid_search_service')
    def test_rerank_chunks(self, mock_hybrid, mock_rerank, mock_vector, mock_embedding):
        """Test re-ranking chunks."""
        # Create mock reranking service
        mock_reranker = Mock()
        mock_reranker.rerank.return_value = [(1, 0.9), (0, 0.5), (2, 0.3)]
        mock_rerank.return_value = mock_reranker

        service = RAGService(use_hybrid_search=False)
        service.reranking_service = mock_reranker

        chunks = [
            RetrievedChunk(
                chunk_id=f"chunk{i}",
                content=f"Content {i}",
                distance=0.1 * i,
                source_type="note",
                source_id=f"note{i}",
                source_title=f"Note {i}",
                chunk_index=0,
            )
            for i in range(3)
        ]

        reranked = service.rerank_chunks("test query", chunks, top_k=3)

        # Should return all 3 chunks in new order based on scores
        assert len(reranked) == 3
        assert reranked[0].chunk_id == "chunk1"  # Index 1 had highest score (0.9)
        assert reranked[1].chunk_id == "chunk0"  # Index 0 had second highest (0.5)
        assert reranked[2].chunk_id == "chunk2"  # Index 2 had lowest (0.3)

    @patch('app.services.rag_service.get_embedding_service')
    @patch('app.services.rag_service.get_vector_service')
    @patch('app.services.rag_service.get_reranking_service')
    @patch('app.services.rag_service.get_hybrid_search_service')
    def test_rerank_chunks_no_reranker(self, mock_hybrid, mock_rerank, mock_vector, mock_embedding):
        """Test that reranking returns original chunks if no reranker."""
        mock_rerank.return_value = None
        service = RAGService(use_hybrid_search=False)
        service.reranking_service = None

        chunks = [
            RetrievedChunk(
                chunk_id=f"chunk{i}",
                content=f"Content {i}",
                distance=0.1 * i,
                source_type="note",
                source_id=f"note{i}",
                source_title=f"Note {i}",
                chunk_index=0,
            )
            for i in range(3)
        ]

        reranked = service.rerank_chunks("test query", chunks, top_k=3)

        # Should return all 3 chunks without reranking (in original order)
        assert len(reranked) == 3
        assert reranked[0].chunk_id == "chunk0"
        assert reranked[1].chunk_id == "chunk1"
        assert reranked[2].chunk_id == "chunk2"
