"""
Query analyzer service for understanding query intent and complexity.
"""
import logging
import re
from enum import Enum
from typing import Dict, Any

logger = logging.getLogger(__name__)


class QueryType(str, Enum):
    """Types of queries the system can handle."""
    FACTUAL = "factual"  # Simple fact lookup (who, what, when, where)
    CONCEPTUAL = "conceptual"  # Explanation or understanding (how, why)
    COMPARATIVE = "comparative"  # Comparing multiple things
    PROCEDURAL = "procedural"  # Step-by-step instructions
    EXPLORATORY = "exploratory"  # Open-ended, requires broad context


class QueryComplexity(str, Enum):
    """Complexity levels for queries."""
    SIMPLE = "simple"  # Single concept, direct answer
    MODERATE = "moderate"  # Multiple concepts, some context needed
    COMPLEX = "complex"  # Multiple concepts, deep reasoning required


class QueryAnalyzer:
    """Analyzes queries to determine optimal retrieval strategy."""

    def __init__(self):
        """Initialize query analyzer."""
        # Keywords for identifying query types
        self.factual_keywords = ["what is", "who is", "when did", "where is", "define"]
        self.conceptual_keywords = ["how does", "why does", "explain", "describe"]
        self.comparative_keywords = ["compare", "difference between", "versus", "vs", "better than"]
        self.procedural_keywords = ["how to", "steps to", "tutorial", "guide", "instructions"]

        # Indicators that suggest a query is general knowledge (doesn't need retrieval)
        self.general_knowledge_indicators = [
            # Math/calculation patterns
            r"\b\d+\s*[\+\-\*\/×÷]\s*\d+",  # Basic arithmetic: 2+2, 5*8, etc.
            r"\bcalculate\b",
            r"\bsolve\b.*\bequation\b",

            # Common general knowledge
            r"\bcapital of\b",
            r"\bpresident of\b",
            r"\bpopulation of\b",
            r"\blargest\b.*\bcity\b",
            r"\bsmallest\b.*\bcountry\b",

            # Very simple greetings/chat
            r"^(hi|hello|hey|thanks|thank you)[\s\?!\.]*$",
        ]

    def analyze(self, query: str) -> Dict[str, Any]:
        """
        Analyze a query to determine its type and complexity.

        Args:
            query: User's question

        Returns:
            Dictionary with analysis results
        """
        query_lower = query.lower()

        # First check if this is a general knowledge question
        needs_retrieval = self._needs_document_retrieval(query_lower)

        # Determine query type
        query_type = self._determine_type(query_lower)

        # Determine complexity
        complexity = self._determine_complexity(query_lower, query_type)

        # Suggest retrieval parameters
        retrieval_params = self._suggest_retrieval_params(query_type, complexity)

        analysis = {
            "query_type": query_type,
            "complexity": complexity,
            "retrieval_params": retrieval_params,
            "needs_web_search": self._needs_web_search(query_lower, query_type),
            "needs_retrieval": needs_retrieval,
        }

        logger.info(f"Query analysis: type={query_type}, complexity={complexity}, "
                   f"needs_retrieval={needs_retrieval}, "
                   f"suggested_chunks={retrieval_params['top_k']}, "
                   f"needs_web={analysis['needs_web_search']}")

        return analysis

    def _needs_document_retrieval(self, query_lower: str) -> bool:
        """
        Determine if the query needs document retrieval or can be answered with general knowledge.

        Args:
            query_lower: Lowercased query string

        Returns:
            True if document retrieval is needed, False for general knowledge questions
        """
        # Check for general knowledge indicators using regex patterns
        for pattern in self.general_knowledge_indicators:
            if re.search(pattern, query_lower, re.IGNORECASE):
                logger.info(f"Query matches general knowledge pattern: {pattern}")
                return False

        # Default: assume retrieval is needed
        return True

    def _determine_type(self, query_lower: str) -> QueryType:
        """Determine the type of query."""
        if any(kw in query_lower for kw in self.comparative_keywords):
            return QueryType.COMPARATIVE

        if any(kw in query_lower for kw in self.procedural_keywords):
            return QueryType.PROCEDURAL

        if any(kw in query_lower for kw in self.conceptual_keywords):
            return QueryType.CONCEPTUAL

        if any(kw in query_lower for kw in self.factual_keywords):
            return QueryType.FACTUAL

        # Default to exploratory for open-ended questions
        return QueryType.EXPLORATORY

    def _determine_complexity(self, query_lower: str, query_type: QueryType) -> QueryComplexity:
        """Determine query complexity."""
        # Count question words and conjunctions
        complexity_indicators = ["and", "or", "but", "also", "multiple", "various"]
        indicator_count = sum(1 for word in complexity_indicators if word in query_lower)

        # Word count
        word_count = len(query_lower.split())

        # Complex queries are typically longer with multiple concepts
        if word_count > 15 or indicator_count >= 2:
            return QueryComplexity.COMPLEX

        if word_count > 8 or indicator_count >= 1:
            return QueryComplexity.MODERATE

        return QueryComplexity.SIMPLE

    def _suggest_retrieval_params(
        self,
        query_type: QueryType,
        complexity: QueryComplexity
    ) -> Dict[str, Any]:
        """
        Suggest optimal retrieval parameters based on query analysis.

        Returns parameters for initial retrieval before re-ranking.
        """
        # Base parameters
        params = {
            "initial_k": 10,  # Always retrieve 10 for re-ranking
            "top_k": 3,  # Default after re-ranking
            "max_final_chunks": 3,  # Final chunks to use
        }

        # Adjust based on query type and complexity
        if query_type == QueryType.COMPARATIVE:
            # Need more context to compare multiple things
            params["top_k"] = 5
            params["max_final_chunks"] = 5

        elif query_type == QueryType.EXPLORATORY:
            # Broader context needed
            params["top_k"] = 4
            params["max_final_chunks"] = 4

        elif query_type == QueryType.PROCEDURAL:
            # Step-by-step needs more detail
            params["top_k"] = 4
            params["max_final_chunks"] = 4

        # Adjust for complexity
        if complexity == QueryComplexity.COMPLEX:
            params["top_k"] = min(params["top_k"] + 1, 5)
            params["max_final_chunks"] = min(params["max_final_chunks"] + 1, 5)

        return params

    def _needs_web_search(self, query_lower: str, query_type: QueryType) -> bool:
        """
        Determine if query likely needs web search.

        Returns True if query seems to ask about current events, specific products,
        or things likely not in uploaded documents.
        """
        current_indicators = [
            "latest", "recent", "current", "today", "now",
            "2024", "2025", "new", "updated"
        ]

        # Queries about current events likely need web search
        if any(indicator in query_lower for indicator in current_indicators):
            return True

        # Exploratory queries might benefit from web search
        if query_type == QueryType.EXPLORATORY:
            return True

        # Default to letting the confidence check decide
        return None  # None means "undecided, use confidence threshold"


def get_query_analyzer() -> QueryAnalyzer:
    """
    Get a query analyzer instance.

    Returns:
        QueryAnalyzer instance
    """
    return QueryAnalyzer()
