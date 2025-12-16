"""
Unit tests for the RerankingService.
"""
import pytest
from unittest.mock import Mock, patch
import numpy as np

from app.services.reranking_service import RerankingService, get_reranking_service


class TestRerankingService:
    """Test suite for RerankingService."""

    @patch('app.services.reranking_service.CrossEncoder')
    def test_initialization_default_model(self, mock_cross_encoder):
        """Test initialization with default model."""
        mock_model = Mock()
        mock_cross_encoder.return_value = mock_model

        service = RerankingService()

        assert service.model is not None
        mock_cross_encoder.assert_called_once_with("cross-encoder/ms-marco-MiniLM-L-6-v2")

    @patch('app.services.reranking_service.CrossEncoder')
    def test_initialization_custom_model(self, mock_cross_encoder):
        """Test initialization with custom model."""
        mock_model = Mock()
        mock_cross_encoder.return_value = mock_model

        service = RerankingService(model_name="custom-model")

        mock_cross_encoder.assert_called_once_with("custom-model")

    @patch('app.services.reranking_service.CrossEncoder')
    def test_rerank_basic(self, mock_cross_encoder):
        """Test basic re-ranking."""
        mock_model = Mock()
        # Scores in reverse order - third text is most relevant
        mock_model.predict.return_value = np.array([0.3, 0.5, 0.8])
        mock_cross_encoder.return_value = mock_model

        service = RerankingService()

        query = "What is machine learning?"
        texts = [
            "Machine learning is a subset of AI",
            "Neural networks are computational models",
            "ML algorithms learn from data"
        ]

        results = service.rerank(query, texts, top_k=3)

        # Should return (index, score) tuples sorted by score descending
        assert len(results) == 3
        assert results[0][0] == 2  # Third text (index 2) has highest score
        assert results[0][1] == 0.8
        assert results[1][0] == 1  # Second text
        assert results[1][1] == 0.5
        assert results[2][0] == 0  # First text
        assert results[2][1] == 0.3

    @patch('app.services.reranking_service.CrossEncoder')
    def test_rerank_with_top_k_limit(self, mock_cross_encoder):
        """Test re-ranking with top_k limit."""
        mock_model = Mock()
        mock_model.predict.return_value = np.array([0.1, 0.3, 0.5, 0.7, 0.9])
        mock_cross_encoder.return_value = mock_model

        service = RerankingService()

        texts = ["text1", "text2", "text3", "text4", "text5"]

        results = service.rerank("query", texts, top_k=2)

        # Should only return top 2 results
        assert len(results) == 2
        assert results[0][0] == 4  # Highest score (0.9)
        assert results[1][0] == 3  # Second highest (0.7)

    @patch('app.services.reranking_service.CrossEncoder')
    def test_rerank_empty_list(self, mock_cross_encoder):
        """Test re-ranking with empty text list."""
        mock_model = Mock()
        mock_cross_encoder.return_value = mock_model

        service = RerankingService()

        results = service.rerank("query", [], top_k=3)

        assert results == []
        # Model predict should not be called
        mock_model.predict.assert_not_called()

    @patch('app.services.reranking_service.CrossEncoder')
    def test_rerank_single_text(self, mock_cross_encoder):
        """Test re-ranking with single text."""
        mock_model = Mock()
        mock_model.predict.return_value = np.array([0.75])
        mock_cross_encoder.return_value = mock_model

        service = RerankingService()

        results = service.rerank("query", ["single text"], top_k=3)

        assert len(results) == 1
        assert results[0][0] == 0
        assert results[0][1] == 0.75

    @patch('app.services.reranking_service.CrossEncoder')
    def test_rerank_top_k_larger_than_texts(self, mock_cross_encoder):
        """Test when top_k is larger than number of texts."""
        mock_model = Mock()
        mock_model.predict.return_value = np.array([0.2, 0.4])
        mock_cross_encoder.return_value = mock_model

        service = RerankingService()

        results = service.rerank("query", ["text1", "text2"], top_k=10)

        # Should return all texts even though top_k=10
        assert len(results) == 2

    @patch('app.services.reranking_service.CrossEncoder')
    def test_rerank_creates_query_text_pairs(self, mock_cross_encoder):
        """Test that query-text pairs are created correctly."""
        mock_model = Mock()
        mock_model.predict.return_value = np.array([0.5, 0.6])
        mock_cross_encoder.return_value = mock_model

        service = RerankingService()

        query = "test query"
        texts = ["text1", "text2"]
        service.rerank(query, texts, top_k=2)

        # Verify predict was called with correct pairs
        call_args = mock_model.predict.call_args
        pairs = call_args[0][0]
        assert pairs == [[query, "text1"], [query, "text2"]]

    @patch('app.services.reranking_service.CrossEncoder')
    def test_rerank_returns_float_scores(self, mock_cross_encoder):
        """Test that scores are returned as floats."""
        mock_model = Mock()
        # Return numpy array
        mock_model.predict.return_value = np.array([0.5])
        mock_cross_encoder.return_value = mock_model

        service = RerankingService()

        results = service.rerank("query", ["text"], top_k=1)

        # Score should be float, not numpy type
        assert isinstance(results[0][1], float)

    @patch('app.services.reranking_service.CrossEncoder')
    def test_rerank_maintains_original_indices(self, mock_cross_encoder):
        """Test that original indices are preserved after sorting."""
        mock_model = Mock()
        # Scores that will result in reverse order
        mock_model.predict.return_value = np.array([0.1, 0.2, 0.3])
        mock_cross_encoder.return_value = mock_model

        service = RerankingService()

        texts = ["first", "second", "third"]
        results = service.rerank("query", texts, top_k=3)

        # Check that indices point to correct original positions
        assert results[0][0] == 2  # "third" was at index 2
        assert results[1][0] == 1  # "second" was at index 1
        assert results[2][0] == 0  # "first" was at index 0

    @patch('app.services.reranking_service.CrossEncoder')
    def test_rerank_with_identical_scores(self, mock_cross_encoder):
        """Test re-ranking when multiple texts have identical scores."""
        mock_model = Mock()
        mock_model.predict.return_value = np.array([0.5, 0.5, 0.5])
        mock_cross_encoder.return_value = mock_model

        service = RerankingService()

        results = service.rerank("query", ["text1", "text2", "text3"], top_k=2)

        # Should return top_k results (order may vary for identical scores)
        assert len(results) == 2
        # All scores should be 0.5
        assert all(score == 0.5 for _, score in results)

    @patch('app.services.reranking_service.CrossEncoder')
    def test_rerank_descending_order(self, mock_cross_encoder):
        """Test that results are sorted in descending order."""
        mock_model = Mock()
        mock_model.predict.return_value = np.array([0.2, 0.8, 0.5, 0.9, 0.1])
        mock_cross_encoder.return_value = mock_model

        service = RerankingService()

        results = service.rerank("query", ["t1", "t2", "t3", "t4", "t5"], top_k=5)

        # Verify descending order
        scores = [score for _, score in results]
        assert scores == sorted(scores, reverse=True)
        assert scores[0] == 0.9
        assert scores[1] == 0.8
        assert scores[4] == 0.1

    @patch('app.services.reranking_service.RerankingService')
    def test_get_reranking_service_singleton(self, mock_service_class):
        """Test that get_reranking_service returns singleton."""
        # Reset global instance
        import app.services.reranking_service
        app.services.reranking_service._reranking_service = None

        # Create mock instance
        mock_instance = Mock()
        mock_service_class.return_value = mock_instance

        service1 = get_reranking_service()
        service2 = get_reranking_service()

        # Should return same instance
        assert service1 is service2
        mock_service_class.assert_called_once()

    @patch('app.services.reranking_service.CrossEncoder')
    def test_rerank_zero_top_k(self, mock_cross_encoder):
        """Test re-ranking with top_k=0."""
        mock_model = Mock()
        mock_model.predict.return_value = np.array([0.5, 0.6])
        mock_cross_encoder.return_value = mock_model

        service = RerankingService()

        results = service.rerank("query", ["text1", "text2"], top_k=0)

        # Should return empty list when top_k=0
        assert results == []

    @patch('app.services.reranking_service.CrossEncoder')
    def test_rerank_with_very_long_texts(self, mock_cross_encoder):
        """Test re-ranking with very long texts."""
        mock_model = Mock()
        mock_model.predict.return_value = np.array([0.7])
        mock_cross_encoder.return_value = mock_model

        service = RerankingService()

        long_text = "word " * 1000  # Very long text
        results = service.rerank("query", [long_text], top_k=1)

        assert len(results) == 1
        # Verify the pair was created correctly
        call_args = mock_model.predict.call_args
        pairs = call_args[0][0]
        assert pairs[0][1] == long_text
