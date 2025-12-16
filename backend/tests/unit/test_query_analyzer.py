"""
Unit tests for the QueryAnalyzer service.
"""
import pytest

from app.services.query_analyzer import (
    QueryAnalyzer,
    QueryType,
    QueryComplexity,
    get_query_analyzer,
)


class TestQueryAnalyzer:
    """Test suite for QueryAnalyzer."""

    def test_initialization(self):
        """Test query analyzer initialization."""
        analyzer = QueryAnalyzer()

        assert analyzer.factual_keywords is not None
        assert analyzer.conceptual_keywords is not None
        assert analyzer.comparative_keywords is not None
        assert analyzer.procedural_keywords is not None
        assert analyzer.general_knowledge_indicators is not None

    def test_analyze_factual_query(self):
        """Test analyzing a factual query."""
        analyzer = QueryAnalyzer()

        query = "What is machine learning?"
        result = analyzer.analyze(query)

        assert result["query_type"] == QueryType.FACTUAL
        assert result["complexity"] == QueryComplexity.SIMPLE
        assert "retrieval_params" in result
        assert "needs_web_search" in result
        assert "needs_retrieval" in result

    def test_analyze_conceptual_query(self):
        """Test analyzing a conceptual query."""
        analyzer = QueryAnalyzer()

        query = "How does neural network training work?"
        result = analyzer.analyze(query)

        assert result["query_type"] == QueryType.CONCEPTUAL
        assert "retrieval_params" in result

    def test_analyze_comparative_query(self):
        """Test analyzing a comparative query."""
        analyzer = QueryAnalyzer()

        query = "Compare Python and JavaScript for web development"
        result = analyzer.analyze(query)

        assert result["query_type"] == QueryType.COMPARATIVE
        # Comparative queries should get more chunks
        assert result["retrieval_params"]["top_k"] == 5
        assert result["retrieval_params"]["max_final_chunks"] == 5

    def test_analyze_procedural_query(self):
        """Test analyzing a procedural query."""
        analyzer = QueryAnalyzer()

        query = "How to set up a FastAPI project?"
        result = analyzer.analyze(query)

        assert result["query_type"] == QueryType.PROCEDURAL
        # Procedural queries need more detail
        assert result["retrieval_params"]["top_k"] == 4

    def test_analyze_exploratory_query(self):
        """Test analyzing an exploratory query."""
        analyzer = QueryAnalyzer()

        query = "Tell me about deep learning"
        result = analyzer.analyze(query)

        assert result["query_type"] == QueryType.EXPLORATORY
        # Exploratory queries need broader context
        assert result["retrieval_params"]["top_k"] >= 3

    def test_complexity_simple(self):
        """Test simple complexity detection."""
        analyzer = QueryAnalyzer()

        query = "What is Python?"
        result = analyzer.analyze(query)

        assert result["complexity"] == QueryComplexity.SIMPLE

    def test_complexity_moderate(self):
        """Test moderate complexity detection."""
        analyzer = QueryAnalyzer()

        query = "What is Python and how is it used?"
        result = analyzer.analyze(query)

        assert result["complexity"] == QueryComplexity.MODERATE

    def test_complexity_complex(self):
        """Test complex query detection."""
        analyzer = QueryAnalyzer()

        query = "What is Python and how does it compare to JavaScript and what are the various use cases for both?"
        result = analyzer.analyze(query)

        assert result["complexity"] == QueryComplexity.COMPLEX

    def test_needs_retrieval_true(self):
        """Test that document-specific queries need retrieval."""
        analyzer = QueryAnalyzer()

        query = "What did the project report say about Q3 results?"
        result = analyzer.analyze(query)

        assert result["needs_retrieval"] is True

    def test_needs_retrieval_false_math(self):
        """Test that math queries don't need retrieval."""
        analyzer = QueryAnalyzer()

        query = "What is 2 + 2?"
        result = analyzer.analyze(query)

        assert result["needs_retrieval"] is False

    def test_needs_retrieval_false_capital(self):
        """Test that capital city queries don't need retrieval."""
        analyzer = QueryAnalyzer()

        query = "What is the capital of France?"
        result = analyzer.analyze(query)

        assert result["needs_retrieval"] is False

    def test_needs_retrieval_false_greeting(self):
        """Test that greetings don't need retrieval."""
        analyzer = QueryAnalyzer()

        for query in ["hello", "hi", "hey", "thanks"]:
            result = analyzer.analyze(query)
            assert result["needs_retrieval"] is False

    def test_needs_retrieval_false_basic_science(self):
        """Test that basic science facts don't need retrieval."""
        analyzer = QueryAnalyzer()

        query = "What is the speed of light?"
        result = analyzer.analyze(query)

        assert result["needs_retrieval"] is False

    def test_needs_retrieval_false_conversion(self):
        """Test that unit conversions don't need retrieval."""
        analyzer = QueryAnalyzer()

        query = "Convert 5 kilometers to miles"
        result = analyzer.analyze(query)

        assert result["needs_retrieval"] is False

    def test_needs_web_search_true_current_events(self):
        """Test that queries about current events need web search."""
        analyzer = QueryAnalyzer()

        query = "What are the latest developments in AI?"
        result = analyzer.analyze(query)

        assert result["needs_web_search"] is True

    def test_needs_web_search_true_exploratory(self):
        """Test that exploratory queries might need web search."""
        analyzer = QueryAnalyzer()

        query = "Tell me about blockchain"
        result = analyzer.analyze(query)

        assert result["needs_web_search"] is True

    def test_needs_web_search_false_factual(self):
        """Test that simple factual queries don't need web search."""
        analyzer = QueryAnalyzer()

        query = "What is TypeScript?"
        result = analyzer.analyze(query)

        # Should return None (undecided) for non-current, non-exploratory queries
        assert result["needs_web_search"] in [False, None]

    def test_retrieval_params_structure(self):
        """Test that retrieval params have correct structure."""
        analyzer = QueryAnalyzer()

        query = "What is Python?"
        result = analyzer.analyze(query)

        params = result["retrieval_params"]
        assert "initial_k" in params
        assert "top_k" in params
        assert "max_final_chunks" in params
        assert params["initial_k"] == 10  # Always 10 for re-ranking

    def test_retrieval_params_comparative(self):
        """Test retrieval params for comparative queries."""
        analyzer = QueryAnalyzer()

        query = "Compare Python versus JavaScript"
        result = analyzer.analyze(query)

        params = result["retrieval_params"]
        assert params["top_k"] == 5
        assert params["max_final_chunks"] == 5

    def test_retrieval_params_complex_adjustment(self):
        """Test that complex queries get more chunks."""
        analyzer = QueryAnalyzer()

        # Simple procedural query
        simple_query = "How to install Python?"
        simple_result = analyzer.analyze(simple_query)

        # Complex procedural query
        complex_query = "How to install Python and set up a virtual environment and also configure the IDE?"
        complex_result = analyzer.analyze(complex_query)

        # Complex query should get at least as many chunks
        assert complex_result["retrieval_params"]["top_k"] >= simple_result["retrieval_params"]["top_k"]

    def test_determine_type_factual(self):
        """Test factual query type detection."""
        analyzer = QueryAnalyzer()

        for keyword in ["what is", "who is", "when did", "where is", "define"]:
            query = f"{keyword} testing?"
            result = analyzer._determine_type(query.lower())
            assert result == QueryType.FACTUAL

    def test_determine_type_conceptual(self):
        """Test conceptual query type detection."""
        analyzer = QueryAnalyzer()

        for keyword in ["how does", "why does", "explain", "describe"]:
            query = f"{keyword} this work?"
            result = analyzer._determine_type(query.lower())
            assert result == QueryType.CONCEPTUAL

    def test_determine_type_comparative(self):
        """Test comparative query type detection."""
        analyzer = QueryAnalyzer()

        for keyword in ["compare", "difference between", "versus", "vs", "better than"]:
            query = f"{keyword} these two"
            result = analyzer._determine_type(query.lower())
            assert result == QueryType.COMPARATIVE

    def test_determine_type_procedural(self):
        """Test procedural query type detection."""
        analyzer = QueryAnalyzer()

        for keyword in ["how to", "steps to", "tutorial", "guide", "instructions"]:
            query = f"{keyword} do this"
            result = analyzer._determine_type(query.lower())
            assert result == QueryType.PROCEDURAL

    def test_determine_complexity_by_word_count(self):
        """Test complexity determination based on word count."""
        analyzer = QueryAnalyzer()

        # Simple: <= 8 words
        simple = "What is Python?"
        assert analyzer._determine_complexity(simple.lower(), QueryType.FACTUAL) == QueryComplexity.SIMPLE

        # Moderate: 9-15 words
        moderate = "What is Python and how is it different from other languages?"
        assert analyzer._determine_complexity(moderate.lower(), QueryType.FACTUAL) == QueryComplexity.MODERATE

        # Complex: > 15 words
        complex_query = "What is Python and how is it different from Java and also what are the main benefits of using Python for web development?"
        assert analyzer._determine_complexity(complex_query.lower(), QueryType.FACTUAL) == QueryComplexity.COMPLEX

    def test_determine_complexity_by_indicators(self):
        """Test complexity determination based on complexity indicators."""
        analyzer = QueryAnalyzer()

        # Two indicators -> complex
        query_with_indicators = "Python and JavaScript or Ruby"
        assert analyzer._determine_complexity(query_with_indicators.lower(), QueryType.FACTUAL) == QueryComplexity.COMPLEX

    def test_needs_document_retrieval_patterns(self):
        """Test document retrieval detection with various patterns."""
        analyzer = QueryAnalyzer()

        # Should NOT need retrieval (general knowledge)
        general_knowledge_queries = [
            "What is the capital of Spain?",
            "Who is the president of USA?",
            "What is the population of China?",
            "When is Christmas?",
            "What is the boiling point of water?",
            "How many planets are in the solar system?",
            "Define the word 'algorithm'",
            "What does 'debug' mean?",
            "How do you spell 'necessary'?",
            "When did World War 2 end?",
            "Convert 10 miles to kilometers",
        ]

        for query in general_knowledge_queries:
            result = analyzer._needs_document_retrieval(query.lower())
            assert result is False, f"Query '{query}' should not need retrieval"

        # Should need retrieval (document-specific)
        document_queries = [
            "What did the research paper conclude?",
            "According to my notes, what is the project timeline?",
            "What does the documentation say about API keys?",
        ]

        for query in document_queries:
            result = analyzer._needs_document_retrieval(query.lower())
            assert result is True, f"Query '{query}' should need retrieval"

    def test_needs_web_search_with_year(self):
        """Test web search detection with year indicators."""
        analyzer = QueryAnalyzer()

        queries_needing_web = [
            "What are the latest AI developments in 2024?",
            "Recent breakthroughs in quantum computing",
            "Current trends in web development",
            "New features in Python 2025",
        ]

        for query in queries_needing_web:
            result = analyzer.analyze(query)
            assert result["needs_web_search"] is True, f"Query '{query}' should need web search"

    def test_get_query_analyzer_returns_instance(self):
        """Test that get_query_analyzer returns an instance."""
        analyzer = get_query_analyzer()

        assert isinstance(analyzer, QueryAnalyzer)

    def test_analyze_returns_all_required_fields(self):
        """Test that analyze returns all required fields."""
        analyzer = QueryAnalyzer()

        query = "Test query"
        result = analyzer.analyze(query)

        required_fields = [
            "query_type",
            "complexity",
            "retrieval_params",
            "needs_web_search",
            "needs_retrieval",
        ]

        for field in required_fields:
            assert field in result, f"Missing required field: {field}"

    def test_analyze_case_insensitive(self):
        """Test that analysis is case-insensitive."""
        analyzer = QueryAnalyzer()

        query_lower = "what is python?"
        query_upper = "WHAT IS PYTHON?"
        query_mixed = "WhAt Is PyThOn?"

        result_lower = analyzer.analyze(query_lower)
        result_upper = analyzer.analyze(query_upper)
        result_mixed = analyzer.analyze(query_mixed)

        assert result_lower["query_type"] == result_upper["query_type"] == result_mixed["query_type"]
        assert result_lower["complexity"] == result_upper["complexity"] == result_mixed["complexity"]
