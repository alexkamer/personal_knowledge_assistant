"""
Document search tool using existing RAG service.

Allows agents to search through stored documents and notes.
"""
import logging
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.tools.base import BaseTool, ToolParameter, ToolResult
from app.services.rag_orchestrator import get_rag_orchestrator

logger = logging.getLogger(__name__)


class DocumentSearchTool(BaseTool):
    """Tool for searching through stored documents and notes using RAG."""

    def __init__(self):
        """Initialize document search tool."""
        super().__init__()
        self._db_session: AsyncSession | None = None

    def set_db_session(self, db: AsyncSession) -> None:
        """
        Set database session for this tool execution.

        Args:
            db: Database session
        """
        self._db_session = db

    @property
    def name(self) -> str:
        return "document_search"

    @property
    def description(self) -> str:
        return (
            "Search through your stored documents and notes to find relevant information. "
            "Uses semantic search to find the most relevant passages. "
            "Useful when you need information from your personal knowledge base."
        )

    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="query",
                type="string",
                description="Search query to find relevant documents and notes",
                required=True,
            ),
            ToolParameter(
                name="top_k",
                type="number",
                description="Number of relevant passages to return (1-20)",
                required=False,
            ),
            ToolParameter(
                name="include_notes",
                type="boolean",
                description="Whether to include personal notes in search results",
                required=False,
            ),
        ]

    async def execute(
        self,
        query: str,
        top_k: int = 5,
        include_notes: bool = True,
        **kwargs
    ) -> ToolResult:
        """
        Execute document search.

        Args:
            query: Search query string
            top_k: Number of results to return (default: 5, max: 20)
            include_notes: Include personal notes (default: True)
            **kwargs: Additional arguments (ignored)

        Returns:
            ToolResult with search results or error
        """
        try:
            # Check if database session is set
            if self._db_session is None:
                return ToolResult(
                    success=False,
                    result=None,
                    error="Database session not set for document search",
                )

            # Validate top_k
            if top_k < 1 or top_k > 20:
                return ToolResult(
                    success=False,
                    result=None,
                    error="top_k must be between 1 and 20",
                )

            # Get RAG orchestrator
            rag_orchestrator = get_rag_orchestrator()

            logger.info(
                f"Searching documents for: {query} "
                f"(top_k={top_k}, include_notes={include_notes})"
            )

            # Perform RAG search and assembly
            context, citations = await rag_orchestrator.retrieve_and_assemble(
                db=self._db_session,
                query=query,
                top_k=top_k,
                include_notes=include_notes,
            )

            # Format results
            formatted_results = []
            for citation in citations:
                formatted_results.append({
                    "content": citation.content[:500] + "..." if len(citation.content) > 500 else citation.content,
                    "source_type": citation.source_type,
                    "source_title": citation.source_title,
                    "chunk_id": citation.chunk_id,
                })

            return ToolResult(
                success=True,
                result={
                    "query": query,
                    "results_count": len(formatted_results),
                    "context": context[:1000] + "..." if len(context) > 1000 else context,
                    "results": formatted_results,
                },
                metadata={
                    "tool": self.name,
                    "top_k": top_k,
                    "include_notes": include_notes,
                },
            )

        except Exception as e:
            logger.error(f"Document search failed: {e}")
            return ToolResult(
                success=False,
                result=None,
                error=f"Document search failed: {str(e)}",
            )
