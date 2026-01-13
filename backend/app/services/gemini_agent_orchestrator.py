"""
Gemini Agent Orchestrator - Uses Gemini's native function calling for agentic RAG.

This orchestrator leverages Gemini's built-in function calling capabilities
instead of prompt engineering, providing more reliable tool use.
"""

import logging
from typing import Any, Dict, List, Optional

from google import genai
from google.genai import types
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.services.rag_orchestrator import get_rag_orchestrator
from app.services.tools.knowledge_search_tool import KnowledgeSearchTool

logger = logging.getLogger(__name__)


class GeminiAgentOrchestrator:
    """Orchestrates agentic RAG using Gemini's native function calling."""

    def __init__(self):
        """Initialize Gemini agent orchestrator."""
        if not settings.gemini_api_key:
            raise ValueError("Gemini API key not configured")

        # Use Google AI API (not Vertex AI)
        # Explicitly disable Vertex AI to override environment variables
        self.client = genai.Client(api_key=settings.gemini_api_key, vertexai=False)
        self.rag_orchestrator = get_rag_orchestrator()
        logger.info("Gemini agent orchestrator initialized (Google AI API mode)")

    def _create_function_declarations(self) -> List[types.FunctionDeclaration]:
        """
        Create Gemini function declarations from our knowledge search tool.

        Returns:
            List of function declarations in Gemini format
        """
        return [
            types.FunctionDeclaration(
                name="knowledge_search",
                description=(
                    "Search the user's personal knowledge base including notes, documents, and web sources. "
                    "Use this when you need factual information that might be in the user's stored knowledge. "
                    "Returns relevant passages with source citations."
                ),
                parameters_json_schema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": (
                                "The search query. Be specific and focused. "
                                "Example: 'machine learning best practices' or 'Python async programming'"
                            ),
                        },
                        "include_notes": {
                            "type": "boolean",
                            "description": (
                                "Whether to include personal notes in search results. "
                                "Set to false for reputable sources only (documents, web). "
                                "Set to true to include personal thoughts and notes."
                            ),
                        },
                        "max_results": {
                            "type": "integer",
                            "description": (
                                "Maximum number of relevant passages to return (1-20). "
                                "Default: 10. Use fewer for simple queries, more for complex topics."
                            ),
                        },
                    },
                    "required": ["query"],
                },
            )
        ]

    async def _execute_knowledge_search(
        self,
        db: AsyncSession,
        query: str,
        include_notes: bool = False,
        max_results: int = 10,
    ) -> Dict[str, Any]:
        """
        Execute knowledge search tool.

        Args:
            db: Database session
            query: Search query
            include_notes: Include personal notes
            max_results: Max results to return

        Returns:
            Search results
        """
        tool = KnowledgeSearchTool()
        tool.set_db_session(db)

        result = await tool.execute(
            query=query,
            include_notes=include_notes,
            max_results=max_results,
        )

        if result.success:
            return result.result
        else:
            return {
                "found": False,
                "error": result.error,
            }

    async def process_with_tools(
        self,
        query: str,
        db: AsyncSession,
        model: str = "gemini-2.5-flash",
        temperature: float = 0.7,
        max_iterations: int = 5,
    ) -> tuple[str, List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Process query using Gemini's native function calling.

        Args:
            query: User query
            db: Database session
            model: Gemini model to use
            temperature: Temperature for response generation
            max_iterations: Maximum function call iterations

        Returns:
            Tuple of (final answer, list of source citations, list of tool calls)
        """
        logger.info(f"Starting Gemini agent orchestration for query: {query[:50]}...")

        # Track all citations from knowledge searches
        all_citations: List[Dict[str, Any]] = []

        # Track all tool calls with their parameters and results
        all_tool_calls: List[Dict[str, Any]] = []

        # Create tools
        tools = self._create_function_declarations()

        # System prompt for agent behavior
        system_prompt = """You are a helpful AI assistant with access to the user's personal knowledge base.

You can use the knowledge_search function to search for information when needed. Use it when:
- The question requires specific facts from the user's documents or notes
- You need context about previous conversations or stored information
- The query asks about domain-specific knowledge

DO NOT use the function for:
- Simple math or logic questions you can answer directly
- General knowledge questions (e.g., "What is the capital of France?")
- Basic conversation or greetings

When you use the knowledge_search function:
1. READ and UNDERSTAND the content from the search results
2. SYNTHESIZE the information into a comprehensive, cohesive answer
3. DO NOT simply list the sources - integrate their information into your response
4. Provide inline citations using [source_title] format when referencing specific information
5. Your answer should be complete and informative, as if you've read and understood the documents

Example of GOOD synthesis:
"Quantum chemistry uses quantum mechanics principles to study molecular behavior. It's particularly valuable in drug discovery where it predicts molecular interactions [Quantum Chemistry Basics]. Recent advances combine quantum chemistry with machine learning to accelerate computational predictions by 10-100x [ML in Quantum Research]."

Example of BAD listing:
"I found these sources:
- Quantum Chemistry Basics: discusses quantum mechanics
- ML in Quantum Research: talks about machine learning applications"

Always synthesize, never just list."""

        # Create tools from function declarations
        tool = types.Tool(function_declarations=tools)

        # Start conversation history
        conversation_history = [
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=query)],
            )
        ]

        # Generate initial response with tools
        response = self.client.models.generate_content(
            model=model,
            contents=conversation_history,
            config=types.GenerateContentConfig(
                temperature=temperature,
                system_instruction=system_prompt,
                tools=[tool],
            ),
        )

        # Handle function calls iteratively
        iteration = 0
        while iteration < max_iterations:
            iteration += 1

            # Check if we have function calls
            function_calls = response.function_calls if hasattr(response, "function_calls") else []
            text_response = response.text if hasattr(response, "text") and response.text else ""

            # If we have a text response and no function calls, we're done
            if text_response and not function_calls:
                logger.info(f"Final answer received after {iteration} iteration(s)")
                return text_response, all_citations, all_tool_calls

            # If no function calls and no text, something went wrong
            if not function_calls:
                logger.warning("No function calls or text in response")
                break

            # Execute function calls
            function_responses = []
            for function_call in function_calls:
                logger.info(f"Iteration {iteration}: Executing {function_call.name}")
                logger.debug(f"function_call.args type: {type(function_call.args)}")
                logger.debug(f"function_call.args content: {function_call.args}")

                if function_call.name == "knowledge_search":
                    # Extract arguments - now they're direct dict attributes
                    try:
                        search_query = dict(function_call.args).get("query", "")
                        include_notes = dict(function_call.args).get("include_notes", False)
                        max_results = dict(function_call.args).get("max_results", 10)
                    except Exception as e:
                        logger.error(f"Error extracting function arguments: {e}")
                        raise

                    # Track tool call (pending state)
                    tool_call_record = {
                        "tool": "knowledge_search",
                        "parameters": {
                            "query": search_query,
                            "include_notes": include_notes,
                            "max_results": max_results,
                        },
                        "status": "pending",
                    }

                    # Execute search
                    try:
                        search_result = await self._execute_knowledge_search(
                            db=db,
                            query=search_query,
                            include_notes=include_notes,
                            max_results=max_results,
                        )

                        # Update tool call with success
                        tool_call_record["status"] = "success"
                        tool_call_record["result"] = search_result

                        # Extract and store citations from search results
                        if search_result.get("found") and "sources" in search_result:
                            for source in search_result["sources"]:
                                # Convert to citation format expected by frontend
                                citation = {
                                    "source_type": source.get("type"),
                                    "source_id": source.get("id"),
                                    "source_title": source.get("title"),
                                }
                                all_citations.append(citation)

                    except Exception as e:
                        # Update tool call with error
                        tool_call_record["status"] = "error"
                        tool_call_record["error"] = str(e)
                        search_result = {
                            "found": False,
                            "error": str(e),
                        }

                    # Store tool call record
                    all_tool_calls.append(tool_call_record)

                    # Build function response part
                    function_response_part = types.Part.from_function_response(
                        name="knowledge_search",
                        response={"result": search_result},
                    )
                    function_responses.append(function_response_part)

            # Send function results back to model
            if function_responses:
                # Add the model's function call to conversation history
                conversation_history.append(response.candidates[0].content)

                # Add function responses to conversation history
                function_response_content = types.Content(
                    role="tool",
                    parts=function_responses,
                )
                conversation_history.append(function_response_content)

                # Generate next response
                response = self.client.models.generate_content(
                    model=model,
                    contents=conversation_history,
                    config=types.GenerateContentConfig(
                        temperature=temperature,
                        system_instruction=system_prompt,
                        tools=[tool],
                    ),
                )
            else:
                break

        # If we exhausted iterations, return best effort response
        logger.warning(f"Max iterations ({max_iterations}) reached")

        # Try to extract text from the last response
        final_text = response.text if hasattr(response, "text") and response.text else ""

        if final_text:
            return final_text, all_citations, all_tool_calls
        else:
            return (
                "I apologize, but I wasn't able to complete the task within the allowed iterations.",
                all_citations,
                all_tool_calls,
            )

    async def process_with_tools_stream(
        self,
        query: str,
        db: AsyncSession,
        model: str = "gemini-2.5-flash",
        temperature: float = 0.7,
        max_iterations: int = 5,
    ):
        """
        Process query using Gemini's native function calling with streaming.

        Yields status updates during tool execution and streams the final response.

        Args:
            query: User query
            db: Database session
            model: Gemini model to use
            temperature: Temperature for response generation
            max_iterations: Maximum function call iterations

        Yields:
            Dict with type ('status', 'tool_call', 'content', 'done') and data
        """
        logger.info(f"Starting streaming Gemini agent orchestration for query: {query[:50]}...")

        # Track all citations from knowledge searches
        all_citations: List[Dict[str, Any]] = []

        # Track all tool calls with their parameters and results
        all_tool_calls: List[Dict[str, Any]] = []

        # Create tools
        tools = self._create_function_declarations()

        # System prompt for agent behavior
        system_prompt = """You are a helpful AI assistant with access to the user's personal knowledge base.

You can use the knowledge_search function to search for information when needed. Use it when:
- The question requires specific facts from the user's documents or notes
- You need context about previous conversations or stored information
- The query asks about domain-specific knowledge

DO NOT use the function for:
- Simple math or logic questions you can answer directly
- General knowledge questions (e.g., "What is the capital of France?")
- Basic conversation or greetings

When you use the knowledge_search function:
1. READ and UNDERSTAND the content from the search results
2. SYNTHESIZE the information into a comprehensive, cohesive answer
3. DO NOT simply list the sources - integrate their information into your response
4. Provide inline citations using [source_title] format when referencing specific information
5. Your answer should be complete and informative, as if you've read and understood the documents

Example of GOOD synthesis:
"Quantum chemistry uses quantum mechanics principles to study molecular behavior. It's particularly valuable in drug discovery where it predicts molecular interactions [Quantum Chemistry Basics]. Recent advances combine quantum chemistry with machine learning to accelerate computational predictions by 10-100x [ML in Quantum Research]."

Example of BAD listing:
"I found these sources:
- Quantum Chemistry Basics: discusses quantum mechanics
- ML in Quantum Research: talks about machine learning applications"

Always synthesize, never just list."""

        # Create tools from function declarations
        tool = types.Tool(function_declarations=tools)

        # Start conversation history
        conversation_history = [
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=query)],
            )
        ]

        # Generate initial response with tools (non-streaming for function call detection)
        response = self.client.models.generate_content(
            model=model,
            contents=conversation_history,
            config=types.GenerateContentConfig(
                temperature=temperature,
                system_instruction=system_prompt,
                tools=[tool],
            ),
        )

        # Handle function calls iteratively
        iteration = 0
        while iteration < max_iterations:
            iteration += 1

            # Check if we have function calls
            function_calls = response.function_calls if hasattr(response, "function_calls") else []
            text_response = response.text if hasattr(response, "text") and response.text else ""

            # If we have a text response and no function calls, we're ready to stream the final answer
            if text_response and not function_calls:
                logger.info(
                    f"Final answer received after {iteration} iteration(s), streaming response"
                )

                # Stream the response word by word for better UX
                words = text_response.split()
                for i, word in enumerate(words):
                    # Add space before word (except first word)
                    chunk = f" {word}" if i > 0 else word
                    yield {"type": "content", "content": chunk}

                # Send completion with metadata
                yield {"type": "done", "citations": all_citations, "tool_calls": all_tool_calls}
                return

            # If no function calls and no text, something went wrong
            if not function_calls:
                logger.warning("No function calls or text in response")
                break

            # Execute function calls
            function_responses = []
            for function_call in function_calls:
                logger.info(f"Iteration {iteration}: Executing {function_call.name}")

                # Emit status update
                yield {"type": "status", "status": f"Searching knowledge base..."}

                if function_call.name == "knowledge_search":
                    # Extract arguments - now they're direct dict attributes
                    try:
                        search_query = dict(function_call.args).get("query", "")
                        include_notes = dict(function_call.args).get("include_notes", False)
                        max_results = dict(function_call.args).get("max_results", 10)
                    except Exception as e:
                        logger.error(f"Error extracting function arguments: {e}")
                        raise

                    # Track tool call (pending state)
                    tool_call_record = {
                        "tool": "knowledge_search",
                        "parameters": {
                            "query": search_query,
                            "include_notes": include_notes,
                            "max_results": max_results,
                        },
                        "status": "pending",
                    }

                    # Emit tool call event
                    yield {"type": "tool_call", "tool_call": tool_call_record}

                    # Execute search
                    try:
                        search_result = await self._execute_knowledge_search(
                            db=db,
                            query=search_query,
                            include_notes=include_notes,
                            max_results=max_results,
                        )

                        # Update tool call with success
                        tool_call_record["status"] = "success"
                        tool_call_record["result"] = search_result

                        # Emit tool call completion
                        yield {"type": "tool_call_complete", "tool_call": tool_call_record}

                        # Extract and store citations from search results
                        if search_result.get("found") and "sources" in search_result:
                            num_sources = len(search_result["sources"])
                            yield {
                                "type": "status",
                                "status": f"Found {num_sources} relevant source{'s' if num_sources != 1 else ''}...",
                            }

                            for source in search_result["sources"]:
                                citation = {
                                    "source_type": source.get("type"),
                                    "source_id": source.get("id"),
                                    "source_title": source.get("title"),
                                }
                                all_citations.append(citation)

                    except Exception as e:
                        # Update tool call with error
                        tool_call_record["status"] = "error"
                        tool_call_record["error"] = str(e)
                        search_result = {
                            "found": False,
                            "error": str(e),
                        }

                        # Emit error
                        yield {"type": "tool_call_error", "tool_call": tool_call_record}

                    # Store tool call record
                    all_tool_calls.append(tool_call_record)

                    # Build function response part
                    function_response_part = types.Part.from_function_response(
                        name="knowledge_search",
                        response={"result": search_result},
                    )
                    function_responses.append(function_response_part)

            # Send function results back to model
            if function_responses:
                # Add the model's function call to conversation history
                conversation_history.append(response.candidates[0].content)

                # Add function responses to conversation history
                function_response_content = types.Content(
                    role="tool",
                    parts=function_responses,
                )
                conversation_history.append(function_response_content)

                # Emit status update
                yield {"type": "status", "status": "Generating answer..."}

                # Generate next response (non-streaming for function call detection)
                response = self.client.models.generate_content(
                    model=model,
                    contents=conversation_history,
                    config=types.GenerateContentConfig(
                        temperature=temperature,
                        system_instruction=system_prompt,
                        tools=[tool],
                    ),
                )
            else:
                break

        # If we exhausted iterations, emit error
        logger.warning(f"Max iterations ({max_iterations}) reached")
        yield {
            "type": "content",
            "content": "I apologize, but I wasn't able to complete the task within the allowed iterations.",
        }
        yield {"type": "done", "citations": all_citations, "tool_calls": all_tool_calls}


# Singleton instance
_gemini_agent_orchestrator: Optional[GeminiAgentOrchestrator] = None


def get_gemini_agent_orchestrator() -> GeminiAgentOrchestrator:
    """Get or create the Gemini agent orchestrator singleton."""
    global _gemini_agent_orchestrator
    if _gemini_agent_orchestrator is None:
        _gemini_agent_orchestrator = GeminiAgentOrchestrator()
    return _gemini_agent_orchestrator
