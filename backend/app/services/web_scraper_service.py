"""
Web scraping service using httpx and trafilatura.
"""
from typing import Optional
import logging

import httpx
import trafilatura

logger = logging.getLogger(__name__)


class WebScraperService:
    """
    Scrapes web content from URLs.

    For MVP, uses httpx + trafilatura for fast static page scraping.
    Future: Add Playwright for JavaScript-heavy sites.
    """

    def __init__(self):
        """Initialize web scraper service."""
        self.timeout = 30.0  # seconds
        self.max_retries = 2

    async def scrape(self, url: str) -> Optional[str]:
        """
        Scrape clean text content from a URL.

        Args:
            url: URL to scrape

        Returns:
            Clean text content or None if failed
        """
        try:
            return await self._scrape_static(url)
        except Exception as e:
            logger.error(f"Scraping failed for {url}: {e}")
            return None

    async def _scrape_static(self, url: str) -> Optional[str]:
        """
        Scrape static HTML with httpx + trafilatura.

        Args:
            url: URL to scrape

        Returns:
            Extracted text content or None
        """
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
                headers={
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
                }
            ) as client:
                # Make request
                response = await client.get(url)
                response.raise_for_status()

                # Try aggressive extraction first (better content extraction)
                content = trafilatura.extract(
                    response.text,
                    include_comments=False,
                    include_tables=True,
                    include_links=False,
                    no_fallback=False,  # Use fallback if main extraction fails
                    favor_precision=False,  # Favor recall over precision (get more content)
                    favor_recall=True,
                )

                # If content is too short, try with more aggressive settings
                if not content or len(content.strip()) < 500:
                    logger.info(f"First extraction yielded {len(content) if content else 0} chars, trying fallback")

                    # Try with even more aggressive extraction
                    content = trafilatura.extract(
                        response.text,
                        include_comments=False,
                        include_tables=True,
                        include_links=True,
                        no_fallback=True,  # Force fallback extraction
                        favor_precision=False,
                        favor_recall=True,
                    )

                # Minimum threshold: 500 characters (roughly 100 words)
                if not content or len(content.strip()) < 500:
                    logger.warning(
                        f"Content too short for {url}: {len(content) if content else 0} chars (need 500+)"
                    )
                    return None

                logger.info(f"Successfully extracted {len(content)} chars from {url}")
                return content

        except httpx.HTTPStatusError as e:
            logger.warning(f"HTTP error {e.response.status_code} for {url}")
            return None
        except httpx.TimeoutException:
            logger.warning(f"Timeout scraping {url}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error scraping {url}: {e}")
            return None


# Global instance
_web_scraper_service: Optional[WebScraperService] = None


def get_web_scraper_service() -> WebScraperService:
    """
    Get the global web scraper service instance.

    Returns:
        Web scraper service singleton
    """
    global _web_scraper_service
    if _web_scraper_service is None:
        _web_scraper_service = WebScraperService()
    return _web_scraper_service
