"""
Unit tests for tool executor.
"""
import pytest
from typing import List
from unittest.mock import patch, Mock

from app.services.tool_executor import ToolExecutor
from app.services.tool_registry import ToolRegistry
from app.services.tools.base import BaseTool, ToolParameter, ToolResult


class SuccessTool(BaseTool):
    """Tool that always succeeds."""

    @property
    def name(self) -> str:
        return "success_tool"

    @property
    def description(self) -> str:
        return "A tool that succeeds"

    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(name="input", type="string", description="Input value", required=True)
        ]

    async def execute(self, **kwargs) -> ToolResult:
        return ToolResult(success=True, result=f"Success: {kwargs.get('input')}")


class FailureTool(BaseTool):
    """Tool that always fails."""

    @property
    def name(self) -> str:
        return "failure_tool"

    @property
    def description(self) -> str:
        return "A tool that fails"

    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(name="input", type="string", description="Input value", required=True)
        ]

    async def execute(self, **kwargs) -> ToolResult:
        return ToolResult(success=False, result=None, error="Tool failed")


class ErrorTool(BaseTool):
    """Tool that raises an error."""

    @property
    def name(self) -> str:
        return "error_tool"

    @property
    def description(self) -> str:
        return "A tool that raises errors"

    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(name="input", type="string", description="Input value", required=True)
        ]

    async def execute(self, **kwargs) -> ToolResult:
        raise RuntimeError("Execution error")


