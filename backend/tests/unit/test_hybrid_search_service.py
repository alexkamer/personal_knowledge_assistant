"""
Unit tests for the HybridSearchService.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4

from app.services.hybrid_search_service import HybridSearchService, get_hybrid_search_service
from app.models.chunk import Chunk


class TestHybridSearchService:
    """Test suite for HybridSearchService."""

    def test_initialization(self):
        """Test service initialization."""
        service = HybridSearchService()

        assert service._bm25_index is None
        assert service._chunk_map == {}

    @pytest.mark.asyncio
    async def test_build_bm25_index_success(self):
        """Test building BM25 index from chunks."""
        service = HybridSearchService()

        # Mock database session
        mock_db = AsyncMock()
        mock_result = Mock()

        # Create mock chunks
        chunk1 = Mock(spec=Chunk)
        chunk1.id = uuid4()
        chunk1.content = "Python is a programming language"

        chunk2 = Mock(spec=Chunk)
        chunk2.id = uuid4()
        chunk2.content = "Machine learning uses algorithms"

        mock_result.scalars.return_value.all.return_value = [chunk1, chunk2]
        mock_db.execute.return_value = mock_result

        await service.build_bm25_index(mock_db)

        # Check index was built
        assert service._bm25_index is not None
        assert len(service._chunk_map) == 2
        assert str(chunk1.id) in service._chunk_map
        assert str(chunk2.id) in service._chunk_map

    @pytest.mark.asyncio
    async def test_build_bm25_index_with_source_type_note(self):
        """Test building BM25 index filtered by note source type."""
        service = HybridSearchService()

        mock_db = AsyncMock()
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        await service.build_bm25_index(mock_db, source_type="note")

        # Verify query was executed
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_build_bm25_index_with_source_type_document(self):
        """Test building BM25 index filtered by document source type."""
        service = HybridSearchService()

        mock_db = AsyncMock()
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        await service.build_bm25_index(mock_db, source_type="document")

        # Verify query was executed
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_build_bm25_index_empty_chunks(self):
        """Test building BM25 index with no chunks."""
        service = HybridSearchService()

        mock_db = AsyncMock()
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        await service.build_bm25_index(mock_db)

        # Index should remain None for empty corpus
        assert service._bm25_index is None
        assert service._chunk_map == {}

    @pytest.mark.asyncio
    async def test_build_bm25_index_tokenization(self):
        """Test that chunks are properly tokenized."""
        service = HybridSearchService()

        mock_db = AsyncMock()
        mock_result = Mock()

        chunk = Mock(spec=Chunk)
        chunk.id = uuid4()
        chunk.content = "Hello World Testing"

        mock_result.scalars.return_value.all.return_value = [chunk]
        mock_db.execute.return_value = mock_result

        await service.build_bm25_index(mock_db)

        # Verify chunk is in map
        assert str(chunk.id) in service._chunk_map

    def test_bm25_search_not_initialized(self):
        """Test BM25 search when index is not initialized."""
        service = HybridSearchService()

        results = service.bm25_search("test query")

        assert results == []

    def test_bm25_search_success(self):
        """Test successful BM25 search."""
        service = HybridSearchService()

        # Manually set up index
        chunk1_id = str(uuid4())
        chunk2_id = str(uuid4())

        service._chunk_map = {
            chunk1_id: Mock(content="Python programming language"),
            chunk2_id: Mock(content="Machine learning algorithms"),
        }

        # Mock BM25 index
        mock_bm25 = Mock()
        mock_bm25.get_scores.return_value = [0.8, 0.3]
        service._bm25_index = mock_bm25

        results = service.bm25_search("Python")

        assert len(results) == 2
        # First result should be chunk1 (higher score)
        assert results[0][0] == chunk1_id
        assert results[0][1] == 0.8

    def test_bm25_search_with_top_k(self):
        """Test BM25 search with top_k limit."""
        service = HybridSearchService()

        # Set up index with 3 chunks
        chunk1_id = str(uuid4())
        chunk2_id = str(uuid4())
        chunk3_id = str(uuid4())

        service._chunk_map = {
            chunk1_id: Mock(),
            chunk2_id: Mock(),
            chunk3_id: Mock(),
        }

        mock_bm25 = Mock()
        mock_bm25.get_scores.return_value = [0.9, 0.5, 0.3]
        service._bm25_index = mock_bm25

        results = service.bm25_search("test", top_k=2)

        # Should only return top 2
        assert len(results) == 2
        assert results[0][1] == 0.9
        assert results[1][1] == 0.5

    def test_bm25_search_query_tokenization(self):
        """Test that query is properly tokenized."""
        service = HybridSearchService()

        chunk_id = str(uuid4())
        service._chunk_map = {chunk_id: Mock()}

        mock_bm25 = Mock()
        mock_bm25.get_scores.return_value = [0.5]
        service._bm25_index = mock_bm25

        results = service.bm25_search("Hello World")

        # Verify get_scores was called with tokenized query
        mock_bm25.get_scores.assert_called_once()
        call_args = mock_bm25.get_scores.call_args[0][0]
        assert call_args == ["hello", "world"]

    def test_bm25_search_empty_query(self):
        """Test BM25 search with empty query."""
        service = HybridSearchService()

        chunk_id = str(uuid4())
        service._chunk_map = {chunk_id: Mock()}

        mock_bm25 = Mock()
        mock_bm25.get_scores.return_value = [0.0]
        service._bm25_index = mock_bm25

        results = service.bm25_search("")

        assert len(results) == 1

    def test_reciprocal_rank_fusion_basic(self):
        """Test basic reciprocal rank fusion."""
        semantic_results = [
            ("chunk1", 0.1),  # Lower distance = better
            ("chunk2", 0.3),
        ]

        bm25_results = [
            ("chunk2", 0.9),  # Higher score = better
            ("chunk3", 0.5),
        ]

        fused = HybridSearchService.reciprocal_rank_fusion(
            semantic_results, bm25_results
        )

        # Should return all unique chunks
        assert len(fused) == 3
        # Results sorted by fused score
        assert all(isinstance(item, tuple) for item in fused)
        assert all(len(item) == 2 for item in fused)

    def test_reciprocal_rank_fusion_weights(self):
        """Test that fusion respects weights."""
        semantic_results = [("chunk1", 0.1)]
        bm25_results = [("chunk2", 0.9)]

        # With default weights (0.7 semantic, 0.3 bm25)
        fused = HybridSearchService.reciprocal_rank_fusion(
            semantic_results,
            bm25_results,
            semantic_weight=0.7,
            bm25_weight=0.3,
        )

        # chunk1 should rank higher (semantic weight is higher)
        chunk_ids = [item[0] for item in fused]
        assert chunk_ids[0] == "chunk1"

    def test_reciprocal_rank_fusion_equal_weights(self):
        """Test fusion with equal weights."""
        semantic_results = [("chunk1", 0.1)]
        bm25_results = [("chunk2", 0.9)]

        fused = HybridSearchService.reciprocal_rank_fusion(
            semantic_results,
            bm25_results,
            semantic_weight=0.5,
            bm25_weight=0.5,
        )

        assert len(fused) == 2

    def test_reciprocal_rank_fusion_overlapping_chunks(self):
        """Test fusion with overlapping chunks."""
        semantic_results = [
            ("chunk1", 0.1),
            ("chunk2", 0.2),
        ]

        bm25_results = [
            ("chunk2", 0.9),
            ("chunk3", 0.5),
        ]

        fused = HybridSearchService.reciprocal_rank_fusion(
            semantic_results, bm25_results
        )

        # chunk2 appears in both, should have boosted score
        chunk_ids = [item[0] for item in fused]
        assert "chunk2" in chunk_ids
        # Should have 3 unique chunks
        assert len(fused) == 3

    def test_reciprocal_rank_fusion_empty_semantic(self):
        """Test fusion with empty semantic results."""
        semantic_results = []
        bm25_results = [("chunk1", 0.9)]

        fused = HybridSearchService.reciprocal_rank_fusion(
            semantic_results, bm25_results
        )

        assert len(fused) == 1
        assert fused[0][0] == "chunk1"

    def test_reciprocal_rank_fusion_empty_bm25(self):
        """Test fusion with empty BM25 results."""
        semantic_results = [("chunk1", 0.1)]
        bm25_results = []

        fused = HybridSearchService.reciprocal_rank_fusion(
            semantic_results, bm25_results
        )

        assert len(fused) == 1
        assert fused[0][0] == "chunk1"

    def test_reciprocal_rank_fusion_both_empty(self):
        """Test fusion with both empty result sets."""
        fused = HybridSearchService.reciprocal_rank_fusion([], [])

        assert fused == []

    def test_reciprocal_rank_fusion_custom_k(self):
        """Test fusion with custom k parameter."""
        semantic_results = [("chunk1", 0.1)]
        bm25_results = [("chunk2", 0.9)]

        # Different k values should affect scores
        fused1 = HybridSearchService.reciprocal_rank_fusion(
            semantic_results, bm25_results, k=60
        )
        fused2 = HybridSearchService.reciprocal_rank_fusion(
            semantic_results, bm25_results, k=30
        )

        # Scores should be different
        assert fused1[0][1] != fused2[0][1]

    def test_reciprocal_rank_fusion_rank_matters(self):
        """Test that rank position affects fusion score."""
        semantic_results = [
            ("chunk1", 0.1),  # Rank 1
            ("chunk2", 0.2),  # Rank 2
            ("chunk3", 0.3),  # Rank 3
        ]

        bm25_results = []

        fused = HybridSearchService.reciprocal_rank_fusion(
            semantic_results, bm25_results
        )

        # chunk1 should have highest score (rank 1)
        assert fused[0][0] == "chunk1"
        # Scores should decrease with rank
        assert fused[0][1] > fused[1][1] > fused[2][1]

    def test_reciprocal_rank_fusion_descending_order(self):
        """Test that results are sorted in descending order."""
        semantic_results = [("chunk1", 0.5), ("chunk2", 0.1)]
        bm25_results = [("chunk3", 0.3)]

        fused = HybridSearchService.reciprocal_rank_fusion(
            semantic_results, bm25_results
        )

        # Verify descending order
        scores = [score for _, score in fused]
        assert scores == sorted(scores, reverse=True)

    def test_reciprocal_rank_fusion_many_results(self):
        """Test fusion with many results."""
        semantic_results = [(f"chunk{i}", 0.1 * i) for i in range(10)]
        bm25_results = [(f"chunk{i+5}", 0.1 * i) for i in range(10)]

        fused = HybridSearchService.reciprocal_rank_fusion(
            semantic_results, bm25_results
        )

        # Should have all unique chunks
        assert len(fused) == 15  # 10 from semantic + 10 from bm25 - 5 overlap

    @patch('app.services.hybrid_search_service.HybridSearchService')
    def test_get_hybrid_search_service_singleton(self, mock_service_class):
        """Test that get_hybrid_search_service returns singleton."""
        # Reset global instance
        import app.services.hybrid_search_service
        app.services.hybrid_search_service._hybrid_search_service = None

        # Create mock instance
        mock_instance = Mock()
        mock_service_class.return_value = mock_instance

        service1 = get_hybrid_search_service()
        service2 = get_hybrid_search_service()

        # Should return same instance
        assert service1 is service2
        mock_service_class.assert_called_once()

    @pytest.mark.asyncio
    async def test_build_bm25_index_replaces_existing(self):
        """Test that building index replaces existing one."""
        service = HybridSearchService()

        # First build
        mock_db1 = AsyncMock()
        mock_result1 = Mock()
        chunk1 = Mock(spec=Chunk)
        chunk1.id = uuid4()
        chunk1.content = "First chunk"
        mock_result1.scalars.return_value.all.return_value = [chunk1]
        mock_db1.execute.return_value = mock_result1

        await service.build_bm25_index(mock_db1)
        first_index = service._bm25_index
        first_map_size = len(service._chunk_map)

        # Second build with different chunks
        mock_db2 = AsyncMock()
        mock_result2 = Mock()
        chunk2 = Mock(spec=Chunk)
        chunk2.id = uuid4()
        chunk2.content = "Second chunk"
        chunk3 = Mock(spec=Chunk)
        chunk3.id = uuid4()
        chunk3.content = "Third chunk"
        mock_result2.scalars.return_value.all.return_value = [chunk2, chunk3]
        mock_db2.execute.return_value = mock_result2

        await service.build_bm25_index(mock_db2)

        # Index should be replaced
        assert service._bm25_index is not first_index
        assert len(service._chunk_map) == 2
        assert len(service._chunk_map) != first_map_size

    def test_bm25_search_long_query_truncation(self):
        """Test BM25 search with very long query."""
        service = HybridSearchService()

        chunk_id = str(uuid4())
        service._chunk_map = {chunk_id: Mock()}

        mock_bm25 = Mock()
        mock_bm25.get_scores.return_value = [0.5]
        service._bm25_index = mock_bm25

        long_query = "word " * 100  # Very long query
        results = service.bm25_search(long_query)

        # Should still work
        assert len(results) == 1

    def test_reciprocal_rank_fusion_zero_weights(self):
        """Test fusion with zero weights."""
        semantic_results = [("chunk1", 0.1)]
        bm25_results = [("chunk2", 0.9)]

        # Zero semantic weight
        fused = HybridSearchService.reciprocal_rank_fusion(
            semantic_results,
            bm25_results,
            semantic_weight=0.0,
            bm25_weight=1.0,
        )

        # chunk2 (from BM25) should rank first
        assert fused[0][0] == "chunk2"
