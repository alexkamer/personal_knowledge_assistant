"""
Knowledge Search Tool - Allows agents to search the knowledge base.

This tool wraps the RAG orchestrator, enabling agents to perform
iterative, multi-step searches through their personal knowledge.
"""
import logging
from typing import Any, Dict, List

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.tools.base import BaseTool, ToolParameter, ToolResult
from app.services.rag_orchestrator import get_rag_orchestrator

logger = logging.getLogger(__name__)


class KnowledgeSearchTool(BaseTool):
    """
    Tool for searching the user's personal knowledge base.

    Uses RAG (Retrieval-Augmented Generation) to find relevant information
    from notes, documents, and web sources.
    """

    def __init__(self):
        """Initialize knowledge search tool."""
        super().__init__()
        self.rag_orchestrator = get_rag_orchestrator()
        self._db_session: AsyncSession = None

    @property
    def name(self) -> str:
        """Tool name."""
        return "knowledge_search"

    @property
    def description(self) -> str:
        """Tool description for LLM."""
        return (
            "Search the user's personal knowledge base including notes, documents, and web sources. "
            "Use this when you need factual information that might be in the user's stored knowledge. "
            "Returns relevant passages with source citations."
        )

    @property
    def parameters(self) -> List[ToolParameter]:
        """Tool parameters."""
        return [
            ToolParameter(
                name="query",
                type="string",
                description=(
                    "The search query. Be specific and focused. "
                    "Example: 'machine learning best practices' or 'Python async programming'"
                ),
                required=True,
            ),
            ToolParameter(
                name="include_notes",
                type="boolean",
                description=(
                    "Whether to include personal notes in search results. "
                    "Set to false for reputable sources only (documents, web). "
                    "Set to true to include personal thoughts and notes."
                ),
                required=False,
            ),
            ToolParameter(
                name="max_results",
                type="number",
                description=(
                    "Maximum number of relevant passages to return (1-20). "
                    "Default: 10. Use fewer for simple queries, more for complex topics."
                ),
                required=False,
            ),
        ]

    def set_db_session(self, db: AsyncSession) -> None:
        """
        Set the database session for this tool instance.

        Args:
            db: Async database session
        """
        self._db_session = db

    async def execute(
        self,
        query: str,
        include_notes: bool = False,
        max_results: int = 10,
        **kwargs
    ) -> ToolResult:
        """
        Execute knowledge search.

        Args:
            query: Search query
            include_notes: Include personal notes in results (default: False)
            max_results: Max passages to return (default: 10)
            **kwargs: Additional parameters (ignored)

        Returns:
            ToolResult with search results or error
        """
        if not self._db_session:
            logger.error("Knowledge search tool used without database session")
            return ToolResult(
                success=False,
                result=None,
                error="Database session not configured for knowledge search",
            )

        try:
            # Validate max_results range
            max_results = max(1, min(20, int(max_results)))

            logger.info(
                f"Executing knowledge search: query='{query[:50]}...', "
                f"include_notes={include_notes}, max_results={max_results}"
            )

            # Perform RAG search
            context, citations, metadata = await self.rag_orchestrator.process_query(
                db=self._db_session,
                query=query,
                top_k=max_results,
                exclude_notes=not include_notes,  # Invert for exclude_notes param
                force_web_search=None,  # Let orchestrator decide
            )

            # Check if we found anything
            if not citations or metadata.get("chunks_retrieved", 0) == 0:
                logger.info(f"No results found for query: {query[:50]}...")
                return ToolResult(
                    success=True,
                    result={
                        "found": False,
                        "message": "No relevant information found in knowledge base.",
                        "query": query,
                        "sources_searched": metadata,
                    },
                    metadata=metadata,
                )

            # Format results for LLM consumption
            formatted_results = self._format_results(context, citations, metadata)

            logger.info(
                f"Knowledge search successful: {metadata['chunks_retrieved']} chunks, "
                f"{metadata['unique_sources']} sources"
            )

            return ToolResult(
                success=True,
                result=formatted_results,
                metadata=metadata,
            )

        except Exception as e:
            logger.error(f"Knowledge search failed: {e}", exc_info=True)
            return ToolResult(
                success=False,
                result=None,
                error=f"Search failed: {str(e)}",
            )

    def _format_results(
        self,
        context: str,
        citations: List[Dict[str, Any]],
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Format search results for LLM consumption.

        Args:
            context: Assembled context text
            citations: Source citations
            metadata: Search metadata

        Returns:
            Formatted results dict
        """
        # Extract unique sources
        sources = []
        seen_sources = set()

        for citation in citations:
            source_id = citation.get("source_id")
            if source_id not in seen_sources:
                sources.append({
                    "type": citation.get("source_type"),
                    "title": citation.get("source_title"),
                    "id": source_id,
                })
                seen_sources.add(source_id)

        # Build result
        result = {
            "found": True,
            "query": metadata.get("query", ""),
            "num_results": metadata.get("chunks_retrieved", 0),
            "num_sources": len(sources),
            "context": context,
            "sources": sources,
            "metadata": {
                "query_type": metadata.get("query_type"),
                "complexity": metadata.get("complexity"),
                "web_search_used": metadata.get("web_search_used", False),
            },
        }

        return result
