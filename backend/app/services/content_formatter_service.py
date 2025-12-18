"""
Content formatter service - formats scraped content into clean markdown.
"""
import logging
from typing import Optional

from app.services.llm_service import get_llm_service

logger = logging.getLogger(__name__)


class ContentFormatterService:
    """
    Formats scraped web content into clean, structured markdown.

    Takes raw text from web scraping and uses an LLM to:
    - Add proper markdown formatting (headings, code blocks, lists)
    - Preserve code examples with syntax highlighting
    - Clean up formatting issues
    - Maintain readability
    """

    def __init__(self):
        """Initialize content formatter service."""
        self.llm_service = get_llm_service()

    async def format_content(self, raw_content: str, url: str, title: Optional[str] = None) -> str:
        """
        Format raw scraped content into clean markdown.

        Args:
            raw_content: Raw text from web scraper
            url: Source URL (for context)
            title: Optional title of the source

        Returns:
            Formatted markdown content
        """
        try:
            # Build formatting prompt
            prompt = self._build_formatting_prompt(raw_content, url, title)

            # Get formatted content from LLM
            formatted = await self.llm_service.generate_answer(
                query="Format this content",
                context=raw_content,
                model="llama3.2:3b",  # Fast model for formatting
                temperature=0.3,  # Low temperature for consistent formatting
                system_prompt=prompt,
                stream=False,
            )

            return formatted.strip()

        except Exception as e:
            logger.error(f"Failed to format content from {url}: {e}")
            # Fallback to original content if formatting fails
            return raw_content

    def _build_formatting_prompt(
        self, raw_content: str, url: str, title: Optional[str] = None
    ) -> str:
        """
        Build prompt for LLM to format content.

        Args:
            raw_content: Raw text content
            url: Source URL
            title: Optional title

        Returns:
            Formatting prompt
        """
        title_context = f"Title: {title}\n" if title else ""

        return f"""Format the following web content into clean, well-structured markdown.

{title_context}URL: {url}

Instructions:
- Use proper markdown syntax (headings, code blocks, lists, etc.)
- Preserve all code examples in fenced code blocks with language tags (```python, ```javascript, etc.)
- Add appropriate headings (##, ###) to organize sections
- Use bullet points or numbered lists where appropriate
- Keep all information from the original content
- Make it highly readable and well-organized
- Do NOT add any extra commentary or explanations
- Do NOT add a title at the top (it's already displayed separately)

Raw Content:
{raw_content}

Formatted Markdown:"""


# Global instance
_content_formatter_service: Optional[ContentFormatterService] = None


def get_content_formatter_service() -> ContentFormatterService:
    """
    Get the global content formatter service instance.

    Returns:
        Content formatter service singleton
    """
    global _content_formatter_service
    if _content_formatter_service is None:
        _content_formatter_service = ContentFormatterService()
    return _content_formatter_service
