"""
Tests for embedding dimension validation.
"""

import pytest
from unittest.mock import MagicMock, patch

from app.services.embedding_service import EmbeddingService


def test_embedding_dimension_validation_success():
    """Test that embedding service initializes successfully when dimensions match."""
    # Mock SentenceTransformer to return correct dimension
    mock_model = MagicMock()
    mock_model.get_sentence_embedding_dimension.return_value = 384

    with patch("app.services.embedding_service.SentenceTransformer", return_value=mock_model):
        with patch("app.services.embedding_service.settings") as mock_settings:
            mock_settings.embedding_model = "sentence-transformers/all-MiniLM-L6-v2"
            mock_settings.embedding_dimension = 384

            # Should initialize without error
            service = EmbeddingService()
            assert service.model is not None
            assert service.get_embedding_dimension() == 384


def test_embedding_dimension_validation_mismatch():
    """Test that embedding service fails when dimensions don't match."""
    # Mock SentenceTransformer to return wrong dimension
    mock_model = MagicMock()
    mock_model.get_sentence_embedding_dimension.return_value = 768  # Wrong dimension

    with patch("app.services.embedding_service.SentenceTransformer", return_value=mock_model):
        with patch("app.services.embedding_service.settings") as mock_settings:
            mock_settings.embedding_model = "sentence-transformers/all-MiniLM-L6-v2"
            mock_settings.embedding_dimension = 384  # Expecting 384 but model returns 768

            # Should raise ValueError with helpful message
            with pytest.raises(ValueError) as exc_info:
                EmbeddingService()

            error_message = str(exc_info.value)
            assert "Embedding dimension mismatch" in error_message
            assert "768" in error_message  # Actual dimension
            assert "384" in error_message  # Expected dimension
            assert "EMBEDDING_DIMENSION" in error_message


def test_embedding_dimension_validation_different_model():
    """Test dimension validation with a different model."""
    # Mock a larger model (e.g., all-mpnet-base-v2 which has 768 dimensions)
    mock_model = MagicMock()
    mock_model.get_sentence_embedding_dimension.return_value = 768

    with patch("app.services.embedding_service.SentenceTransformer", return_value=mock_model):
        with patch("app.services.embedding_service.settings") as mock_settings:
            mock_settings.embedding_model = "sentence-transformers/all-mpnet-base-v2"
            mock_settings.embedding_dimension = 768

            # Should initialize successfully with matching dimensions
            service = EmbeddingService()
            assert service.model is not None
            assert service.get_embedding_dimension() == 768


def test_embedding_service_preserves_other_errors():
    """Test that other initialization errors are still raised properly."""
    # Mock SentenceTransformer to raise a different error
    with patch("app.services.embedding_service.SentenceTransformer") as mock_st:
        mock_st.side_effect = RuntimeError("Model download failed")

        with patch("app.services.embedding_service.settings") as mock_settings:
            mock_settings.embedding_model = "invalid-model"
            mock_settings.embedding_dimension = 384

            # Should raise the original RuntimeError
            with pytest.raises(RuntimeError) as exc_info:
                EmbeddingService()

            assert "Model download failed" in str(exc_info.value)
