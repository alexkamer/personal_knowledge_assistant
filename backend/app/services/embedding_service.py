"""
Embedding service using sentence-transformers for text vectorization.
"""
import hashlib
import logging
from typing import List

from sentence_transformers import SentenceTransformer

from app.core.cache import cached_with_ttl, embedding_cache, create_cache_key
from app.core.config import settings
from app.core.retry import retry_with_backoff, embedding_circuit_breaker

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

    @staticmethod
    def _hash_text(text: str) -> str:
        """Create a hash of text for cache key."""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()

    @retry_with_backoff(
        max_retries=3,
        initial_delay=0.5,
        backoff_factor=2.0,
        exceptions=(Exception,),  # RuntimeError will not be retried
        circuit_breaker=embedding_circuit_breaker,
    )
    def _generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding with retry logic and circuit breaker.

        Args:
            text: Text to embed

        Returns:
            Embedding vector as list of floats
        """
        if not self.model:
            raise RuntimeError("Embedding model not initialized")

        try:
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        except RuntimeError:
            # Don't retry configuration errors
            raise

    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text with caching.

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
            # Check cache first
            cache_key = create_cache_key("embed_text", text)
            cached_result = embedding_cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Embedding cache hit for text: {text[:50]}...")
                return cached_result

            # Generate with retry logic
            embedding = self._generate_embedding(text)

            # Store in cache
            embedding_cache.set(cache_key, embedding)
            logger.debug(f"Cached embedding for text: {text[:50]}...")

            return embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts efficiently with retry logic.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        # Check preconditions before retry logic
        if not self.model:
            raise RuntimeError("Embedding model not initialized")

        if not texts:
            return []

        # Filter out empty texts
        valid_texts = [text for text in texts if text and text.strip()]
        if not valid_texts:
            raise ValueError("No valid texts to embed")

        # Call internal method with retry logic
        return self._embed_batch_with_retry(valid_texts)

    @retry_with_backoff(
        max_retries=3,
        initial_delay=1.0,
        backoff_factor=2.0,
        exceptions=(Exception,),
        circuit_breaker=embedding_circuit_breaker,
    )
    def _embed_batch_with_retry(self, valid_texts: List[str]) -> List[List[float]]:
        """Internal method with retry logic for batch embedding."""
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
