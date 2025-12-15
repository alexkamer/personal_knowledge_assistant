"""
Embedding service using sentence-transformers for text vectorization.
"""
import logging
from typing import List

from sentence_transformers import SentenceTransformer

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating text embeddings using sentence-transformers."""

    def __init__(self):
        """Initialize the embedding model."""
        self.model_name = settings.embedding_model
        self.model = None
        self._initialize_model()

    def _initialize_model(self):
        """Load the sentence-transformers model."""
        try:
            logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"Embedding model loaded successfully. Dimension: {self.model.get_sentence_embedding_dimension()}")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise

    def get_embedding_dimension(self) -> int:
        """
        Get the dimensionality of the embeddings.

        Returns:
            Embedding dimension
        """
        if not self.model:
            raise RuntimeError("Embedding model not initialized")
        return self.model.get_sentence_embedding_dimension()

    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector as list of floats
        """
        if not self.model:
            raise RuntimeError("Embedding model not initialized")

        if not text or not text.strip():
            raise ValueError("Cannot embed empty text")

        try:
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts efficiently.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        if not self.model:
            raise RuntimeError("Embedding model not initialized")

        if not texts:
            return []

        # Filter out empty texts
        valid_texts = [text for text in texts if text and text.strip()]
        if not valid_texts:
            raise ValueError("No valid texts to embed")

        try:
            embeddings = self.model.encode(
                valid_texts,
                convert_to_numpy=True,
                batch_size=32,
                show_progress_bar=len(valid_texts) > 10,
            )
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {e}")
            raise


# Global instance for reuse across the application
_embedding_service: EmbeddingService | None = None


def get_embedding_service() -> EmbeddingService:
    """
    Get the global embedding service instance.

    Returns:
        Embedding service singleton
    """
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
