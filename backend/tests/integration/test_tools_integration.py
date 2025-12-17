"""
Integration tests for tool system.
"""
import pytest

from app.services.tool_registry import get_tool_registry
from app.services.tool_executor import get_tool_executor


@pytest.mark.asyncio
async def test_tool_registry_has_all_tools():
    """Test that all 4 core tools are registered."""
    registry = get_tool_registry()
    tools = registry.list_tools()

    assert "web_search" in tools
    assert "calculator" in tools
    assert "code_executor" in tools
    assert "document_search" in tools
    assert len(tools) == 4


@pytest.mark.asyncio
async def test_calculator_tool_basic():
    """Test calculator tool with basic arithmetic."""
    executor = get_tool_executor()

    result = await executor.execute(
        tool_name="calculator",
        parameters={"expression": "2 + 2"},
        agent_access_list=None,
    )

    assert result.success is True
    assert result.result["result"] == 4
    assert result.result["expression"] == "2 + 2"


@pytest.mark.asyncio
async def test_calculator_tool_complex():
    """Test calculator with complex expression."""
    executor = get_tool_executor()

    result = await executor.execute(
        tool_name="calculator",
        parameters={"expression": "10 * 5 + 3 - 2 ** 2"},
        agent_access_list=None,
    )

    assert result.success is True
    # 10 * 5 + 3 - 2^2 = 50 + 3 - 4 = 49
    assert result.result["result"] == 49


@pytest.mark.asyncio
async def test_calculator_division_by_zero():
    """Test calculator handles division by zero."""
    executor = get_tool_executor()

    result = await executor.execute(
        tool_name="calculator",
        parameters={"expression": "1 / 0"},
        agent_access_list=None,
    )

    assert result.success is False
    assert "division by zero" in result.error.lower()


@pytest.mark.asyncio
async def test_code_executor_simple():
    """Test code executor with simple print."""
    executor = get_tool_executor()

    result = await executor.execute(
        tool_name="code_executor",
        parameters={"code": "print('Hello, World!')"},
        agent_access_list=None,
    )

    assert result.success is True
    assert "Hello, World!" in result.result["stdout"]
    assert result.result["return_code"] == 0


@pytest.mark.asyncio
async def test_code_executor_calculation():
    """Test code executor with calculation."""
    executor = get_tool_executor()

    result = await executor.execute(
        tool_name="code_executor",
        parameters={"code": "result = 2 + 2\nprint(result)"},
        agent_access_list=None,
    )

    assert result.success is True
    assert "4" in result.result["stdout"]


@pytest.mark.asyncio
async def test_code_executor_restricted_import():
    """Test code executor blocks restricted imports."""
    executor = get_tool_executor()

    result = await executor.execute(
        tool_name="code_executor",
        parameters={"code": "import os\nprint(os.listdir())"},
        agent_access_list=None,
    )

    assert result.success is False
    assert "restricted" in result.error.lower()


@pytest.mark.asyncio
async def test_tool_access_control():
    """Test that access control works."""
    executor = get_tool_executor()

    # With access list that doesn't include calculator
    result = await executor.execute(
        tool_name="calculator",
        parameters={"expression": "2 + 2"},
        agent_access_list=["web_search"],  # Only web_search allowed
    )

    assert result.success is False
    assert "not authorized" in result.error


@pytest.mark.asyncio
async def test_tool_batch_execution():
    """Test batch tool execution."""
    executor = get_tool_executor()

    tool_calls = [
        {"tool": "calculator", "parameters": {"expression": "2 + 2"}},
        {"tool": "calculator", "parameters": {"expression": "10 * 5"}},
    ]

    results = await executor.execute_batch(tool_calls, agent_access_list=None)

    assert len(results) == 2
    assert results[0].success is True
    assert results[0].result["result"] == 4
    assert results[1].success is True
    assert results[1].result["result"] == 50


@pytest.mark.asyncio
async def test_get_tools_info():
    """Test getting tools information."""
    executor = get_tool_executor()

    tools_info = executor.get_available_tools_info(agent_access_list=None)

    assert len(tools_info) == 4
    tool_names = [t["name"] for t in tools_info]
    assert "calculator" in tool_names
    assert "code_executor" in tool_names
    assert "web_search" in tool_names
    assert "document_search" in tool_names

    # Check that each tool has proper schema
    for tool_info in tools_info:
        assert "name" in tool_info
        assert "description" in tool_info
        assert "parameters" in tool_info
