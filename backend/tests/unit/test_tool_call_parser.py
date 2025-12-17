"""
Unit tests for tool call parser.
"""
import json
import pytest

from app.services.tool_call_parser import ToolCallParser, ToolCall, ParsedResponse


class TestToolCallParser:
    """Test suite for ToolCallParser."""

    @pytest.fixture
    def parser(self):
        """Create parser instance."""
        return ToolCallParser()

    def test_parse_pure_json_with_tool_calls(self, parser):
        """Test parsing pure JSON with tool calls."""
        response = json.dumps({
            "thought": "I need to search for information",
            "tool_calls": [
                {
                    "tool": "web_search",
                    "parameters": {"query": "AI news"},
                    "thought": "Searching for AI news"
                }
            ]
        })

        parsed = parser.parse(response)

        assert parsed.thought == "I need to search for information"
        assert len(parsed.tool_calls) == 1
        assert parsed.tool_calls[0].tool == "web_search"
        assert parsed.tool_calls[0].parameters["query"] == "AI news"
        assert parsed.tool_calls[0].thought == "Searching for AI news"
        assert parsed.final_answer is None

    def test_parse_pure_json_with_final_answer(self, parser):
        """Test parsing pure JSON with final answer."""
        response = json.dumps({
            "thought": "I have all the information I need",
            "final_answer": "The answer is 42"
        })

        parsed = parser.parse(response)

        assert parsed.thought == "I have all the information I need"
        assert parsed.final_answer == "The answer is 42"
        assert len(parsed.tool_calls) == 0

    def test_parse_json_in_markdown_code_block(self, parser):
        """Test parsing JSON in markdown code block."""
        response = """Here's my response:

```json
{
  "thought": "Let me calculate this",
  "tool_calls": [
    {
      "tool": "calculator",
      "parameters": {"expression": "2 + 2"}
    }
  ]
}
```

That should do it!"""

        parsed = parser.parse(response)

        assert parsed.thought == "Let me calculate this"
        assert len(parsed.tool_calls) == 1
        assert parsed.tool_calls[0].tool == "calculator"

    def test_parse_json_without_json_marker(self, parser):
        """Test parsing JSON in code block without 'json' marker."""
        response = """```
{
  "thought": "Searching",
  "tool_calls": [{"tool": "web_search", "parameters": {"query": "test"}}]
}
```"""

        parsed = parser.parse(response)

        assert parsed.thought == "Searching"
        assert len(parsed.tool_calls) == 1

    def test_parse_json_mixed_with_text(self, parser):
        """Test parsing JSON embedded in text."""
        response = """Let me think about this.

{"thought": "I'll use a tool", "tool_calls": [{"tool": "calculator", "parameters": {"expression": "5 * 5"}}]}

That's my plan."""

        parsed = parser.parse(response)

        assert parsed.thought == "I'll use a tool"
        assert len(parsed.tool_calls) == 1
        assert parsed.tool_calls[0].tool == "calculator"

    def test_parse_plain_text_as_final_answer(self, parser):
        """Test that plain text without JSON is treated as final answer."""
        response = "This is just a regular text response without any JSON."

        parsed = parser.parse(response)

        assert parsed.final_answer == response
        assert len(parsed.tool_calls) == 0

    def test_parse_empty_response(self, parser):
        """Test parsing empty response."""
        response = ""

        parsed = parser.parse(response)

        assert parsed.final_answer == "I apologize, but I couldn't generate a response."
        assert len(parsed.tool_calls) == 0

    def test_parse_multiple_tool_calls(self, parser):
        """Test parsing multiple tool calls."""
        response = json.dumps({
            "thought": "I need multiple tools",
            "tool_calls": [
                {"tool": "web_search", "parameters": {"query": "AI"}},
                {"tool": "calculator", "parameters": {"expression": "1 + 1"}},
                {"tool": "code_executor", "parameters": {"code": "print('hello')"}}
            ]
        })

        parsed = parser.parse(response)

        assert len(parsed.tool_calls) == 3
        assert parsed.tool_calls[0].tool == "web_search"
        assert parsed.tool_calls[1].tool == "calculator"
        assert parsed.tool_calls[2].tool == "code_executor"

    def test_parse_tool_call_without_parameters(self, parser):
        """Test parsing tool call with no parameters."""
        response = json.dumps({
            "tool_calls": [{"tool": "list_files"}]
        })

        parsed = parser.parse(response)

        assert len(parsed.tool_calls) == 1
        assert parsed.tool_calls[0].tool == "list_files"
        assert parsed.tool_calls[0].parameters == {}

    def test_parse_invalid_tool_call_no_tool_field(self, parser):
        """Test parsing invalid tool call missing 'tool' field."""
        response = json.dumps({
            "tool_calls": [{"parameters": {"query": "test"}}]  # Missing 'tool'
        })

        parsed = parser.parse(response)

        # Should skip invalid tool call
        assert len(parsed.tool_calls) == 0

    def test_parse_invalid_tool_call_format(self, parser):
        """Test parsing invalid tool call (not a dict)."""
        response = json.dumps({
            "tool_calls": ["invalid", "format"]  # Should be list of dicts
        })

        parsed = parser.parse(response)

        # Should skip invalid tool calls
        assert len(parsed.tool_calls) == 0

    def test_format_tool_definitions_empty(self, parser):
        """Test formatting empty tool list."""
        formatted = parser.format_tool_definitions([])

        assert "No tools available" in formatted

    def test_format_tool_definitions_single_tool(self, parser):
        """Test formatting single tool definition."""
        tools_info = [
            {
                "name": "web_search",
                "description": "Search the web",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query"
                        }
                    },
                    "required": ["query"]
                }
            }
        ]

        formatted = parser.format_tool_definitions(tools_info)

        assert "web_search" in formatted
        assert "Search the web" in formatted
        assert "query" in formatted
        assert "required" in formatted

    def test_format_tool_definitions_with_enum(self, parser):
        """Test formatting tool with enum parameter."""
        tools_info = [
            {
                "name": "test_tool",
                "description": "A test tool",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "mode": {
                            "type": "string",
                            "description": "Operation mode",
                            "enum": ["fast", "slow", "medium"]
                        }
                    },
                    "required": []
                }
            }
        ]

        formatted = parser.format_tool_definitions(tools_info)

        assert "mode" in formatted
        assert "optional" in formatted
        assert "fast, slow, medium" in formatted

    def test_build_tool_prompt_no_history(self, parser):
        """Test building prompt without tool history."""
        query = "What is 2 + 2?"
        tools_info = [
            {
                "name": "calculator",
                "description": "Perform calculations",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {"type": "string", "description": "Math expression"}
                    },
                    "required": ["expression"]
                }
            }
        ]

        prompt = parser.build_tool_prompt(query, tools_info, [])

        assert "calculator" in prompt
        assert "What is 2 + 2?" in prompt
        assert "tool_calls" in prompt
        assert "final_answer" in prompt
        assert "Previous Tool Calls" not in prompt

    def test_build_tool_prompt_with_history(self, parser):
        """Test building prompt with tool history."""
        query = "Calculate it"
        tools_info = [
            {
                "name": "calculator",
                "description": "Perform calculations",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        ]
        tool_history = [
            {
                "tool": "web_search",
                "parameters": {"query": "math"},
                "result": {"answer": "Math is fun"}
            }
        ]

        prompt = parser.build_tool_prompt(query, tools_info, tool_history)

        assert "Previous Tool Calls" in prompt
        assert "web_search" in prompt
        assert "math" in prompt

    def test_extract_json_with_nested_braces(self, parser):
        """Test extracting JSON with nested objects."""
        response = 'Some text {"outer": {"inner": {"value": 123}}, "tool_calls": []} more text'

        json_data = parser._extract_json(response)

        assert json_data is not None
        assert "outer" in json_data
        assert json_data["outer"]["inner"]["value"] == 123

    def test_extract_json_multiple_objects(self, parser):
        """Test that first valid JSON with expected fields is extracted."""
        response = '{"random": "data"} {"thought": "valid", "tool_calls": []} {"more": "data"}'

        json_data = parser._extract_json(response)

        assert json_data is not None
        assert "thought" in json_data
        assert "tool_calls" in json_data

    def test_raw_response_preserved(self, parser):
        """Test that raw response is always preserved."""
        response = "Just some text"

        parsed = parser.parse(response)

        assert parsed.raw_response == response
