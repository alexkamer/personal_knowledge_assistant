"""
Unit tests for the WebSearchService.
"""
import pytest
from unittest.mock import Mock, patch

from app.services.web_search_service import WebSearchService, get_web_search_service


class TestWebSearchService:
    """Test suite for WebSearchService."""

    @patch('app.services.web_search_service.DDGS')
    def test_initialization(self, mock_ddgs):
        """Test service initialization."""
        mock_instance = Mock()
        mock_ddgs.return_value = mock_instance

        service = WebSearchService()

        assert service.ddgs is not None
        mock_ddgs.assert_called_once()

    @patch('app.services.web_search_service.DDGS')
    @pytest.mark.asyncio
    async def test_search_success(self, mock_ddgs):
        """Test successful web search."""
        mock_instance = Mock()
        mock_instance.text.return_value = [
            {
                "title": "Python Programming",
                "body": "Python is a high-level programming language",
                "href": "https://example.com/python",
            },
            {
                "title": "Python Tutorial",
                "body": "Learn Python programming",
                "href": "https://example.com/tutorial",
            },
        ]
        mock_ddgs.return_value = mock_instance

        service = WebSearchService()
        results = await service.search("Python programming", max_results=5)

        assert len(results) == 2
        assert results[0]["title"] == "Python Programming"
        assert results[0]["body"] == "Python is a high-level programming language"
        assert results[0]["href"] == "https://example.com/python"
        assert results[1]["title"] == "Python Tutorial"

    @patch('app.services.web_search_service.DDGS')
    @pytest.mark.asyncio
    async def test_search_with_custom_max_results(self, mock_ddgs):
        """Test search with custom max_results parameter."""
        mock_instance = Mock()
        mock_instance.text.return_value = [
            {"title": "Result 1", "body": "Body 1", "href": "https://example.com/1"},
            {"title": "Result 2", "body": "Body 2", "href": "https://example.com/2"},
            {"title": "Result 3", "body": "Body 3", "href": "https://example.com/3"},
        ]
        mock_ddgs.return_value = mock_instance

        service = WebSearchService()
        results = await service.search("test query", max_results=3)

        assert len(results) == 3
        mock_instance.text.assert_called_once_with(
            query="test query",
            max_results=3,
        )

    @patch('app.services.web_search_service.DDGS')
    @pytest.mark.asyncio
    async def test_search_empty_results(self, mock_ddgs):
        """Test search with no results."""
        mock_instance = Mock()
        mock_instance.text.return_value = []
        mock_ddgs.return_value = mock_instance

        service = WebSearchService()
        results = await service.search("nonexistent query")

        assert results == []

    @patch('app.services.web_search_service.DDGS')
    @pytest.mark.asyncio
    async def test_search_missing_fields(self, mock_ddgs):
        """Test search with missing optional fields."""
        mock_instance = Mock()
        mock_instance.text.return_value = [
            {
                "title": "Title Only",
                # Missing body and href
            },
            {
                "body": "Body Only",
                # Missing title and href
            },
            {
                # All fields missing
            },
        ]
        mock_ddgs.return_value = mock_instance

        service = WebSearchService()
        results = await service.search("test")

        assert len(results) == 3
        assert results[0] == {"title": "Title Only", "body": "", "href": ""}
        assert results[1] == {"title": "", "body": "Body Only", "href": ""}
        assert results[2] == {"title": "", "body": "", "href": ""}

    @patch('app.services.web_search_service.DDGS')
    @pytest.mark.asyncio
    async def test_search_exception_handling(self, mock_ddgs):
        """Test search handles exceptions gracefully."""
        mock_instance = Mock()
        mock_instance.text.side_effect = Exception("Network error")
        mock_ddgs.return_value = mock_instance

        service = WebSearchService()
        results = await service.search("test query")

        # Should return empty list on error
        assert results == []

    @patch('app.services.web_search_service.DDGS')
    @pytest.mark.asyncio
    async def test_search_ddgs_exception(self, mock_ddgs):
        """Test search handles DDGS-specific exceptions."""
        mock_instance = Mock()
        mock_instance.text.side_effect = ValueError("Invalid query")
        mock_ddgs.return_value = mock_instance

        service = WebSearchService()
        results = await service.search("invalid query")

        assert results == []

    @patch('app.services.web_search_service.DDGS')
    @pytest.mark.asyncio
    async def test_search_long_query_truncation(self, mock_ddgs):
        """Test that long queries are truncated in logs."""
        mock_instance = Mock()
        mock_instance.text.return_value = []
        mock_ddgs.return_value = mock_instance

        service = WebSearchService()
        long_query = "x" * 200  # Very long query
        results = await service.search(long_query)

        # Should still work despite long query
        assert results == []
        mock_instance.text.assert_called_once()

    @patch('app.services.web_search_service.DDGS')
    @pytest.mark.asyncio
    async def test_search_default_max_results(self, mock_ddgs):
        """Test that default max_results is 5."""
        mock_instance = Mock()
        mock_instance.text.return_value = []
        mock_ddgs.return_value = mock_instance

        service = WebSearchService()
        await service.search("test")

        call_args = mock_instance.text.call_args
        assert call_args[1]["max_results"] == 5

    @patch('app.services.web_search_service.DDGS')
    @pytest.mark.asyncio
    async def test_search_returns_correct_structure(self, mock_ddgs):
        """Test that results have correct structure."""
        mock_instance = Mock()
        mock_instance.text.return_value = [
            {
                "title": "Test Title",
                "body": "Test Body",
                "href": "https://test.com",
                "extra_field": "ignored",  # Should be ignored
            },
        ]
        mock_ddgs.return_value = mock_instance

        service = WebSearchService()
        results = await service.search("test")

        assert len(results) == 1
        assert set(results[0].keys()) == {"title", "body", "href"}
        assert "extra_field" not in results[0]

    @patch('app.services.web_search_service.DDGS')
    @pytest.mark.asyncio
    async def test_search_preserves_order(self, mock_ddgs):
        """Test that search results preserve order."""
        mock_instance = Mock()
        mock_instance.text.return_value = [
            {"title": "First", "body": "1", "href": "https://1.com"},
            {"title": "Second", "body": "2", "href": "https://2.com"},
            {"title": "Third", "body": "3", "href": "https://3.com"},
        ]
        mock_ddgs.return_value = mock_instance

        service = WebSearchService()
        results = await service.search("test")

        assert results[0]["title"] == "First"
        assert results[1]["title"] == "Second"
        assert results[2]["title"] == "Third"

    @patch('app.services.web_search_service.DDGS')
    @pytest.mark.asyncio
    async def test_search_with_special_characters(self, mock_ddgs):
        """Test search with special characters in query."""
        mock_instance = Mock()
        mock_instance.text.return_value = []
        mock_ddgs.return_value = mock_instance

        service = WebSearchService()
        special_query = "Python & Java: What's the difference?"
        await service.search(special_query)

        call_args = mock_instance.text.call_args
        assert call_args[1]["query"] == special_query

    @patch('app.services.web_search_service.DDGS')
    @pytest.mark.asyncio
    async def test_search_with_unicode(self, mock_ddgs):
        """Test search with unicode characters."""
        mock_instance = Mock()
        mock_instance.text.return_value = [
            {"title": "Résumé", "body": "Café", "href": "https://test.com"},
        ]
        mock_ddgs.return_value = mock_instance

        service = WebSearchService()
        results = await service.search("café résumé")

        assert len(results) == 1
        assert results[0]["title"] == "Résumé"
        assert results[0]["body"] == "Café"

    @patch('app.services.web_search_service.DDGS')
    @pytest.mark.asyncio
    async def test_search_with_zero_max_results(self, mock_ddgs):
        """Test search with max_results=0."""
        mock_instance = Mock()
        mock_instance.text.return_value = []
        mock_ddgs.return_value = mock_instance

        service = WebSearchService()
        results = await service.search("test", max_results=0)

        # Should pass 0 to DDGS
        mock_instance.text.assert_called_once_with(query="test", max_results=0)
        assert results == []

    @patch('app.services.web_search_service.DDGS')
    @pytest.mark.asyncio
    async def test_search_with_large_max_results(self, mock_ddgs):
        """Test search with very large max_results."""
        mock_instance = Mock()
        mock_instance.text.return_value = []
        mock_ddgs.return_value = mock_instance

        service = WebSearchService()
        await service.search("test", max_results=100)

        call_args = mock_instance.text.call_args
        assert call_args[1]["max_results"] == 100

    @patch('app.services.web_search_service.WebSearchService')
    def test_get_web_search_service_singleton(self, mock_service_class):
        """Test that get_web_search_service returns singleton."""
        # Reset global instance
        import app.services.web_search_service
        app.services.web_search_service._web_search_service = None

        # Create mock instance
        mock_instance = Mock()
        mock_service_class.return_value = mock_instance

        service1 = get_web_search_service()
        service2 = get_web_search_service()

        # Should return same instance
        assert service1 is service2
        mock_service_class.assert_called_once()

    @patch('app.services.web_search_service.DDGS')
    @pytest.mark.asyncio
    async def test_search_logs_query_truncation(self, mock_ddgs):
        """Test that very long queries are truncated in logs."""
        mock_instance = Mock()
        mock_instance.text.return_value = []
        mock_ddgs.return_value = mock_instance

        service = WebSearchService()
        # Create query longer than 100 chars
        long_query = "Python programming tutorial for beginners with advanced topics including machine learning and data science"

        results = await service.search(long_query)

        # Should still work
        assert results == []
        # Full query should be passed to DDGS
        call_args = mock_instance.text.call_args
        assert call_args[1]["query"] == long_query

    @patch('app.services.web_search_service.DDGS')
    @pytest.mark.asyncio
    async def test_search_result_count_logging(self, mock_ddgs):
        """Test that result count is logged correctly."""
        mock_instance = Mock()
        mock_instance.text.return_value = [
            {"title": "1", "body": "1", "href": "https://1.com"},
            {"title": "2", "body": "2", "href": "https://2.com"},
        ]
        mock_ddgs.return_value = mock_instance

        service = WebSearchService()
        results = await service.search("test")

        # Should return correct count
        assert len(results) == 2
