"""
Unit tests for the embedding service.
"""
import pytest
from unittest.mock import Mock, patch

from app.services.embedding_service import EmbeddingService, get_embedding_service


class TestEmbeddingService:
    """Test suite for EmbeddingService."""

    @patch('app.services.embedding_service.SentenceTransformer')
    def test_initialization(self, mock_transformer):
        """Test service initialization."""
        mock_model = Mock()
        mock_model.get_sentence_embedding_dimension.return_value = 384
        mock_transformer.return_value = mock_model

        service = EmbeddingService()

        assert service.model is not None
        assert service.model_name == "sentence-transformers/all-MiniLM-L6-v2"
        mock_transformer.assert_called_once()

    @patch('app.services.embedding_service.SentenceTransformer')
    def test_get_embedding_dimension(self, mock_transformer):
        """Test getting embedding dimension."""
        mock_model = Mock()
        mock_model.get_sentence_embedding_dimension.return_value = 384
        mock_transformer.return_value = mock_model

        service = EmbeddingService()
        dimension = service.get_embedding_dimension()

        assert dimension == 384

    @patch('app.services.embedding_service.SentenceTransformer')
    def test_embed_text_success(self, mock_transformer):
        """Test embedding a single text successfully."""
        mock_model = Mock()
        mock_model.get_sentence_embedding_dimension.return_value = 384
        mock_embedding = Mock()
        mock_embedding.tolist.return_value = [0.1] * 384
        mock_model.encode.return_value = mock_embedding
        mock_transformer.return_value = mock_model

        service = EmbeddingService()
        embedding = service.embed_text("Test text")

        assert len(embedding) == 384
        assert all(isinstance(x, float) for x in embedding)
        mock_model.encode.assert_called_once_with("Test text", convert_to_numpy=True)

    @patch('app.services.embedding_service.SentenceTransformer')
    def test_embed_text_empty_raises_error(self, mock_transformer):
        """Test that embedding empty text raises an error."""
        mock_model = Mock()
        mock_model.get_sentence_embedding_dimension.return_value = 384
        mock_transformer.return_value = mock_model

        service = EmbeddingService()

        with pytest.raises(ValueError, match="Cannot embed empty text"):
            service.embed_text("")

        with pytest.raises(ValueError, match="Cannot embed empty text"):
            service.embed_text("   ")

    @patch('app.services.embedding_service.SentenceTransformer')
    def test_embed_text_caching(self, mock_transformer):
        """Test that embedding results are cached."""
        mock_model = Mock()
        mock_model.get_sentence_embedding_dimension.return_value = 384
        mock_embedding = Mock()
        mock_embedding.tolist.return_value = [0.1] * 384
        mock_model.encode.return_value = mock_embedding
        mock_transformer.return_value = mock_model

        service = EmbeddingService()

        # First call
        embedding1 = service.embed_text("Test text")
        # Second call with same text (should use cache)
        embedding2 = service.embed_text("Test text")

        assert embedding1 == embedding2
        # Model.encode should only be called once due to caching
        assert mock_model.encode.call_count == 1

    @patch('app.services.embedding_service.SentenceTransformer')
    def test_embed_batch_success(self, mock_transformer):
        """Test embedding multiple texts successfully."""
        mock_model = Mock()
        mock_model.get_sentence_embedding_dimension.return_value = 384
        mock_embeddings = Mock()
        mock_embeddings.tolist.return_value = [[0.1] * 384, [0.2] * 384, [0.3] * 384]
        mock_model.encode.return_value = mock_embeddings
        mock_transformer.return_value = mock_model

        service = EmbeddingService()
        texts = ["Text 1", "Text 2", "Text 3"]
        embeddings = service.embed_batch(texts)

        assert len(embeddings) == 3
        assert all(len(emb) == 384 for emb in embeddings)
        mock_model.encode.assert_called_once()

    @patch('app.services.embedding_service.SentenceTransformer')
    def test_embed_batch_empty_list(self, mock_transformer):
        """Test embedding empty list returns empty list."""
        mock_model = Mock()
        mock_model.get_sentence_embedding_dimension.return_value = 384
        mock_transformer.return_value = mock_model

        service = EmbeddingService()
        embeddings = service.embed_batch([])

        assert embeddings == []
        mock_model.encode.assert_not_called()

    @patch('app.services.embedding_service.SentenceTransformer')
    def test_embed_batch_filters_empty_texts(self, mock_transformer):
        """Test that batch embedding filters out empty texts."""
        mock_model = Mock()
        mock_model.get_sentence_embedding_dimension.return_value = 384
        mock_embeddings = Mock()
        mock_embeddings.tolist.return_value = [[0.1] * 384, [0.2] * 384]
        mock_model.encode.return_value = mock_embeddings
        mock_transformer.return_value = mock_model

        service = EmbeddingService()
        texts = ["Text 1", "", "Text 2", "   "]  # 2 empty texts
        embeddings = service.embed_batch(texts)

        # Should only embed the 2 valid texts
        assert len(embeddings) == 2
        # Check that encode was called with only valid texts
        call_args = mock_model.encode.call_args
        assert len(call_args[0][0]) == 2  # Only 2 valid texts passed

    @patch('app.services.embedding_service.SentenceTransformer')
    def test_hash_text_consistency(self, mock_transformer):
        """Test that text hashing is consistent."""
        mock_model = Mock()
        mock_model.get_sentence_embedding_dimension.return_value = 384
        mock_transformer.return_value = mock_model

        service = EmbeddingService()

        hash1 = service._hash_text("Test text")
        hash2 = service._hash_text("Test text")
        hash3 = service._hash_text("Different text")

        assert hash1 == hash2
        assert hash1 != hash3

    def test_get_embedding_service_singleton(self):
        """Test that get_embedding_service returns a singleton."""
        with patch('app.services.embedding_service.SentenceTransformer'):
            service1 = get_embedding_service()
            service2 = get_embedding_service()

            assert service1 is service2
