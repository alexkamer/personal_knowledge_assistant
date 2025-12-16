"""
Re-ranking service using cross-encoder models for improved relevance.
"""
import logging
from typing import List, Tuple

from sentence_transformers import CrossEncoder

logger = logging.getLogger(__name__)


class RerankingService:
    """Service for re-ranking retrieved chunks using cross-encoder models."""

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        """
        Initialize re-ranking service.

        Args:
            model_name: Name of the cross-encoder model to use
        """
        logger.info(f"Loading cross-encoder model: {model_name}")
        self.model = CrossEncoder(model_name)
        logger.info("Cross-encoder model loaded successfully")

    def rerank(
        self,
        query: str,
        texts: List[str],
        top_k: int = 3,
    ) -> List[Tuple[int, float]]:
        """
        Re-rank texts based on relevance to query.

        Args:
            query: The search query
            texts: List of text candidates to re-rank
            top_k: Number of top results to return

        Returns:
            List of tuples (original_index, score) sorted by relevance
        """
        if not texts:
            return []

        # Create query-text pairs
        pairs = [[query, text] for text in texts]

        # Get relevance scores
        logger.info(f"Re-ranking {len(texts)} texts, keeping top {top_k}")
        scores = self.model.predict(pairs)

        # Create list of (index, score) tuples and sort by score (descending)
        ranked_results = [(idx, float(score)) for idx, score in enumerate(scores)]
        ranked_results.sort(key=lambda x: x[1], reverse=True)

        # Return top k results
        top_results = ranked_results[:top_k]
        logger.info(f"Top {len(top_results)} scores: {[f'{score:.3f}' for _, score in top_results]}")

        return top_results


# Global instance
_reranking_service = None


def get_reranking_service() -> RerankingService:
    """
    Get or create a global re-ranking service instance.

    Returns:
        RerankingService instance
    """
    global _reranking_service
    if _reranking_service is None:
        _reranking_service = RerankingService()
    return _reranking_service
