"""
Unit tests for the RAGOrchestrator.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4

from app.services.rag_orchestrator import RAGOrchestrator, get_rag_orchestrator
from app.services.query_analyzer import QueryType, QueryComplexity


class TestRAGOrchestrator:
    """Test suite for RAGOrchestrator."""

    @patch('app.services.rag_orchestrator.get_query_analyzer')
    @patch('app.services.rag_orchestrator.get_rag_service')
    def test_initialization(self, mock_get_rag, mock_get_analyzer):
        """Test orchestrator initialization."""
        mock_rag = Mock()
        mock_analyzer = Mock()
        mock_get_rag.return_value = mock_rag
        mock_get_analyzer.return_value = mock_analyzer

        orchestrator = RAGOrchestrator()

        assert orchestrator.rag_service is not None
        assert orchestrator.query_analyzer is not None
        mock_get_rag.assert_called_once()
        mock_get_analyzer.assert_called_once()

    @patch('app.services.rag_orchestrator.get_query_analyzer')
    @patch('app.services.rag_orchestrator.get_rag_service')
    @pytest.mark.asyncio
    async def test_process_query_general_knowledge_skips_retrieval(
        self, mock_get_rag, mock_get_analyzer
    ):
        """Test that general knowledge queries skip retrieval."""
        mock_analyzer = Mock()
        mock_analyzer.analyze.return_value = {
            "query_type": QueryType.FACTUAL,
            "complexity": QueryComplexity.SIMPLE,
            "needs_retrieval": False,
            "needs_web_search": False,
            "retrieval_params": {"initial_k": 10, "top_k": 3, "max_final_chunks": 3},
        }
        mock_get_analyzer.return_value = mock_analyzer
        mock_get_rag.return_value = Mock()

        orchestrator = RAGOrchestrator()
        mock_db = AsyncMock()

        context, citations, metadata = await orchestrator.process_query(
            db=mock_db,
            query="What is 2+2?"
        )

        assert context == ""
        assert citations == []
        assert metadata["retrieval_skipped"] is True
        assert metadata["chunks_retrieved"] == 0
        assert metadata["web_search_used"] is False

    @patch('app.services.rag_orchestrator.settings')
    @patch('app.services.rag_orchestrator.get_query_analyzer')
    @patch('app.services.rag_orchestrator.get_rag_service')
    @pytest.mark.asyncio
    async def test_process_query_with_retrieval(
        self, mock_get_rag, mock_get_analyzer, mock_settings
    ):
        """Test query processing with document retrieval."""
        # Mock query analyzer
        mock_analyzer = Mock()
        mock_analyzer.analyze.return_value = {
            "query_type": QueryType.FACTUAL,
            "complexity": QueryComplexity.SIMPLE,
            "needs_retrieval": True,
            "needs_web_search": False,
            "retrieval_params": {"initial_k": 10, "top_k": 3, "max_final_chunks": 3},
        }
        mock_get_analyzer.return_value = mock_analyzer

        # Mock RAG service
        mock_rag = Mock()
        mock_chunk = Mock()
        mock_chunk.distance = 0.1
        mock_rag.search_relevant_chunks = AsyncMock(return_value=[mock_chunk])
        mock_rag.rerank_chunks.return_value = [mock_chunk]
        mock_rag.assemble_context.return_value = ("Test context", [{"index": 1}])
        mock_get_rag.return_value = mock_rag

        # Mock settings
        mock_settings.rerank_enabled = True
        mock_settings.max_context_tokens = 1000
        mock_settings.web_search_confidence_threshold = 0.3

        orchestrator = RAGOrchestrator()
        mock_db = AsyncMock()

        context, citations, metadata = await orchestrator.process_query(
            db=mock_db,
            query="What is Python?"
        )

        assert context == "Test context"
        assert len(citations) == 1
        assert metadata["chunks_retrieved"] == 1
        assert metadata["unique_sources"] == 1
        mock_rag.search_relevant_chunks.assert_called_once()

    @patch('app.services.rag_orchestrator.settings')
    @patch('app.services.rag_orchestrator.get_query_analyzer')
    @patch('app.services.rag_orchestrator.get_rag_service')
    @pytest.mark.asyncio
    async def test_process_query_with_top_k_override(
        self, mock_get_rag, mock_get_analyzer, mock_settings
    ):
        """Test query processing with agent top_k override."""
        mock_analyzer = Mock()
        mock_analyzer.analyze.return_value = {
            "query_type": QueryType.FACTUAL,
            "complexity": QueryComplexity.SIMPLE,
            "needs_retrieval": True,
            "needs_web_search": False,
            "retrieval_params": {"initial_k": 10, "top_k": 3, "max_final_chunks": 3},
        }
        mock_get_analyzer.return_value = mock_analyzer

        mock_rag = Mock()
        mock_chunk = Mock()
        mock_chunk.distance = 0.1
        mock_rag.search_relevant_chunks = AsyncMock(return_value=[mock_chunk])
        mock_rag.rerank_chunks.return_value = [mock_chunk]
        mock_rag.assemble_context.return_value = ("Context", [])
        mock_get_rag.return_value = mock_rag

        mock_settings.rerank_enabled = True
        mock_settings.max_context_tokens = 1000
        mock_settings.web_search_confidence_threshold = 0.3

        orchestrator = RAGOrchestrator()
        mock_db = AsyncMock()

        # Use top_k override
        context, citations, metadata = await orchestrator.process_query(
            db=mock_db,
            query="Test query",
            top_k=5
        )

        # Should use override value
        mock_rag.search_relevant_chunks.assert_called_once_with(
            db=mock_db,
            query="Test query",
            top_k=5,
            exclude_notes=True
        )

    @patch('app.services.rag_orchestrator.settings')
    @patch('app.services.rag_orchestrator.get_query_analyzer')
    @patch('app.services.rag_orchestrator.get_rag_service')
    @pytest.mark.asyncio
    async def test_process_query_reranking_disabled(
        self, mock_get_rag, mock_get_analyzer, mock_settings
    ):
        """Test query processing with reranking disabled."""
        mock_analyzer = Mock()
        mock_analyzer.analyze.return_value = {
            "query_type": QueryType.FACTUAL,
            "complexity": QueryComplexity.SIMPLE,
            "needs_retrieval": True,
            "needs_web_search": False,
            "retrieval_params": {"initial_k": 10, "top_k": 3, "max_final_chunks": 3},
        }
        mock_get_analyzer.return_value = mock_analyzer

        mock_rag = Mock()
        mock_chunk = Mock()
        mock_chunk.distance = 0.1
        mock_rag.search_relevant_chunks = AsyncMock(return_value=[mock_chunk])
        mock_rag.assemble_context.return_value = ("Context", [])
        mock_get_rag.return_value = mock_rag

        # Disable reranking
        mock_settings.rerank_enabled = False
        mock_settings.max_context_tokens = 1000
        mock_settings.web_search_confidence_threshold = 0.3

        orchestrator = RAGOrchestrator()
        mock_db = AsyncMock()

        context, citations, metadata = await orchestrator.process_query(
            db=mock_db,
            query="Test query"
        )

        # Rerank should not be called
        mock_rag.rerank_chunks.assert_not_called()

    def test_decide_web_search_forced_true(self):
        """Test web search decision when forced true."""
        orchestrator = RAGOrchestrator()

        result = orchestrator._decide_web_search(
            chunks=[],
            analysis={},
            force_web_search=True
        )

        assert result is True

    def test_decide_web_search_forced_false(self):
        """Test web search decision when forced false."""
        orchestrator = RAGOrchestrator()

        result = orchestrator._decide_web_search(
            chunks=[Mock()],
            analysis={},
            force_web_search=False
        )

        assert result is False

    def test_decide_web_search_no_chunks(self):
        """Test web search enabled when no chunks found."""
        orchestrator = RAGOrchestrator()

        result = orchestrator._decide_web_search(
            chunks=[],
            analysis={"needs_web_search": False},
            force_web_search=None
        )

        assert result is True

    @patch('app.services.rag_orchestrator.settings')
    def test_decide_web_search_high_confidence(self, mock_settings):
        """Test web search skipped for high confidence matches."""
        orchestrator = RAGOrchestrator()
        mock_settings.web_search_confidence_threshold = 0.3

        mock_chunk = Mock()
        mock_chunk.distance = -0.6  # High confidence

        result = orchestrator._decide_web_search(
            chunks=[mock_chunk],
            analysis={"needs_web_search": None},
            force_web_search=None
        )

        assert result is False

    @patch('app.services.rag_orchestrator.settings')
    def test_decide_web_search_low_confidence(self, mock_settings):
        """Test web search enabled for low confidence matches."""
        orchestrator = RAGOrchestrator()
        mock_settings.web_search_confidence_threshold = 0.3

        mock_chunk = Mock()
        mock_chunk.distance = 0.5  # Low confidence

        result = orchestrator._decide_web_search(
            chunks=[mock_chunk],
            analysis={"needs_web_search": None},
            force_web_search=None
        )

        assert result is True

    @patch('app.services.rag_orchestrator.settings')
    def test_decide_web_search_analysis_recommends(self, mock_settings):
        """Test web search enabled when analysis recommends it."""
        orchestrator = RAGOrchestrator()
        mock_settings.web_search_confidence_threshold = 0.3

        mock_chunk = Mock()
        mock_chunk.distance = 0.2

        result = orchestrator._decide_web_search(
            chunks=[mock_chunk],
            analysis={"needs_web_search": True},
            force_web_search=None
        )

        assert result is True

    @patch('app.services.rag_orchestrator.settings')
    def test_decide_web_search_analysis_says_no(self, mock_settings):
        """Test web search skipped when analysis says no."""
        orchestrator = RAGOrchestrator()
        mock_settings.web_search_confidence_threshold = 0.3

        mock_chunk = Mock()
        mock_chunk.distance = 0.2

        result = orchestrator._decide_web_search(
            chunks=[mock_chunk],
            analysis={"needs_web_search": False},
            force_web_search=None
        )

        assert result is False

    @patch('app.services.web_search_service.get_web_search_service')
    @pytest.mark.asyncio
    async def test_add_web_search_success(self, mock_get_web_search):
        """Test adding web search results to context."""
        mock_web_service = Mock()
        mock_web_service.search = AsyncMock(return_value=[
            {
                "title": "Test Result",
                "body": "Test content",
                "href": "https://example.com",
            }
        ])
        mock_get_web_search.return_value = mock_web_service

        orchestrator = RAGOrchestrator()

        existing_context = "Existing context"
        existing_citations = [{"index": 1}]

        context, citations = await orchestrator._add_web_search(
            query="Test query",
            context=existing_context,
            citations=existing_citations
        )

        assert "WEB SEARCH RESULTS" in context
        assert "Test Result" in context
        assert len(citations) == 2  # 1 existing + 1 web
        assert citations[1]["source_type"] == "web"

    @patch('app.services.web_search_service.get_web_search_service')
    @pytest.mark.asyncio
    async def test_add_web_search_no_results(self, mock_get_web_search):
        """Test adding web search with no results."""
        mock_web_service = Mock()
        mock_web_service.search = AsyncMock(return_value=[])
        mock_get_web_search.return_value = mock_web_service

        orchestrator = RAGOrchestrator()

        context, citations = await orchestrator._add_web_search(
            query="Test query",
            context="Original",
            citations=[]
        )

        # Should return unchanged
        assert context == "Original"
        assert citations == []

    @patch('app.services.web_search_service.get_web_search_service')
    @pytest.mark.asyncio
    async def test_add_web_search_multiple_results(self, mock_get_web_search):
        """Test adding multiple web search results."""
        mock_web_service = Mock()
        mock_web_service.search = AsyncMock(return_value=[
            {"title": "Result 1", "body": "Body 1", "href": "https://1.com"},
            {"title": "Result 2", "body": "Body 2", "href": "https://2.com"},
            {"title": "Result 3", "body": "Body 3", "href": "https://3.com"},
        ])
        mock_get_web_search.return_value = mock_web_service

        orchestrator = RAGOrchestrator()

        context, citations = await orchestrator._add_web_search(
            query="Test query",
            context="",
            citations=[]
        )

        assert "Result 1" in context
        assert "Result 2" in context
        assert "Result 3" in context
        assert len(citations) == 3

    @patch('app.services.web_search_service.get_web_search_service')
    @pytest.mark.asyncio
    async def test_add_web_search_error_handling(self, mock_get_web_search):
        """Test that web search errors are handled gracefully."""
        mock_web_service = Mock()
        mock_web_service.search = AsyncMock(side_effect=Exception("Network error"))
        mock_get_web_search.return_value = mock_web_service

        orchestrator = RAGOrchestrator()

        context, citations = await orchestrator._add_web_search(
            query="Test query",
            context="Original",
            citations=[]
        )

        # Should return original context/citations on error
        assert context == "Original"
        assert citations == []

    @patch('app.services.rag_orchestrator.settings')
    @patch('app.services.web_search_service.get_web_search_service')
    @patch('app.services.rag_orchestrator.get_query_analyzer')
    @patch('app.services.rag_orchestrator.get_rag_service')
    @pytest.mark.asyncio
    async def test_process_query_with_web_search(
        self, mock_get_rag, mock_get_analyzer, mock_get_web_search, mock_settings
    ):
        """Test full query processing with web search."""
        # Mock analyzer
        mock_analyzer = Mock()
        mock_analyzer.analyze.return_value = {
            "query_type": QueryType.EXPLORATORY,
            "complexity": QueryComplexity.SIMPLE,
            "needs_retrieval": True,
            "needs_web_search": True,
            "retrieval_params": {"initial_k": 10, "top_k": 3, "max_final_chunks": 3},
        }
        mock_get_analyzer.return_value = mock_analyzer

        # Mock RAG service (no chunks)
        mock_rag = Mock()
        mock_rag.search_relevant_chunks = AsyncMock(return_value=[])
        mock_rag.assemble_context.return_value = ("", [])
        mock_get_rag.return_value = mock_rag

        # Mock web search
        mock_web_service = Mock()
        mock_web_service.search = AsyncMock(return_value=[
            {"title": "Web Result", "body": "Content", "href": "https://test.com"}
        ])
        mock_get_web_search.return_value = mock_web_service

        mock_settings.rerank_enabled = False
        mock_settings.max_context_tokens = 1000
        mock_settings.web_search_confidence_threshold = 0.3

        orchestrator = RAGOrchestrator()
        mock_db = AsyncMock()

        context, citations, metadata = await orchestrator.process_query(
            db=mock_db,
            query="Latest AI trends"
        )

        assert metadata["web_search_used"] is True
        assert "WEB SEARCH RESULTS" in context
        assert len(citations) == 1
        assert citations[0]["source_type"] == "web"

    def test_get_rag_orchestrator(self):
        """Test that get_rag_orchestrator returns instance."""
        orchestrator = get_rag_orchestrator()

        assert isinstance(orchestrator, RAGOrchestrator)

    @patch('app.services.rag_orchestrator.settings')
    @patch('app.services.rag_orchestrator.get_query_analyzer')
    @patch('app.services.rag_orchestrator.get_rag_service')
    @pytest.mark.asyncio
    async def test_process_query_empty_chunks_no_rerank(
        self, mock_get_rag, mock_get_analyzer, mock_settings
    ):
        """Test that reranking is skipped when no chunks are found."""
        mock_analyzer = Mock()
        mock_analyzer.analyze.return_value = {
            "query_type": QueryType.FACTUAL,
            "complexity": QueryComplexity.SIMPLE,
            "needs_retrieval": True,
            "needs_web_search": False,
            "retrieval_params": {"initial_k": 10, "top_k": 3, "max_final_chunks": 3},
        }
        mock_get_analyzer.return_value = mock_analyzer

        mock_rag = Mock()
        mock_rag.search_relevant_chunks = AsyncMock(return_value=[])
        mock_rag.assemble_context.return_value = ("", [])
        mock_get_rag.return_value = mock_rag

        mock_settings.rerank_enabled = True
        mock_settings.max_context_tokens = 1000
        mock_settings.web_search_confidence_threshold = 0.3

        orchestrator = RAGOrchestrator()
        mock_db = AsyncMock()

        context, citations, metadata = await orchestrator.process_query(
            db=mock_db,
            query="Test query"
        )

        # Rerank should not be called for empty chunks
        mock_rag.rerank_chunks.assert_not_called()

    @patch('app.services.rag_orchestrator.settings')
    @patch('app.services.rag_orchestrator.get_query_analyzer')
    @patch('app.services.rag_orchestrator.get_rag_service')
    @pytest.mark.asyncio
    async def test_process_query_exclude_notes_true_by_default(
        self, mock_get_rag, mock_get_analyzer, mock_settings
    ):
        """Test that exclude_notes defaults to True (reputable sources only)."""
        mock_analyzer = Mock()
        mock_analyzer.analyze.return_value = {
            "query_type": QueryType.FACTUAL,
            "complexity": QueryComplexity.SIMPLE,
            "needs_retrieval": True,
            "needs_web_search": False,
            "retrieval_params": {"initial_k": 10, "top_k": 3, "max_final_chunks": 3},
        }
        mock_get_analyzer.return_value = mock_analyzer

        mock_rag = Mock()
        mock_chunk = Mock()
        mock_chunk.distance = 0.1
        mock_rag.search_relevant_chunks = AsyncMock(return_value=[mock_chunk])
        mock_rag.rerank_chunks.return_value = [mock_chunk]
        mock_rag.assemble_context.return_value = ("Context", [])
        mock_get_rag.return_value = mock_rag

        mock_settings.rerank_enabled = False
        mock_settings.max_context_tokens = 1000
        mock_settings.web_search_confidence_threshold = 0.3

        orchestrator = RAGOrchestrator()
        mock_db = AsyncMock()

        # Call without specifying exclude_notes
        context, citations, metadata = await orchestrator.process_query(
            db=mock_db,
            query="Test query"
        )

        # Should use default exclude_notes=True
        mock_rag.search_relevant_chunks.assert_called_once_with(
            db=mock_db,
            query="Test query",
            top_k=10,
            exclude_notes=True
        )

    @patch('app.services.rag_orchestrator.settings')
    @patch('app.services.rag_orchestrator.get_query_analyzer')
    @patch('app.services.rag_orchestrator.get_rag_service')
    @pytest.mark.asyncio
    async def test_process_query_with_exclude_notes_false(
        self, mock_get_rag, mock_get_analyzer, mock_settings
    ):
        """Test that exclude_notes=False includes notes in search."""
        mock_analyzer = Mock()
        mock_analyzer.analyze.return_value = {
            "query_type": QueryType.FACTUAL,
            "complexity": QueryComplexity.SIMPLE,
            "needs_retrieval": True,
            "needs_web_search": False,
            "retrieval_params": {"initial_k": 10, "top_k": 3, "max_final_chunks": 3},
        }
        mock_get_analyzer.return_value = mock_analyzer

        mock_rag = Mock()
        mock_chunk = Mock()
        mock_chunk.distance = 0.1
        mock_rag.search_relevant_chunks = AsyncMock(return_value=[mock_chunk])
        mock_rag.rerank_chunks.return_value = [mock_chunk]
        mock_rag.assemble_context.return_value = ("Context with notes", [])
        mock_get_rag.return_value = mock_rag

        mock_settings.rerank_enabled = False
        mock_settings.max_context_tokens = 1000
        mock_settings.web_search_confidence_threshold = 0.3

        orchestrator = RAGOrchestrator()
        mock_db = AsyncMock()

        # Call with exclude_notes=False (include notes)
        context, citations, metadata = await orchestrator.process_query(
            db=mock_db,
            query="Test query",
            exclude_notes=False
        )

        # Should pass exclude_notes=False to search
        mock_rag.search_relevant_chunks.assert_called_once_with(
            db=mock_db,
            query="Test query",
            top_k=10,
            exclude_notes=False
        )

    @patch('app.services.rag_orchestrator.settings')
    @patch('app.services.rag_orchestrator.get_query_analyzer')
    @patch('app.services.rag_orchestrator.get_rag_service')
    @pytest.mark.asyncio
    async def test_process_query_with_exclude_notes_true_explicit(
        self, mock_get_rag, mock_get_analyzer, mock_settings
    ):
        """Test explicitly setting exclude_notes=True."""
        mock_analyzer = Mock()
        mock_analyzer.analyze.return_value = {
            "query_type": QueryType.FACTUAL,
            "complexity": QueryComplexity.SIMPLE,
            "needs_retrieval": True,
            "needs_web_search": False,
            "retrieval_params": {"initial_k": 10, "top_k": 3, "max_final_chunks": 3},
        }
        mock_get_analyzer.return_value = mock_analyzer

        mock_rag = Mock()
        mock_chunk = Mock()
        mock_chunk.distance = 0.1
        mock_rag.search_relevant_chunks = AsyncMock(return_value=[mock_chunk])
        mock_rag.rerank_chunks.return_value = [mock_chunk]
        mock_rag.assemble_context.return_value = ("Context without notes", [])
        mock_get_rag.return_value = mock_rag

        mock_settings.rerank_enabled = False
        mock_settings.max_context_tokens = 1000
        mock_settings.web_search_confidence_threshold = 0.3

        orchestrator = RAGOrchestrator()
        mock_db = AsyncMock()

        # Call with explicit exclude_notes=True
        context, citations, metadata = await orchestrator.process_query(
            db=mock_db,
            query="Test query",
            exclude_notes=True
        )

        # Should pass exclude_notes=True to search
        mock_rag.search_relevant_chunks.assert_called_once_with(
            db=mock_db,
            query="Test query",
            top_k=10,
            exclude_notes=True
        )
