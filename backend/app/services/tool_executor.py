"""
Tool executor for validating and dispatching tool calls.

Handles parameter validation, execution, error handling, and result formatting.
"""
import logging
from typing import Any, Dict, List, Optional

from app.services.tool_registry import get_tool_registry
from app.services.tools.base import ToolResult

logger = logging.getLogger(__name__)


class ToolExecutor:
    """
    Executor for agent tools.

    Validates parameters, dispatches execution, and handles errors.
    """

    def __init__(self):
        """Initialize the tool executor."""
        self.registry = get_tool_registry()

    async def execute(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        agent_access_list: Optional[List[str]] = None,
    ) -> ToolResult:
        """
        Execute a tool with given parameters.

        Args:
            tool_name: Name of the tool to execute
            parameters: Tool parameters
            agent_access_list: Agent's tool access list for authorization

        Returns:
            ToolResult with execution outcome

        Raises:
            ValueError: If tool not found or not authorized
            RuntimeError: If execution fails critically
        """
        # Check if tool exists
        try:
            tool = self.registry.get_tool(tool_name)
        except ValueError as e:
            logger.error(f"Tool not found: {tool_name}")
            return ToolResult(
                success=False,
                result=None,
                error=f"Tool '{tool_name}' not found",
            )

        # Check access control
        if not self.registry.is_tool_available(tool_name, agent_access_list):
            logger.warning(
                f"Tool '{tool_name}' not authorized for agent (access_list={agent_access_list})"
            )
            return ToolResult(
                success=False,
                result=None,
                error=f"Tool '{tool_name}' not authorized for this agent",
            )

        # Validate parameters
        try:
            tool.validate_parameters(parameters)
        except ValueError as e:
            logger.error(f"Parameter validation failed for {tool_name}: {e}")
            return ToolResult(
                success=False,
                result=None,
                error=f"Invalid parameters: {str(e)}",
            )

        # Execute tool
        try:
            logger.info(f"Executing tool: {tool_name} with parameters: {parameters}")
            result = await tool.execute(**parameters)
            logger.info(f"Tool {tool_name} execution completed: success={result.success}")
            return result

        except ValueError as e:
            # Parameter errors (shouldn't happen after validation, but just in case)
            logger.error(f"Tool {tool_name} parameter error: {e}")
            return ToolResult(
                success=False,
                result=None,
                error=f"Parameter error: {str(e)}",
            )

        except RuntimeError as e:
            # Tool execution errors
            logger.error(f"Tool {tool_name} execution error: {e}")
            return ToolResult(
                success=False,
                result=None,
                error=f"Execution error: {str(e)}",
            )

        except Exception as e:
            # Unexpected errors
            logger.exception(f"Unexpected error executing tool {tool_name}: {e}")
            return ToolResult(
                success=False,
                result=None,
                error=f"Unexpected error: {str(e)}",
            )

    async def execute_batch(
        self,
        tool_calls: List[Dict[str, Any]],
        agent_access_list: Optional[List[str]] = None,
    ) -> List[ToolResult]:
        """
        Execute multiple tool calls.

        Args:
            tool_calls: List of tool calls with 'tool' and 'parameters' keys
            agent_access_list: Agent's tool access list for authorization

        Returns:
            List of ToolResults in same order as input

        Example:
            tool_calls = [
                {"tool": "web_search", "parameters": {"query": "AI news"}},
                {"tool": "calculator", "parameters": {"expression": "2 + 2"}},
            ]
        """
        results = []

        for tool_call in tool_calls:
            tool_name = tool_call.get("tool")
            parameters = tool_call.get("parameters", {})

            if not tool_name:
                logger.error("Tool call missing 'tool' field")
                results.append(
                    ToolResult(
                        success=False,
                        result=None,
                        error="Missing 'tool' field in tool call",
                    )
                )
                continue

            result = await self.execute(tool_name, parameters, agent_access_list)
            results.append(result)

        return results

    def validate_tool_call(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        agent_access_list: Optional[List[str]] = None,
    ) -> tuple[bool, Optional[str]]:
        """
        Validate a tool call without executing it.

        Args:
            tool_name: Name of the tool
            parameters: Tool parameters
            agent_access_list: Agent's tool access list

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check if tool exists
        try:
            tool = self.registry.get_tool(tool_name)
        except ValueError:
            return False, f"Tool '{tool_name}' not found"

        # Check access control
        if not self.registry.is_tool_available(tool_name, agent_access_list):
            return False, f"Tool '{tool_name}' not authorized"

        # Validate parameters
        try:
            tool.validate_parameters(parameters)
        except ValueError as e:
            return False, f"Invalid parameters: {str(e)}"

        return True, None

    def get_available_tools_info(
        self, agent_access_list: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get information about available tools for an agent.

        Args:
            agent_access_list: Agent's tool access list

        Returns:
            List of tool info dictionaries with name, description, and schema
        """
        available_tools = self.registry.get_available_tools(agent_access_list)
        tools_info = []

        for tool_name in available_tools:
            try:
                tool = self.registry.get_tool(tool_name)
                schema = tool.get_json_schema()
                tools_info.append(schema)
            except Exception as e:
                logger.error(f"Error getting info for tool {tool_name}: {e}")
                continue

        return tools_info


# Global executor instance
_tool_executor: Optional[ToolExecutor] = None


def get_tool_executor() -> ToolExecutor:
    """
    Get the global tool executor instance.

    Returns:
        Tool executor singleton
    """
    global _tool_executor
    if _tool_executor is None:
        _tool_executor = ToolExecutor()
    return _tool_executor
