"""
Hybrid search service combining semantic (vector) and keyword (BM25) search.
"""
import logging
from typing import List, Dict, Optional
from collections import defaultdict

from rank_bm25 import BM25Okapi
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chunk import Chunk

logger = logging.getLogger(__name__)


class HybridSearchService:
    """Service for hybrid search combining semantic and keyword-based retrieval."""

    def __init__(self):
        """Initialize hybrid search service."""
        self._bm25_index: Optional[BM25Okapi] = None
        self._chunk_map: Dict[str, Chunk] = {}  # chunk_id -> Chunk object

    async def build_bm25_index(self, db: AsyncSession, source_type: Optional[str] = None) -> None:
        """
        Build BM25 index from all chunks in the database.

        Args:
            db: Database session
            source_type: Optional filter for 'note' or 'document'
        """
        logger.info(f"Building BM25 index (source_type={source_type})")

        # Query chunks from database
        query = select(Chunk)
        if source_type == "note":
            query = query.where(Chunk.note_id.isnot(None))
        elif source_type == "document":
            query = query.where(Chunk.document_id.isnot(None))

        result = await db.execute(query)
        chunks = list(result.scalars().all())

        if not chunks:
            logger.warning("No chunks found for BM25 indexing")
            return

        # Tokenize chunk contents (simple whitespace tokenization)
        tokenized_corpus = []
        self._chunk_map = {}

        for chunk in chunks:
            # Simple tokenization (split by whitespace, lowercase)
            tokens = chunk.content.lower().split()
            tokenized_corpus.append(tokens)
            self._chunk_map[str(chunk.id)] = chunk

        # Build BM25 index
        self._bm25_index = BM25Okapi(tokenized_corpus)
        logger.info(f"Built BM25 index with {len(chunks)} chunks")

    def bm25_search(self, query: str, top_k: int = 10) -> List[tuple[str, float]]:
        """
        Perform BM25 keyword search.

        Args:
            query: Search query
            top_k: Number of results to return

        Returns:
            List of (chunk_id, score) tuples sorted by relevance
        """
        if not self._bm25_index or not self._chunk_map:
            logger.warning("BM25 index not initialized, returning empty results")
            return []

        # Tokenize query
        tokenized_query = query.lower().split()

        # Get BM25 scores
        scores = self._bm25_index.get_scores(tokenized_query)

        # Get chunk IDs in order
        chunk_ids = list(self._chunk_map.keys())

        # Combine chunk_ids with scores and sort
        results = sorted(
            zip(chunk_ids, scores),
            key=lambda x: x[1],
            reverse=True
        )[:top_k]

        logger.info(f"BM25 search found {len(results)} results for query: {query[:50]}")
        return results

    @staticmethod
    def reciprocal_rank_fusion(
        semantic_results: List[tuple[str, float]],
        bm25_results: List[tuple[str, float]],
        k: int = 60,
        semantic_weight: float = 0.7,
        bm25_weight: float = 0.3,
    ) -> List[tuple[str, float]]:
        """
        Combine semantic and BM25 results using Reciprocal Rank Fusion (RRF).

        RRF formula: score(chunk) = sum(weight / (k + rank))
        where rank is the position in the result list (1-indexed)

        Args:
            semantic_results: List of (chunk_id, distance) from semantic search
            bm25_results: List of (chunk_id, bm25_score) from BM25 search
            k: RRF constant (default 60, standard value)
            semantic_weight: Weight for semantic search (default 0.7)
            bm25_weight: Weight for BM25 search (default 0.3)

        Returns:
            List of (chunk_id, fused_score) sorted by fused score
        """
        fused_scores = defaultdict(float)

        # Process semantic results (convert distance to rank)
        # Lower distance = better, so rank 1 is best
        for rank, (chunk_id, distance) in enumerate(semantic_results, 1):
            fused_scores[chunk_id] += semantic_weight / (k + rank)

        # Process BM25 results (higher score = better)
        for rank, (chunk_id, bm25_score) in enumerate(bm25_results, 1):
            fused_scores[chunk_id] += bm25_weight / (k + rank)

        # Sort by fused score (descending)
        sorted_results = sorted(
            fused_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        logger.info(f"Fused {len(semantic_results)} semantic + {len(bm25_results)} BM25 results into {len(sorted_results)} unique results")
        return sorted_results


# Global instance
_hybrid_search_service: HybridSearchService | None = None


def get_hybrid_search_service() -> HybridSearchService:
    """
    Get the global hybrid search service instance.

    Returns:
        Hybrid search service singleton
    """
    global _hybrid_search_service
    if _hybrid_search_service is None:
        _hybrid_search_service = HybridSearchService()
    return _hybrid_search_service
