"""
Tests for URL content extraction utilities.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx
from bs4 import BeautifulSoup

from app.utils.url_extractor import (
    extract_text_from_url,
    _extract_metadata,
    _extract_main_content,
    _clean_text,
)


class TestExtractTextFromUrl:
    """Tests for extract_text_from_url function."""

    @pytest.mark.asyncio
    async def test_extract_text_from_url_success(self):
        """Test successful URL extraction."""
        html_content = """
        <html>
            <head>
                <title>Test Article</title>
                <meta name="description" content="Test description">
                <meta name="author" content="John Doe">
            </head>
            <body>
                <nav>Navigation</nav>
                <article>
                    <h1>Main Article Title</h1>
                    <p>This is the main content of the article. This is a longer paragraph to ensure we have enough content.</p>
                    <p>It has multiple paragraphs with substantial text content to pass the minimum length check.</p>
                    <p>Here is even more content to make sure the extraction succeeds with plenty of meaningful text.</p>
                </article>
                <footer>Footer content</footer>
            </body>
        </html>
        """

        mock_response = MagicMock()
        mock_response.text = html_content
        mock_response.raise_for_status = MagicMock()

        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

            content, metadata = await extract_text_from_url("https://example.com/article")

            assert "Main Article Title" in content
            assert "main content" in content
            assert "Navigation" not in content  # Should be removed
            assert "Footer" not in content  # Should be removed
            assert metadata["source_url"] == "https://example.com/article"
            assert metadata["title"] == "Test Article"
            assert metadata["description"] == "Test description"
            assert metadata["author"] == "John Doe"

    @pytest.mark.asyncio
    async def test_extract_text_from_url_invalid_url(self):
        """Test extraction with invalid URL."""
        with pytest.raises(ValueError, match="Invalid URL"):
            await extract_text_from_url("not-a-url")

    @pytest.mark.asyncio
    async def test_extract_text_from_url_http_error(self):
        """Test extraction when HTTP request fails."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_get = AsyncMock(side_effect=httpx.HTTPError("Connection failed"))
            mock_client.return_value.__aenter__.return_value.get = mock_get

            with pytest.raises(ValueError, match="Failed to fetch URL"):
                await extract_text_from_url("https://example.com/article")

    @pytest.mark.asyncio
    async def test_extract_text_from_url_no_content(self):
        """Test extraction when page has no meaningful content."""
        html_content = "<html><head><title>Empty</title></head><body></body></html>"

        mock_response = MagicMock()
        mock_response.text = html_content
        mock_response.raise_for_status = MagicMock()

        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

            with pytest.raises(ValueError, match="Could not extract meaningful content"):
                await extract_text_from_url("https://example.com/empty")


class TestExtractMetadata:
    """Tests for _extract_metadata function."""

    def test_extract_metadata_full(self):
        """Test metadata extraction with all fields present."""
        html = """
        <html>
            <head>
                <title>Test Title</title>
                <meta name="description" content="Test description">
                <meta name="author" content="Jane Smith">
                <meta property="og:title" content="OG Title">
                <meta property="og:description" content="OG Description">
                <meta property="article:published_time" content="2024-01-01">
            </head>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        metadata = _extract_metadata(soup, "https://example.com")

        assert metadata["source_url"] == "https://example.com"
        assert metadata["source_type"] == "web"
        assert metadata["title"] == "Test Title"
        assert metadata["description"] == "Test description"
        assert metadata["author"] == "Jane Smith"
        assert metadata["og_title"] == "OG Title"
        assert metadata["og_description"] == "OG Description"
        assert metadata["published_date"] == "2024-01-01"

    def test_extract_metadata_minimal(self):
        """Test metadata extraction with minimal fields."""
        html = "<html><head></head></html>"
        soup = BeautifulSoup(html, 'html.parser')
        metadata = _extract_metadata(soup, "https://example.com")

        assert metadata["source_url"] == "https://example.com"
        assert metadata["source_type"] == "web"
        assert "title" not in metadata
        assert "author" not in metadata


class TestExtractMainContent:
    """Tests for _extract_main_content function."""

    def test_extract_main_content_with_article_tag(self):
        """Test content extraction using article tag."""
        html = """
        <html>
            <body>
                <nav>Skip this</nav>
                <article>
                    <h1>Article Title</h1>
                    <p>Article content here.</p>
                </article>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        content = _extract_main_content(soup)

        assert "Article Title" in content
        assert "Article content" in content
        assert "Skip this" not in content

    def test_extract_main_content_with_main_tag(self):
        """Test content extraction using main tag."""
        html = """
        <html>
            <body>
                <header>Header</header>
                <main>
                    <h1>Main Content</h1>
                    <p>This is the main content.</p>
                </main>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        content = _extract_main_content(soup)

        assert "Main Content" in content
        assert "This is the main content" in content

    def test_extract_main_content_with_content_div(self):
        """Test content extraction using div with 'content' class."""
        html = """
        <html>
            <body>
                <div class="sidebar">Sidebar</div>
                <div class="main-content">
                    <h1>Page Title</h1>
                    <p>Page content.</p>
                </div>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        content = _extract_main_content(soup)

        assert "Page Title" in content
        assert "Page content" in content

    def test_extract_main_content_fallback_to_body(self):
        """Test content extraction falls back to body when no semantic tags found."""
        html = """
        <html>
            <body>
                <h1>Title</h1>
                <p>Content in body.</p>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        content = _extract_main_content(soup)

        assert "Title" in content
        assert "Content in body" in content


class TestCleanText:
    """Tests for _clean_text function."""

    def test_clean_text_removes_empty_lines(self):
        """Test that empty lines are removed."""
        text = "Line 1\n\n\nLine 2\n\n"
        cleaned = _clean_text(text)
        assert cleaned == "Line 1\nLine 2"

    def test_clean_text_strips_whitespace(self):
        """Test that leading/trailing whitespace is stripped from lines."""
        text = "  Line 1  \n   Line 2   "
        cleaned = _clean_text(text)
        assert cleaned == "Line 1\nLine 2"

    def test_clean_text_removes_duplicate_lines(self):
        """Test that duplicate consecutive lines are removed."""
        text = "Line 1\nLine 1\nLine 2\nLine 2\nLine 3"
        cleaned = _clean_text(text)
        assert cleaned == "Line 1\nLine 2\nLine 3"

    def test_clean_text_preserves_non_consecutive_duplicates(self):
        """Test that non-consecutive duplicate lines are preserved."""
        text = "Line 1\nLine 2\nLine 1"
        cleaned = _clean_text(text)
        assert cleaned == "Line 1\nLine 2\nLine 1"
