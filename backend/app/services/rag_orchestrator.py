"""
RAG Orchestrator - Coordinates the entire RAG pipeline with intelligent decision-making.
"""
import logging
from typing import List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.services.rag_service import RAGService, get_rag_service
from app.services.query_analyzer import QueryAnalyzer, get_query_analyzer

logger = logging.getLogger(__name__)


class RAGOrchestrator:
    """
    Orchestrates the RAG pipeline with intelligent query analysis and adaptive retrieval.
    """

    def __init__(self):
        """Initialize RAG orchestrator."""
        self.rag_service = get_rag_service()
        self.query_analyzer = get_query_analyzer()

    async def process_query(
        self,
        db: AsyncSession,
        query: str,
        force_web_search: bool = None,
        top_k: int = None,
        exclude_notes: bool = True,
    ) -> Tuple[str, List[dict], Dict[str, Any]]:
        """
        Process a query through the intelligent RAG pipeline.

        Args:
            db: Database session
            query: User's question
            force_web_search: Force web search on/off (overrides analysis)
            top_k: Override for number of chunks to retrieve (for agent config)
            exclude_notes: Exclude notes from search (default: True for reputable sources only)

        Returns:
            Tuple of (context, citations, metadata)
        """
        logger.info(f"Processing query: {query[:100]}...")

        # Step 1: Analyze the query
        analysis = self.query_analyzer.analyze(query)
        logger.info(f"Query analysis complete: {analysis}")

        # Step 2: Check if retrieval is needed
        if not analysis.get("needs_retrieval", True):
            logger.info("Query is general knowledge - skipping document retrieval")
            # Return empty context and citations for general knowledge questions
            metadata = {
                "query_type": analysis["query_type"],
                "complexity": analysis["complexity"],
                "chunks_retrieved": 0,
                "unique_sources": 0,
                "web_search_used": False,
                "retrieval_skipped": True,
            }
            return "", [], metadata

        # Step 3: Determine retrieval parameters (use override if provided)
        retrieval_params = analysis["retrieval_params"]
        if top_k is not None:
            # Agent override - use simple 1:1 ratio
            top_k_initial = top_k
            top_k_final = top_k
            logger.info(f"Using agent override: top_k={top_k}")
        else:
            # Use query analyzer's recommendations
            top_k_initial = retrieval_params["initial_k"]
            top_k_final = retrieval_params["max_final_chunks"]

        # Step 4: Retrieve and re-rank chunks
        chunks = await self.rag_service.search_relevant_chunks(
            db=db,
            query=query,
            top_k=top_k_initial,
            exclude_notes=exclude_notes
        )

        logger.info(f"Retrieved {len(chunks)} initial chunks")

        # Step 5: Re-rank chunks to get the best ones
        if settings.rerank_enabled and chunks:
            logger.info(f"Re-ranking to top {top_k_final} chunks")
            chunks = self.rag_service.rerank_chunks(
                query=query,
                chunks=chunks,
                top_k=top_k_final
            )

        # Step 6: Assemble context with deduplication
        context, citations = self.rag_service.assemble_context(
            chunks=chunks,
            max_tokens=settings.max_context_tokens
        )

        # Step 7: Decide on web search
        should_use_web = self._decide_web_search(
            chunks=chunks,
            analysis=analysis,
            force_web_search=force_web_search
        )

        # Step 8: Add web search if needed
        if should_use_web:
            context, citations = await self._add_web_search(
                query=query,
                context=context,
                citations=citations
            )

        # Prepare metadata
        metadata = {
            "query_type": analysis["query_type"],
            "complexity": analysis["complexity"],
            "chunks_retrieved": len(chunks),
            "unique_sources": len(citations),
            "web_search_used": should_use_web,
        }

        logger.info(f"Query processing complete: {metadata}")

        return context, citations, metadata

    def _decide_web_search(
        self,
        chunks: List,
        analysis: Dict[str, Any],
        force_web_search: bool = None
    ) -> bool:
        """
        Intelligently decide whether to use web search.

        Args:
            chunks: Retrieved chunks
            analysis: Query analysis results
            force_web_search: User override

        Returns:
            True if web search should be used
        """
        # User override takes precedence
        if force_web_search is not None:
            logger.info(f"Web search forced: {force_web_search}")
            return force_web_search

        # If no chunks found, definitely use web search
        if not chunks:
            logger.info("No chunks found, enabling web search")
            return True

        # Check query analysis recommendation
        if analysis.get("needs_web_search") is True:
            logger.info("Query analysis recommends web search")
            return True

        # Check confidence of best match
        best_distance = chunks[0].distance
        confidence_threshold = settings.web_search_confidence_threshold

        # Lower distance = better match (for cross-encoder scores, we inverted them)
        # If score is negative (after inversion), it means original score was > 1.0 (very good)
        if best_distance < -0.5:  # Very high confidence (original score > 1.5)
            logger.info(f"High confidence match (distance={best_distance:.2f}), skipping web search")
            return False

        # Medium confidence - use query analysis suggestion
        if analysis.get("needs_web_search") is False:
            logger.info("Medium confidence but query doesn't need web search")
            return False

        # Default: use web search for safety
        logger.info(f"Medium/low confidence (distance={best_distance:.2f}), enabling web search")
        return True

    async def _add_web_search(
        self,
        query: str,
        context: str,
        citations: List[dict]
    ) -> Tuple[str, List[dict]]:
        """
        Add web search results to context.

        Args:
            query: User's question
            context: Existing context
            citations: Existing citations

        Returns:
            Updated (context, citations)
        """
        try:
            from app.services.web_search_service import get_web_search_service

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
                        "distance": 0.0,
                    })

                context += "".join(web_context_parts)
                citations.extend(web_citations)
                logger.info(f"Added {len(web_results)} web search results to context")

        except Exception as e:
            logger.error(f"Failed to add web search results: {e}")
            # Continue without web results

        return context, citations


def get_rag_orchestrator() -> RAGOrchestrator:
    """
    Get a RAG orchestrator instance.

    Returns:
        RAGOrchestrator instance
    """
    return RAGOrchestrator()
