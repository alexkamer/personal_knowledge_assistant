"""
URL content extraction utilities.

Fetches and extracts main content from web pages.
"""
import logging
from typing import Optional
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


async def extract_text_from_url(url: str, timeout: int = 30) -> tuple[str, dict]:
    """
    Fetch a URL and extract its main text content.

    Args:
        url: The URL to fetch
        timeout: Request timeout in seconds

    Returns:
        Tuple of (extracted_text, metadata_dict)

    Raises:
        ValueError: If URL is invalid or content cannot be extracted
        httpx.HTTPError: If the request fails
    """
    # Validate URL
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        raise ValueError(f"Invalid URL: {url}")

    # Fetch the page
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        try:
            response = await client.get(url, headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            })
            response.raise_for_status()
        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch URL {url}: {e}")
            raise ValueError(f"Failed to fetch URL: {str(e)}")

    # Parse HTML
    soup = BeautifulSoup(response.text, 'html.parser')

    # Extract metadata
    metadata = _extract_metadata(soup, url)

    # Remove unwanted elements
    for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'iframe', 'noscript']):
        element.decompose()

    # Try to find main content
    content = _extract_main_content(soup)

    if not content or len(content.strip()) < 100:
        raise ValueError("Could not extract meaningful content from URL")

    return content, metadata


def _extract_metadata(soup: BeautifulSoup, url: str) -> dict:
    """Extract metadata from the HTML."""
    metadata = {
        "source_url": url,
        "source_type": "web",
    }

    # Identify source credibility level based on domain
    domain = url.split('/')[2]
    if 'plato.stanford.edu' in domain:
        metadata['source_credibility'] = 'high'
        metadata['source_name'] = 'Stanford Encyclopedia of Philosophy'
        metadata['source_category'] = 'academic'
    elif 'iep.utm.edu' in domain:
        metadata['source_credibility'] = 'high'
        metadata['source_name'] = 'Internet Encyclopedia of Philosophy'
        metadata['source_category'] = 'academic'
    elif 'britannica.com' in domain:
        metadata['source_credibility'] = 'high'
        metadata['source_name'] = 'Encyclopedia Britannica'
        metadata['source_category'] = 'encyclopedia'
    elif 'nasa.gov' in domain:
        metadata['source_credibility'] = 'high'
        metadata['source_name'] = 'NASA'
        metadata['source_category'] = 'government'
    elif 'nih.gov' in domain or 'ncbi.nlm.nih.gov' in domain or 'genome.gov' in domain:
        metadata['source_credibility'] = 'high'
        metadata['source_name'] = 'National Institutes of Health'
        metadata['source_category'] = 'government'
    elif 'cdc.gov' in domain:
        metadata['source_credibility'] = 'high'
        metadata['source_name'] = 'Centers for Disease Control'
        metadata['source_category'] = 'government'
    elif 'wikipedia.org' in domain:
        metadata['source_credibility'] = 'medium'
        metadata['source_name'] = 'Wikipedia'
        metadata['source_category'] = 'encyclopedia'

    # Title
    title_tag = soup.find('title')
    if title_tag:
        metadata['title'] = title_tag.get_text().strip()

    # Meta description
    meta_desc = soup.find('meta', attrs={'name': 'description'})
    if meta_desc and meta_desc.get('content'):
        metadata['description'] = meta_desc['content'].strip()

    # Open Graph metadata
    og_title = soup.find('meta', property='og:title')
    if og_title and og_title.get('content'):
        metadata['og_title'] = og_title['content'].strip()

    og_desc = soup.find('meta', property='og:description')
    if og_desc and og_desc.get('content'):
        metadata['og_description'] = og_desc['content'].strip()

    # Author
    author = soup.find('meta', attrs={'name': 'author'})
    if author and author.get('content'):
        metadata['author'] = author['content'].strip()

    # Publication date
    pub_date = soup.find('meta', property='article:published_time')
    if pub_date and pub_date.get('content'):
        metadata['published_date'] = pub_date['content'].strip()

    return metadata


def _extract_main_content(soup: BeautifulSoup) -> str:
    """
    Extract the main text content from the page.

    Tries multiple strategies to find the main content area,
    including specialized extractors for academic sources.
    """
    # Strategy 1: Stanford Encyclopedia of Philosophy
    sep_entry = soup.find(id='aueditable')
    if sep_entry:
        return _clean_text(sep_entry.get_text())

    # Strategy 2: Internet Encyclopedia of Philosophy
    iep_content = soup.find(id='post')
    if iep_content:
        return _clean_text(iep_content.get_text())

    # Strategy 3: Britannica articles
    britannica_content = soup.find(class_=lambda x: x and 'article-content' in ' '.join(x).lower())
    if britannica_content:
        return _clean_text(britannica_content.get_text())

    # Strategy 4: NASA articles
    nasa_content = soup.find(class_=lambda x: x and 'wysiwyg-content' in ' '.join(x).lower())
    if nasa_content:
        return _clean_text(nasa_content.get_text())

    # Strategy 5: NIH/NCBI articles
    ncbi_content = soup.find(class_='article')
    if ncbi_content:
        return _clean_text(ncbi_content.get_text())

    # Strategy 6: Look for article tag
    article = soup.find('article')
    if article:
        return _clean_text(article.get_text())

    # Strategy 7: Look for main tag
    main = soup.find('main')
    if main:
        return _clean_text(main.get_text())

    # Strategy 8: Look for div with id/class containing 'content', 'article', 'post'
    content_indicators = ['content', 'article', 'post', 'entry', 'text', 'body', 'main-content']
    for indicator in content_indicators:
        # Try ID
        content_div = soup.find(id=lambda x: x and indicator in x.lower())
        if content_div:
            text = _clean_text(content_div.get_text())
            if len(text.strip()) > 500:  # Only use if substantial content
                return text

        # Try class
        content_div = soup.find(class_=lambda x: x and indicator in ' '.join(x).lower())
        if content_div:
            text = _clean_text(content_div.get_text())
            if len(text.strip()) > 500:  # Only use if substantial content
                return text

    # Strategy 9: Fall back to body
    body = soup.find('body')
    if body:
        return _clean_text(body.get_text())

    # Strategy 10: Get all text as last resort
    return _clean_text(soup.get_text())


def _clean_text(text: str) -> str:
    """Clean and normalize extracted text."""
    # Split into lines
    lines = text.split('\n')

    # Remove leading/trailing whitespace from each line
    lines = [line.strip() for line in lines]

    # Remove empty lines
    lines = [line for line in lines if line]

    # Remove duplicate consecutive lines (often navigation items)
    cleaned_lines = []
    prev_line = None
    for line in lines:
        if line != prev_line:
            cleaned_lines.append(line)
            prev_line = line

    # Join with newlines
    return '\n'.join(cleaned_lines)
