"""
Tests for BM25 index invalidation.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.hybrid_search_service import HybridSearchService
from app.services.vector_service import VectorService


def test_bm25_index_invalidation_on_add():
    """Test that adding a chunk invalidates the BM25 index."""
    # Create hybrid search service with a valid index
    hybrid_service = HybridSearchService()
    hybrid_service._index_valid = True

    # Mock the get_hybrid_search_service to return our instance
    with patch(
        "app.services.hybrid_search_service.get_hybrid_search_service",
        return_value=hybrid_service,
    ):
        # Create vector service
        vector_service = VectorService()

        # Mock ChromaDB collection
        mock_collection = MagicMock()
        vector_service.collection = mock_collection

        # Add a chunk (this should invalidate the BM25 index)
        import asyncio

        asyncio.run(
            vector_service.add_chunk_embedding(
                chunk_id="test-chunk-1",
                embedding=[0.1, 0.2, 0.3],
                chunk_text="Test content",
                metadata={"source_type": "note"},
            )
        )

        # Verify BM25 index was invalidated
        assert hybrid_service._index_valid is False


def test_bm25_index_invalidation_on_batch_add():
    """Test that batch adding chunks invalidates the BM25 index."""
    # Create hybrid search service with a valid index
    hybrid_service = HybridSearchService()
    hybrid_service._index_valid = True

    # Mock the get_hybrid_search_service to return our instance
    with patch(
        "app.services.hybrid_search_service.get_hybrid_search_service",
        return_value=hybrid_service,
    ):
        # Create vector service
        vector_service = VectorService()

        # Mock ChromaDB collection
        mock_collection = MagicMock()
        vector_service.collection = mock_collection

        # Add chunks in batch (this should invalidate the BM25 index)
        import asyncio

        asyncio.run(
            vector_service.add_batch_embeddings(
                chunk_ids=["chunk-1", "chunk-2"],
                embeddings=[[0.1, 0.2], [0.3, 0.4]],
                chunk_texts=["Content 1", "Content 2"],
                metadatas=[{"source_type": "note"}, {"source_type": "document"}],
            )
        )

        # Verify BM25 index was invalidated
        assert hybrid_service._index_valid is False


def test_bm25_index_invalidation_on_delete():
    """Test that deleting a chunk invalidates the BM25 index."""
    # Create hybrid search service with a valid index
    hybrid_service = HybridSearchService()
    hybrid_service._index_valid = True

    # Mock the get_hybrid_search_service to return our instance
    with patch(
        "app.services.hybrid_search_service.get_hybrid_search_service",
        return_value=hybrid_service,
    ):
        # Create vector service
        vector_service = VectorService()

        # Mock ChromaDB collection
        mock_collection = MagicMock()
        vector_service.collection = mock_collection

        # Delete a chunk (this should invalidate the BM25 index)
        import asyncio

        asyncio.run(vector_service.delete_chunk(chunk_id="test-chunk-1"))

        # Verify BM25 index was invalidated
        assert hybrid_service._index_valid is False


def test_bm25_index_invalidation_on_delete_by_source():
    """Test that deleting chunks by source invalidates the BM25 index."""
    # Create hybrid search service with a valid index
    hybrid_service = HybridSearchService()
    hybrid_service._index_valid = True

    # Mock the get_hybrid_search_service to return our instance
    with patch(
        "app.services.hybrid_search_service.get_hybrid_search_service",
        return_value=hybrid_service,
    ):
        # Create vector service
        vector_service = VectorService()

        # Mock ChromaDB collection
        mock_collection = MagicMock()
        vector_service.collection = mock_collection

        # Delete chunks by source (this should invalidate the BM25 index)
        import asyncio

        asyncio.run(
            vector_service.delete_chunks_by_source(source_id="note-123", source_type="note")
        )

        # Verify BM25 index was invalidated
        assert hybrid_service._index_valid is False


def test_bm25_search_returns_empty_when_invalid():
    """Test that BM25 search returns empty results when index is invalid."""
    hybrid_service = HybridSearchService()

    # Build a mock index
    from rank_bm25 import BM25Okapi

    hybrid_service._bm25_index = BM25Okapi([["test", "content"]])
    hybrid_service._chunk_map = {"chunk-1": MagicMock()}
    hybrid_service._index_valid = True

    # Search should work when index is valid
    results = hybrid_service.bm25_search("test query", top_k=5)
    assert len(results) > 0

    # Invalidate the index
    hybrid_service.invalidate_index()
    assert hybrid_service._index_valid is False

    # Search should return empty when index is invalid
    results = hybrid_service.bm25_search("test query", top_k=5)
    assert len(results) == 0


def test_invalidate_index_method():
    """Test that invalidate_index() correctly sets the flag."""
    hybrid_service = HybridSearchService()

    # Initially invalid
    assert hybrid_service._index_valid is False

    # Set to valid
    hybrid_service._index_valid = True
    assert hybrid_service._index_valid is True

    # Invalidate
    hybrid_service.invalidate_index()
    assert hybrid_service._index_valid is False


@pytest.mark.asyncio
async def test_build_index_sets_valid_flag(test_db):
    """Test that building the index sets the valid flag."""
    from app.models.note import Note
    from app.models.chunk import Chunk

    # Create a note and chunk
    note = Note(title="Test Note", content="Test content")
    test_db.add(note)
    await test_db.commit()
    await test_db.refresh(note)

    chunk = Chunk(
        content="Test chunk content",
        chunk_index=0,
        token_count=10,
        note_id=str(note.id),
    )
    test_db.add(chunk)
    await test_db.commit()

    # Create hybrid search service
    hybrid_service = HybridSearchService()
    assert hybrid_service._index_valid is False

    # Build index
    await hybrid_service.build_bm25_index(test_db)

    # Verify index is now valid
    assert hybrid_service._index_valid is True
    assert hybrid_service._bm25_index is not None
    assert len(hybrid_service._chunk_map) > 0
