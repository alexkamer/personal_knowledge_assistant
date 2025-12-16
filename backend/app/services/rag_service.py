"""
RAG (Retrieval-Augmented Generation) service for semantic search and context assembly.
"""
import logging
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.chunk import Chunk
from app.models.note import Note
from app.models.document import Document
from app.services.embedding_service import get_embedding_service
from app.services.vector_service import get_vector_service
from app.services.web_search_service import get_web_search_service
from app.services.reranking_service import get_reranking_service

logger = logging.getLogger(__name__)


class RetrievedChunk:
    """Represents a chunk retrieved from vector search with its source info."""

    def __init__(
        self,
        chunk_id: str,
        content: str,
        distance: float,
        source_type: str,
        source_id: str,
        source_title: str,
        chunk_index: int,
    ):
        self.chunk_id = chunk_id
        self.content = content
        self.distance = distance
        self.source_type = source_type
        self.source_id = source_id
        self.source_title = source_title
        self.chunk_index = chunk_index

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "chunk_id": self.chunk_id,
            "content": self.content,
            "distance": self.distance,
            "source_type": self.source_type,
            "source_id": self.source_id,
            "source_title": self.source_title,
            "chunk_index": self.chunk_index,
        }


class RAGService:
    """Service for retrieval-augmented generation operations."""

    def __init__(self):
        """Initialize RAG service."""
        self.embedding_service = get_embedding_service()
        self.vector_service = get_vector_service()
        self.reranking_service = get_reranking_service() if settings.rerank_enabled else None

    async def search_relevant_chunks(
        self,
        db: AsyncSession,
        query: str,
        top_k: int = None,
        source_type: Optional[str] = None,
        exclude_notes: bool = True,
    ) -> List[RetrievedChunk]:
        """
        Search for relevant chunks using semantic similarity.

        Args:
            db: Database session
            query: Search query
            top_k: Number of chunks to retrieve (defaults to config)
            source_type: Optional filter for 'note' or 'document'
            exclude_notes: If True, excludes notes from search results (default: True)

        Returns:
            List of retrieved chunks with source information
        """
        top_k = top_k or settings.max_retrieval_chunks

        # If excluding notes, force source_type to 'document'
        if exclude_notes and source_type is None:
            source_type = 'document'

        # Generate embedding for the query
        logger.info(f"Generating embedding for query: {query[:50]}...")
        query_embedding = self.embedding_service.embed_text(query)

        # Search in vector database
        logger.info(f"Searching for top {top_k} similar chunks (source_type={source_type})")
        results = await self.vector_service.search_similar_chunks(
            query_embedding=query_embedding,
            n_results=top_k,
            source_type=source_type,
        )

        if not results["ids"] or not results["ids"][0]:
            logger.info("No relevant chunks found")
            return []

        # Extract results from ChromaDB response
        chunk_ids = results["ids"][0]
        distances = results["distances"][0]
        documents = results["documents"][0]
        metadatas = results["metadatas"][0]

        logger.info(f"Found {len(chunk_ids)} relevant chunks")

        # Fetch source titles from database
        retrieved_chunks = []
        for idx, chunk_id in enumerate(chunk_ids):
            metadata = metadatas[idx]
            source_type = metadata["source_type"]
            source_id = metadata["source_id"]

            # Get source title
            if source_type == "note":
                result = await db.execute(
                    select(Note.title).where(Note.id == source_id)
                )
                source_title = result.scalar_one_or_none() or "Unknown Note"
            else:
                result = await db.execute(
                    select(Document.filename).where(Document.id == source_id)
                )
                source_title = result.scalar_one_or_none() or "Unknown Document"

            retrieved_chunk = RetrievedChunk(
                chunk_id=chunk_id,
                content=documents[idx],
                distance=distances[idx],
                source_type=source_type,
                source_id=source_id,
                source_title=source_title,
                chunk_index=metadata["chunk_index"],
            )
            retrieved_chunks.append(retrieved_chunk)

        return retrieved_chunks

    def rerank_chunks(
        self,
        query: str,
        chunks: List[RetrievedChunk],
        top_k: int = None,
    ) -> List[RetrievedChunk]:
        """
        Re-rank chunks using cross-encoder for improved relevance.

        Args:
            query: Original search query
            chunks: List of retrieved chunks
            top_k: Number of top chunks to keep (defaults to config)

        Returns:
            Re-ranked list of chunks (top k only)
        """
        if not chunks or not self.reranking_service:
            return chunks

        top_k = top_k or settings.max_final_chunks

        # Extract text content for re-ranking
        texts = [chunk.content for chunk in chunks]

        # Get re-ranked indices and scores
        reranked_results = self.reranking_service.rerank(query, texts, top_k=top_k)

        # Build new list with re-ranked chunks
        reranked_chunks = []
        for original_idx, score in reranked_results:
            chunk = chunks[original_idx]
            # Update distance to reflect re-ranking score (higher is better, so invert)
            chunk.distance = 1.0 - score  # Convert score to distance-like metric
            reranked_chunks.append(chunk)

        logger.info(f"Re-ranked {len(chunks)} chunks down to top {len(reranked_chunks)}")
        return reranked_chunks

    def assemble_context(
        self,
        chunks: List[RetrievedChunk],
        max_tokens: int = None,
    ) -> tuple[str, List[dict]]:
        """
        Assemble context from retrieved chunks for the LLM prompt.

        Args:
            chunks: List of retrieved chunks
            max_tokens: Maximum tokens for context (defaults to config)

        Returns:
            Tuple of (assembled context string, source citations)
        """
        max_tokens = max_tokens or settings.max_context_tokens

        if not chunks:
            return "", []

        context_parts = []
        all_chunk_citations = []
        total_tokens = 0

        # Build context with source citations
        for idx, chunk in enumerate(chunks, 1):
            # Estimate tokens (rough: 4 chars per token)
            chunk_tokens = len(chunk.content) // 4

            if total_tokens + chunk_tokens > max_tokens:
                logger.info(f"Reached max context tokens ({max_tokens}), stopping at {idx-1} chunks")
                break

            # Add chunk with citation marker
            context_parts.append(f"[Source {idx}: {chunk.source_title}]\n{chunk.content}\n")

            # Track all chunk citations (including duplicates from same document)
            all_chunk_citations.append({
                "index": idx,
                "source_type": chunk.source_type,
                "source_id": chunk.source_id,
                "source_title": chunk.source_title,
                "chunk_index": chunk.chunk_index,
                "distance": chunk.distance,
            })

            total_tokens += chunk_tokens

        # Deduplicate citations by source (keep best distance for each unique source)
        unique_sources = {}
        for citation in all_chunk_citations:
            source_key = (citation["source_type"], citation["source_id"])
            if source_key not in unique_sources:
                unique_sources[source_key] = citation
            else:
                # Keep the one with better (lower) distance
                if citation["distance"] < unique_sources[source_key]["distance"]:
                    unique_sources[source_key] = citation

        # Convert back to list and re-index
        citations = []
        for new_idx, citation in enumerate(unique_sources.values(), 1):
            citation["index"] = new_idx
            citations.append(citation)

        context = "\n".join(context_parts)
        logger.info(f"Assembled context with {len(all_chunk_citations)} chunks from {len(citations)} unique sources (~{total_tokens} tokens)")

        return context, citations

    async def retrieve_and_assemble(
        self,
        db: AsyncSession,
        query: str,
        top_k: int = None,
        max_tokens: int = None,
        include_web_search: bool = True,  # Changed default to True
        exclude_notes: bool = True,  # Exclude notes by default
    ) -> tuple[str, List[dict]]:
        """
        Convenience method to search and assemble context in one call.

        Args:
            db: Database session
            query: Search query
            top_k: Number of chunks to retrieve (before re-ranking)
            max_tokens: Maximum tokens for context
            include_web_search: Whether to include web search results (default: True)
            exclude_notes: Whether to exclude notes from sources (default: True)

        Returns:
            Tuple of (assembled context, source citations)
        """
        # Get local chunks from knowledge base (documents only, no notes)
        chunks = await self.search_relevant_chunks(db, query, top_k=top_k, exclude_notes=exclude_notes)

        # Re-rank chunks to get the best ones
        if settings.rerank_enabled and chunks:
            logger.info(f"Applying re-ranking to {len(chunks)} chunks")
            chunks = self.rerank_chunks(query, chunks)
            logger.info(f"After re-ranking: {len(chunks)} chunks (distances: {[f'{c.distance:.3f}' for c in chunks]})")

        # Assemble context from re-ranked chunks
        context, citations = self.assemble_context(chunks, max_tokens=max_tokens)

        # Determine if we should add web search based on confidence
        should_add_web = include_web_search
        if chunks and include_web_search:
            # Check confidence of best match (lower distance = better match)
            best_distance = chunks[0].distance
            confidence_threshold = settings.web_search_confidence_threshold

            # If best match is good enough (distance < threshold), skip web search
            if best_distance < (1.0 - confidence_threshold):
                logger.info(f"Best match confidence high ({1.0 - best_distance:.2f}), skipping web search")
                should_add_web = False
            else:
                logger.info(f"Best match confidence low ({1.0 - best_distance:.2f}), adding web search")

        # Add web search results if needed
        if should_add_web:
            try:
                web_search_service = get_web_search_service()
                web_results = await web_search_service.search(query, max_results=3)

                if web_results:
                    # Add web results to context
                    web_context_parts = ["\n\n=== WEB SEARCH RESULTS ===\n"]
                    web_citations = []

                    for idx, result in enumerate(web_results, 1):
                        web_context_parts.append(
                            f"\n[Web Source {idx}] {result['title']}\n{result['body']}\n"
                        )
                        web_citations.append({
                            "index": len(citations) + idx,
                            "source_type": "web",
                            "source_id": result['href'],
                            "source_title": result['title'],
                            "chunk_index": 0,
                            "distance": 0.0,  # Web results don't have distance
                        })

                    context += "".join(web_context_parts)
                    citations.extend(web_citations)
                    logger.info(f"Added {len(web_results)} web search results to context")

            except Exception as e:
                logger.error(f"Failed to add web search results: {e}")
                # Continue without web results if search fails

        return context, citations


def get_rag_service() -> RAGService:
    """
    Get a RAG service instance.

    Returns:
        RAGService instance
    """
    return RAGService()