class TestToolExecutor:
    """Test suite for ToolExecutor."""

    @pytest.fixture
    def registry(self):
        """Create a fresh registry with test tools."""
        reg = ToolRegistry()
        reg.register(SuccessTool, access_level="all")
        reg.register(FailureTool, access_level="restricted")
        reg.register(ErrorTool, access_level="all")
        return reg

    @pytest.fixture
    def executor(self, registry):
        """Create executor with test registry."""
        executor = ToolExecutor()
        executor.registry = registry
        return executor

    @pytest.mark.asyncio
    async def test_execute_success(self, executor):
        """Test successful tool execution."""
        result = await executor.execute(
            tool_name="success_tool",
            parameters={"input": "test"},
            agent_access_list=None,  # Full access
        )

        assert result.success is True
        assert "Success: test" in result.result
        assert result.error is None

    @pytest.mark.asyncio
    async def test_execute_tool_not_found(self, executor):
        """Test execution with non-existent tool."""
        result = await executor.execute(
            tool_name="nonexistent_tool",
            parameters={},
            agent_access_list=None,
        )

        assert result.success is False
        assert "not found" in result.error

    @pytest.mark.asyncio
    async def test_execute_not_authorized(self, executor):
        """Test execution with unauthorized tool."""
        # failure_tool is restricted, agent has no access
        result = await executor.execute(
            tool_name="failure_tool",
            parameters={"input": "test"},
            agent_access_list=["success_tool"],  # Only success_tool allowed
        )

        assert result.success is False
        assert "not authorized" in result.error

    @pytest.mark.asyncio
    async def test_execute_invalid_parameters(self, executor):
        """Test execution with invalid parameters."""
        # Missing required parameter
        result = await executor.execute(
            tool_name="success_tool",
            parameters={},  # Missing 'input'
            agent_access_list=None,
        )

        assert result.success is False
        assert "Invalid parameters" in result.error

    @pytest.mark.asyncio
    async def test_execute_unexpected_parameters(self, executor):
        """Test execution with unexpected parameters."""
        result = await executor.execute(
            tool_name="success_tool",
            parameters={"input": "test", "unexpected": "param"},
            agent_access_list=None,
        )

        assert result.success is False
        assert "Invalid parameters" in result.error

    @pytest.mark.asyncio
    async def test_execute_tool_failure(self, executor):
        """Test execution of tool that returns failure."""
        # failure_tool is restricted, give full access
        result = await executor.execute(
            tool_name="failure_tool",
            parameters={"input": "test"},
            agent_access_list=None,  # Full access
        )

        assert result.success is False
        assert result.error == "Tool failed"

    @pytest.mark.asyncio
    async def test_execute_tool_error(self, executor):
        """Test execution of tool that raises error."""
        result = await executor.execute(
            tool_name="error_tool",
            parameters={"input": "test"},
            agent_access_list=None,
        )

        assert result.success is False
        assert "error" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_batch(self, executor):
        """Test batch execution."""
        tool_calls = [
            {"tool": "success_tool", "parameters": {"input": "test1"}},
            {"tool": "success_tool", "parameters": {"input": "test2"}},
        ]

        results = await executor.execute_batch(tool_calls, agent_access_list=None)

        assert len(results) == 2
        assert results[0].success is True
        assert results[1].success is True
        assert "test1" in results[0].result
        assert "test2" in results[1].result

    @pytest.mark.asyncio
    async def test_execute_batch_with_failures(self, executor):
        """Test batch execution with some failures."""
        tool_calls = [
            {"tool": "success_tool", "parameters": {"input": "test"}},
            {"tool": "nonexistent_tool", "parameters": {}},
            {"tool": "error_tool", "parameters": {"input": "test"}},
        ]

        results = await executor.execute_batch(tool_calls, agent_access_list=None)

        assert len(results) == 3
        assert results[0].success is True
        assert results[1].success is False  # Not found
        assert results[2].success is False  # Error

    @pytest.mark.asyncio
    async def test_execute_batch_missing_tool_field(self, executor):
        """Test batch execution with missing tool field."""
        tool_calls = [
            {"parameters": {"input": "test"}},  # Missing 'tool' field
        ]

        results = await executor.execute_batch(tool_calls, agent_access_list=None)

        assert len(results) == 1
        assert results[0].success is False
        assert "Missing 'tool' field" in results[0].error

    def test_validate_tool_call_success(self, executor):
        """Test successful tool call validation."""
        is_valid, error = executor.validate_tool_call(
            tool_name="success_tool",
            parameters={"input": "test"},
            agent_access_list=None,
        )

        assert is_valid is True
        assert error is None

    def test_validate_tool_call_not_found(self, executor):
        """Test validation with non-existent tool."""
        is_valid, error = executor.validate_tool_call(
            tool_name="nonexistent_tool",
            parameters={},
            agent_access_list=None,
        )

        assert is_valid is False
        assert "not found" in error

    def test_validate_tool_call_not_authorized(self, executor):
        """Test validation with unauthorized tool."""
        is_valid, error = executor.validate_tool_call(
            tool_name="failure_tool",
            parameters={"input": "test"},
            agent_access_list=["success_tool"],  # Only success_tool allowed
        )

        assert is_valid is False
        assert "not authorized" in error

    def test_validate_tool_call_invalid_parameters(self, executor):
        """Test validation with invalid parameters."""
        is_valid, error = executor.validate_tool_call(
            tool_name="success_tool",
            parameters={},  # Missing required 'input'
            agent_access_list=None,
        )

        assert is_valid is False
        assert "Invalid parameters" in error

    def test_get_available_tools_info(self, executor):
        """Test getting available tools info."""
        # Full access
        tools_info = executor.get_available_tools_info(agent_access_list=None)

        assert len(tools_info) == 3
        tool_names = [t["name"] for t in tools_info]
        assert "success_tool" in tool_names
        assert "failure_tool" in tool_names
        assert "error_tool" in tool_names

    def test_get_available_tools_info_restricted(self, executor):
        """Test getting available tools info with restricted access."""
        # Only success_tool allowed
        tools_info = executor.get_available_tools_info(agent_access_list=["success_tool"])

        assert len(tools_info) == 1
        assert tools_info[0]["name"] == "success_tool"

    def test_get_available_tools_info_no_access(self, executor):
        """Test getting available tools info with no access."""
        tools_info = executor.get_available_tools_info(agent_access_list=[])

        assert len(tools_info) == 0
