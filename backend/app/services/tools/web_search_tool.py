"""
Web search tool using existing WebSearchService.

Allows agents to search the web for information using DuckDuckGo.
"""
import logging
from typing import List

from app.services.tools.base import BaseTool, ToolParameter, ToolResult
from app.services.web_search_service import get_web_search_service

logger = logging.getLogger(__name__)


class WebSearchTool(BaseTool):
    """Tool for searching the web using DuckDuckGo."""

    @property
    def name(self) -> str:
        return "web_search"

    @property
    def description(self) -> str:
        return (
            "Search the web for information using DuckDuckGo. "
            "Use this when you need current information, facts, news, or data "
            "that might not be in your knowledge base."
        )

    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="query",
                type="string",
                description="The search query to look up on the web",
                required=True,
            ),
            ToolParameter(
                name="max_results",
                type="number",
                description="Maximum number of search results to return (1-10)",
                required=False,
            ),
        ]

    async def execute(self, query: str, max_results: int = 5, **kwargs) -> ToolResult:
        """
        Execute web search.

        Args:
            query: Search query string
            max_results: Maximum number of results (default: 5, max: 10)
            **kwargs: Additional arguments (ignored)

        Returns:
            ToolResult with search results or error
        """
        try:
            # Validate max_results
            if max_results < 1 or max_results > 10:
                return ToolResult(
                    success=False,
                    result=None,
                    error="max_results must be between 1 and 10",
                )

            # Get web search service
            web_search_service = get_web_search_service()

            # Perform search
            logger.info(f"Searching web for: {query} (max_results={max_results})")
            search_results = await web_search_service.search(query, max_results=max_results)

            # Format results
            formatted_results = []
            for result in search_results:
                formatted_results.append({
                    "title": result.title,
                    "snippet": result.snippet,
                    "url": result.url,
                })

            return ToolResult(
                success=True,
                result={
                    "query": query,
                    "results_count": len(formatted_results),
                    "results": formatted_results,
                },
                metadata={
                    "tool": self.name,
                    "max_results": max_results,
                },
            )

        except Exception as e:
            logger.error(f"Web search failed: {e}")
            return ToolResult(
                success=False,
                result=None,
                error=f"Web search failed: {str(e)}",
            )
