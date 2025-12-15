"""
Web search service using DuckDuckGo.
"""
import logging
from typing import List, Dict

from ddgs import DDGS

logger = logging.getLogger(__name__)


class WebSearchService:
    """Service for performing web searches."""

    def __init__(self):
        """Initialize web search service."""
        self.ddgs = DDGS()

    async def search(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """
        Perform a web search and return results.

        Args:
            query: Search query
            max_results: Maximum number of results to return

        Returns:
            List of search results with title, body, and href
        """
        try:
            logger.info(f"Performing web search for: {query[:100]}...")

            # DuckDuckGo search is synchronous, but we wrap it in async context
            results = []

            # Perform text search
            search_results = self.ddgs.text(
                query=query,
                max_results=max_results,
            )

            for result in search_results:
                results.append({
                    "title": result.get("title", ""),
                    "body": result.get("body", ""),
                    "href": result.get("href", ""),
                })

            logger.info(f"Found {len(results)} web search results")
            return results

        except Exception as e:
            logger.error(f"Web search failed: {e}")
            return []


# Global instance
_web_search_service: WebSearchService | None = None


def get_web_search_service() -> WebSearchService:
    """
    Get the global web search service instance.

    Returns:
        Web search service singleton
    """
    global _web_search_service
    if _web_search_service is None:
        _web_search_service = WebSearchService()
    return _web_search_service
