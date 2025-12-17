"""
Tool orchestrator for multi-step reasoning with tools.

Manages the agent reasoning loop: LLM calls, tool execution, and iteration
until a final answer is reached.
"""
import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.agent_service import AgentConfig
from app.services.llm_service import get_llm_service
from app.services.tool_call_parser import get_tool_call_parser, ParsedResponse, ToolCall
from app.services.tool_executor import get_tool_executor
from app.services.tools.document_search_tool import DocumentSearchTool

logger = logging.getLogger(__name__)


class ToolOrchestrator:
    """
    Orchestrator for multi-step tool-using agent reasoning.

    Manages the loop:
    1. Build prompt with tool definitions and history
    2. Call LLM to get tool calls or final answer
    3. Execute tool calls and collect results
    4. Repeat until final answer or max iterations
    """

    def __init__(self):
        """Initialize the tool orchestrator."""
        self.llm_service = get_llm_service()
        self.tool_executor = get_tool_executor()
        self.tool_parser = get_tool_call_parser()

    async def process_with_tools(
        self,
        query: str,
        agent_config: AgentConfig,
        db: Optional[AsyncSession] = None,
        max_iterations: int = 5,
        on_tool_call: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_tool_result: Optional[Callable[[str, Dict[str, Any]], None]] = None,
        on_iteration: Optional[Callable[[int, str], None]] = None,
    ) -> str:
        """
        Process a query with multi-step tool reasoning.

        Args:
            query: User's query
            agent_config: Agent configuration
            db: Database session (for document_search tool)
            max_iterations: Maximum reasoning iterations
            on_tool_call: Callback for tool call events
            on_tool_result: Callback for tool result events
            on_iteration: Callback for iteration start events

        Returns:
            Final answer string
        """
        tool_history: List[Dict[str, Any]] = []
        iteration = 0

        # Get available tools for this agent
        tools_info = self.tool_executor.get_available_tools_info(
            agent_access_list=agent_config.tool_access_list
        )

        logger.info(
            f"Starting tool orchestration for query: {query[:100]}... "
            f"(max_iterations={max_iterations}, available_tools={len(tools_info)})"
        )

        # Main reasoning loop
        for iteration in range(max_iterations):
            logger.info(f"Tool orchestration iteration {iteration + 1}/{max_iterations}")

            if on_iteration:
                on_iteration(iteration + 1, f"Thinking (iteration {iteration + 1}/{max_iterations})...")

            # Build prompt with tool definitions and history
            prompt = self.tool_parser.build_tool_prompt(
                query=query,
                tools_info=tools_info,
                tool_history=tool_history,
            )

            # Call LLM
            try:
                llm_response = await self.llm_service._generate_response(
                    model=agent_config.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=agent_config.temperature,
                )
            except Exception as e:
                logger.error(f"LLM call failed: {e}")
                return f"I encountered an error while processing your request: {str(e)}"

            # Parse response
            parsed = self.tool_parser.parse(llm_response)

            logger.info(
                f"LLM response parsed: {len(parsed.tool_calls)} tool calls, "
                f"final_answer={'Yes' if parsed.final_answer else 'No'}"
            )

            # Check if we have a final answer
            if parsed.final_answer:
                logger.info("Final answer received from LLM")
                return parsed.final_answer

            # Check if we have tool calls
            if not parsed.tool_calls:
                # No tool calls and no final answer - LLM might be confused
                if iteration == max_iterations - 1:
                    # Last iteration, synthesize answer from history
                    logger.warning("No tool calls or final answer on last iteration")
                    return self._synthesize_final_answer(query, tool_history)
                else:
                    # Ask LLM to provide final answer
                    logger.warning("No tool calls or final answer, prompting for final answer")
                    continue

            # Execute tool calls
            for tool_call in parsed.tool_calls:
                await self._execute_tool_call(
                    tool_call=tool_call,
                    tool_history=tool_history,
                    agent_config=agent_config,
                    db=db,
                    on_tool_call=on_tool_call,
                    on_tool_result=on_tool_result,
                )

        # Max iterations reached - synthesize final answer
        logger.info(f"Max iterations ({max_iterations}) reached, synthesizing answer")
        return self._synthesize_final_answer(query, tool_history)

    async def _execute_tool_call(
        self,
        tool_call: ToolCall,
        tool_history: List[Dict[str, Any]],
        agent_config: AgentConfig,
        db: Optional[AsyncSession],
        on_tool_call: Optional[Callable[[Dict[str, Any]], None]],
        on_tool_result: Optional[Callable[[str, Dict[str, Any]], None]],
    ) -> None:
        """
        Execute a single tool call and update history.

        Args:
            tool_call: Tool call to execute
            tool_history: History list to update
            agent_config: Agent configuration
            db: Database session
            on_tool_call: Callback for tool call event
            on_tool_result: Callback for tool result event
        """
        # Emit tool call event
        if on_tool_call:
            on_tool_call({
                "tool": tool_call.tool,
                "parameters": tool_call.parameters,
                "thought": tool_call.thought,
            })

        # Special handling for document_search tool (needs DB session)
        if tool_call.tool == "document_search" and db is not None:
            tool = self.tool_executor.registry.get_tool("document_search")
            if isinstance(tool, DocumentSearchTool):
                tool.set_db_session(db)

        # Execute tool
        result = await self.tool_executor.execute(
            tool_name=tool_call.tool,
            parameters=tool_call.parameters,
            agent_access_list=agent_config.tool_access_list,
        )

        # Emit tool result event
        if on_tool_result:
            on_tool_result(tool_call.tool, result.to_dict())

        # Add to history
        tool_history.append({
            "tool": tool_call.tool,
            "parameters": tool_call.parameters,
            "thought": tool_call.thought,
            "result": result.to_dict(),
        })

        logger.info(
            f"Tool {tool_call.tool} executed: success={result.success}, "
            f"history_length={len(tool_history)}"
        )

    def _synthesize_final_answer(
        self,
        query: str,
        tool_history: List[Dict[str, Any]],
    ) -> str:
        """
        Synthesize a final answer from tool history when max iterations reached.

        Args:
            query: Original query
            tool_history: History of tool calls and results

        Returns:
            Synthesized final answer
        """
        if not tool_history:
            return (
                "I apologize, but I wasn't able to find an answer to your question. "
                "Please try rephrasing your query or providing more details."
            )

        # Build summary of what we found
        summary_parts = [
            f"Based on my investigation of your question: '{query}'\n",
            "\nHere's what I found:\n"
        ]

        for i, entry in enumerate(tool_history, 1):
            tool_name = entry["tool"]
            result = entry["result"]

            if result.get("success"):
                summary_parts.append(f"\n{i}. Using {tool_name}:")

                # Extract relevant information based on tool type
                if tool_name == "web_search":
                    results = result.get("result", {}).get("results", [])
                    if results:
                        summary_parts.append(f"   Found {len(results)} relevant web results")
                        for r in results[:2]:  # Show top 2
                            summary_parts.append(f"   - {r.get('title', 'N/A')}")

                elif tool_name == "calculator":
                    expr = result.get("result", {}).get("expression")
                    calc_result = result.get("result", {}).get("result")
                    summary_parts.append(f"   {expr} = {calc_result}")

                elif tool_name == "code_executor":
                    stdout = result.get("result", {}).get("stdout", "").strip()
                    if stdout:
                        summary_parts.append(f"   Output: {stdout[:200]}")

                elif tool_name == "document_search":
                    count = result.get("result", {}).get("results_count", 0)
                    summary_parts.append(f"   Found {count} relevant passages in your documents")
            else:
                error = result.get("error", "Unknown error")
                summary_parts.append(f"\n{i}. {tool_name} failed: {error}")

        summary_parts.append(
            "\n\nI've gathered this information but need more iterations to provide a complete answer. "
            "You may want to ask a more specific question or try again."
        )

        return "".join(summary_parts)


# Global orchestrator instance
_tool_orchestrator: Optional[ToolOrchestrator] = None


def get_tool_orchestrator() -> ToolOrchestrator:
    """
    Get the global tool orchestrator instance.

    Returns:
        Tool orchestrator singleton
    """
    global _tool_orchestrator
    if _tool_orchestrator is None:
        _tool_orchestrator = ToolOrchestrator()
    return _tool_orchestrator
