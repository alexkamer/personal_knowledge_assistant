"""
End-to-end tests for tool orchestrator integration.
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch

from app.services.agent_service import get_agent_service
from app.services.tool_orchestrator import get_tool_orchestrator


@pytest.mark.asyncio
async def test_orchestrator_with_calculator_single_step():
    """Test orchestrator with simple calculator query (single step)."""
    agent_service = get_agent_service()
    agent_config = agent_service.get_agent("deep")

    # Mock LLM to return a calculator tool call, then final answer
    with patch('app.services.tool_orchestrator.get_llm_service') as mock_llm_service:
        mock_llm = Mock()
        mock_llm_service.return_value = mock_llm

        # First call: LLM decides to use calculator
        # Second call: LLM provides final answer
        mock_llm._generate_response = AsyncMock(side_effect=[
            # Iteration 1: Use calculator
            '{"thought": "I need to calculate this", "tool_calls": [{"tool": "calculator", "parameters": {"expression": "2 + 2"}}]}',
            # Iteration 2: Final answer
            '{"thought": "I have the result", "final_answer": "The answer is 4."}',
        ])

        orchestrator = get_tool_orchestrator()
        result = await orchestrator.process_with_tools(
            query="What is 2 + 2?",
            agent_config=agent_config,
            max_iterations=5,
        )

        # Verify we got a final answer
        assert "4" in result or "four" in result.lower()
        assert mock_llm._generate_response.call_count == 2


@pytest.mark.asyncio
async def test_orchestrator_with_multiple_tool_calls():
    """Test orchestrator with multiple tool calls in sequence."""
    agent_service = get_agent_service()
    agent_config = agent_service.get_agent("deep")

    tool_calls_captured = []
    tool_results_captured = []

    def on_tool_call(tool_call_data):
        tool_calls_captured.append(tool_call_data)

    def on_tool_result(tool_name, result_data):
        tool_results_captured.append((tool_name, result_data))

    with patch('app.services.tool_orchestrator.get_llm_service') as mock_llm_service:
        mock_llm = Mock()
        mock_llm_service.return_value = mock_llm

        mock_llm._generate_response = AsyncMock(side_effect=[
            # Iteration 1: Calculate first
            '{"thought": "First calculate", "tool_calls": [{"tool": "calculator", "parameters": {"expression": "10 * 5"}}]}',
            # Iteration 2: Calculate again
            '{"thought": "Now add 3", "tool_calls": [{"tool": "calculator", "parameters": {"expression": "50 + 3"}}]}',
            # Iteration 3: Final answer
            '{"final_answer": "The result is 53."}',
        ])

        orchestrator = get_tool_orchestrator()
        result = await orchestrator.process_with_tools(
            query="What is 10 times 5, plus 3?",
            agent_config=agent_config,
            max_iterations=5,
            on_tool_call=on_tool_call,
            on_tool_result=on_tool_result,
        )

        # Verify final answer
        assert "53" in result

        # Verify tool calls were captured
        assert len(tool_calls_captured) == 2
        assert tool_calls_captured[0]["tool"] == "calculator"
        assert tool_calls_captured[1]["tool"] == "calculator"

        # Verify tool results were captured
        assert len(tool_results_captured) == 2
        assert tool_results_captured[0][0] == "calculator"
        assert tool_results_captured[1][0] == "calculator"


@pytest.mark.asyncio
async def test_orchestrator_max_iterations_reached():
    """Test orchestrator when max iterations is reached without final answer."""
    agent_service = get_agent_service()
    agent_config = agent_service.get_agent("deep")

    with patch('app.services.tool_orchestrator.get_llm_service') as mock_llm_service:
        mock_llm = Mock()
        mock_llm_service.return_value = mock_llm

        # LLM keeps calling tools without providing final answer
        mock_llm._generate_response = AsyncMock(return_value=(
            '{"thought": "I need more info", "tool_calls": [{"tool": "calculator", "parameters": {"expression": "1 + 1"}}]}'
        ))

        orchestrator = get_tool_orchestrator()
        result = await orchestrator.process_with_tools(
            query="Test query",
            agent_config=agent_config,
            max_iterations=3,  # Low limit
        )

        # Should synthesize an answer
        assert len(result) > 0
        assert "calculator" in result.lower() or "iteration" in result.lower() or "information" in result.lower()


@pytest.mark.asyncio
async def test_orchestrator_handles_tool_failure():
    """Test orchestrator handles tool execution failures gracefully."""
    agent_service = get_agent_service()
    agent_config = agent_service.get_agent("deep")

    with patch('app.services.tool_orchestrator.get_llm_service') as mock_llm_service:
        mock_llm = Mock()
        mock_llm_service.return_value = mock_llm

        mock_llm._generate_response = AsyncMock(side_effect=[
            # Try to divide by zero
            '{"tool_calls": [{"tool": "calculator", "parameters": {"expression": "1 / 0"}}]}',
            # LLM provides final answer after seeing error
            '{"final_answer": "Cannot divide by zero."}',
        ])

        orchestrator = get_tool_orchestrator()
        result = await orchestrator.process_with_tools(
            query="What is 1 divided by 0?",
            agent_config=agent_config,
            max_iterations=5,
        )

        # Should handle the error and provide answer
        assert len(result) > 0
        assert mock_llm._generate_response.call_count == 2


@pytest.mark.asyncio
async def test_orchestrator_with_code_executor():
    """Test orchestrator with code executor tool."""
    agent_service = get_agent_service()
    agent_config = agent_service.get_agent("code")  # Code agent has code_executor

    with patch('app.services.tool_orchestrator.get_llm_service') as mock_llm_service:
        mock_llm = Mock()
        mock_llm_service.return_value = mock_llm

        mock_llm._generate_response = AsyncMock(side_effect=[
            # Execute Python code
            '{"tool_calls": [{"tool": "code_executor", "parameters": {"code": "print(\'Hello, World!\')"}}]}',
            # Final answer
            '{"final_answer": "The code prints Hello, World!"}',
        ])

        orchestrator = get_tool_orchestrator()
        result = await orchestrator.process_with_tools(
            query="Execute print('Hello, World!')",
            agent_config=agent_config,
            max_iterations=5,
        )

        assert "Hello" in result or "code" in result.lower()


@pytest.mark.asyncio
async def test_orchestrator_respects_tool_access_control():
    """Test that orchestrator respects agent tool access restrictions."""
    agent_service = get_agent_service()
    agent_config = agent_service.get_agent("code")  # Has limited tool access

    # Verify code agent only has specific tools
    assert agent_config.use_tools is True
    assert "code_executor" in agent_config.tool_access_list
    assert "calculator" not in agent_config.tool_access_list

    with patch('app.services.tool_orchestrator.get_llm_service') as mock_llm_service:
        mock_llm = Mock()
        mock_llm_service.return_value = mock_llm

        # LLM tries to use calculator (not allowed for code agent)
        mock_llm._generate_response = AsyncMock(side_effect=[
            '{"tool_calls": [{"tool": "calculator", "parameters": {"expression": "2 + 2"}}]}',
            '{"final_answer": "Tool not available."}',
        ])

        tool_results_captured = []

        def on_tool_result(tool_name, result_data):
            tool_results_captured.append((tool_name, result_data))

        orchestrator = get_tool_orchestrator()
        result = await orchestrator.process_with_tools(
            query="Calculate 2 + 2",
            agent_config=agent_config,
            max_iterations=5,
            on_tool_result=on_tool_result,
        )

        # Verify tool execution failed due to access control
        assert len(tool_results_captured) == 1
        assert tool_results_captured[0][1]["success"] is False
        assert "not authorized" in tool_results_captured[0][1].get("error", "").lower()


@pytest.mark.asyncio
async def test_orchestrator_parses_plain_text_response():
    """Test orchestrator handles plain text responses (no JSON)."""
    agent_service = get_agent_service()
    agent_config = agent_service.get_agent("deep")

    with patch('app.services.tool_orchestrator.get_llm_service') as mock_llm_service:
        mock_llm = Mock()
        mock_llm_service.return_value = mock_llm

        # LLM returns plain text instead of JSON
        mock_llm._generate_response = AsyncMock(return_value=(
            "I cannot help with that."
        ))

        orchestrator = get_tool_orchestrator()
        result = await orchestrator.process_with_tools(
            query="Test",
            agent_config=agent_config,
            max_iterations=5,
        )

        # Should treat plain text as final answer
        assert "cannot help" in result.lower()


@pytest.mark.asyncio
async def test_orchestrator_iteration_callbacks():
    """Test that iteration callbacks are invoked."""
    agent_service = get_agent_service()
    agent_config = agent_service.get_agent("deep")

    iterations_captured = []

    def on_iteration(iteration, status):
        iterations_captured.append((iteration, status))

    with patch('app.services.tool_orchestrator.get_llm_service') as mock_llm_service:
        mock_llm = Mock()
        mock_llm_service.return_value = mock_llm

        mock_llm._generate_response = AsyncMock(side_effect=[
            '{"tool_calls": [{"tool": "calculator", "parameters": {"expression": "1 + 1"}}]}',
            '{"final_answer": "The answer is 2."}',
        ])

        orchestrator = get_tool_orchestrator()
        await orchestrator.process_with_tools(
            query="What is 1 + 1?",
            agent_config=agent_config,
            max_iterations=5,
            on_iteration=on_iteration,
        )

        # Should have 2 iterations
        assert len(iterations_captured) == 2
        assert iterations_captured[0][0] == 1
        assert iterations_captured[1][0] == 2
        assert "iteration" in iterations_captured[0][1].lower()


@pytest.mark.asyncio
async def test_agent_configs_have_correct_tool_settings():
    """Test that agent configurations have correct tool settings."""
    agent_service = get_agent_service()

    # Quick agent: no tools
    quick = agent_service.get_agent("quick")
    assert quick.use_tools is False
    assert quick.tool_access_list == []

    # Deep agent: all tools
    deep = agent_service.get_agent("deep")
    assert deep.use_tools is True
    assert deep.tool_access_list is None  # None = all tools
    assert deep.max_tool_iterations == 10

    # Code agent: specific tools
    code = agent_service.get_agent("code")
    assert code.use_tools is True
    assert "code_executor" in code.tool_access_list
    assert "web_search" in code.tool_access_list
    assert "document_search" in code.tool_access_list
    assert code.max_tool_iterations == 7

    # Summarize agent: no tools
    summarize = agent_service.get_agent("summarize")
    assert summarize.use_tools is False
    assert summarize.tool_access_list == []

    # Default agent: no tools (backwards compatibility)
    default = agent_service.get_agent(None)
    assert default.use_tools is False
