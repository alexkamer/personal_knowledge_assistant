"""
Parser for extracting tool calls from LLM responses.

Since Ollama models don't have native function calling, we use prompt engineering
to get the LLM to output JSON with tool calls or final answers. This module parses
those responses.
"""
import json
import logging
import re
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ToolCall(BaseModel):
    """Parsed tool call from LLM response."""

    tool: str = Field(..., description="Tool name (snake_case)")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Tool parameters")
    thought: Optional[str] = Field(default=None, description="Reasoning behind tool call")


class ParsedResponse(BaseModel):
    """Parsed LLM response with tool calls or final answer."""

    thought: Optional[str] = Field(default=None, description="LLM's reasoning")
    tool_calls: List[ToolCall] = Field(default_factory=list, description="Tool calls to execute")
    final_answer: Optional[str] = Field(default=None, description="Final answer if reasoning complete")
    raw_response: str = Field(..., description="Original LLM response")


class ToolCallParser:
    """
    Parser for extracting tool calls from LLM responses.

    Supports multiple formats:
    1. Pure JSON: {"thought": "...", "tool_calls": [...]}
    2. JSON in markdown code block: ```json\n{...}\n```
    3. JSON with extra text: Some text before {"tool_calls": [...]} some text after
    """

    def __init__(self):
        """Initialize the parser."""
        pass

    def parse(self, llm_response: str) -> ParsedResponse:
        """
        Parse LLM response for tool calls or final answer.

        Args:
            llm_response: Raw response from LLM

        Returns:
            ParsedResponse with extracted tool calls or final answer
        """
        if not llm_response or not llm_response.strip():
            logger.warning("Empty LLM response received")
            return ParsedResponse(
                raw_response=llm_response,
                final_answer="I apologize, but I couldn't generate a response.",
            )

        # Try to extract JSON from response
        json_data = self._extract_json(llm_response)

        if json_data:
            return self._parse_json(json_data, llm_response)

        # No JSON found - treat as final answer
        logger.info("No JSON structure found in response, treating as final answer")
        return ParsedResponse(
            raw_response=llm_response,
            final_answer=llm_response.strip(),
        )

    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Extract JSON from text.

        Tries multiple extraction strategies:
        1. Direct JSON parse
        2. Extract from markdown code block
        3. Extract first JSON object from mixed text
        """
        # Strategy 1: Try direct parse
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            pass

        # Strategy 2: Extract from markdown code block
        # Matches ```json\n{...}\n``` or ```\n{...}\n```
        code_block_pattern = r"```(?:json)?\s*\n(.*?)\n```"
        matches = re.findall(code_block_pattern, text, re.DOTALL)
        for match in matches:
            try:
                return json.loads(match.strip())
            except json.JSONDecodeError:
                continue

        # Strategy 3: Find first JSON object in text
        # Use a more robust approach: find { and match closing }
        brace_count = 0
        start_idx = -1

        for i, char in enumerate(text):
            if char == '{':
                if brace_count == 0:
                    start_idx = i
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0 and start_idx != -1:
                    # Found a complete JSON object
                    potential_json = text[start_idx:i+1]
                    try:
                        data = json.loads(potential_json)
                        # Only accept if it has expected fields
                        if isinstance(data, dict) and (
                            "tool_calls" in data or "final_answer" in data or "thought" in data
                        ):
                            return data
                    except json.JSONDecodeError:
                        # Continue searching
                        pass
                    start_idx = -1

        return None

    def _parse_json(self, json_data: Dict[str, Any], raw_response: str) -> ParsedResponse:
        """
        Parse extracted JSON into ParsedResponse.

        Args:
            json_data: Extracted JSON data
            raw_response: Original LLM response

        Returns:
            ParsedResponse
        """
        thought = json_data.get("thought")
        final_answer = json_data.get("final_answer")
        tool_calls_data = json_data.get("tool_calls", [])

        # Parse tool calls
        tool_calls = []
        for tc_data in tool_calls_data:
            if not isinstance(tc_data, dict):
                logger.warning(f"Invalid tool call format: {tc_data}")
                continue

            tool = tc_data.get("tool")
            if not tool:
                logger.warning(f"Tool call missing 'tool' field: {tc_data}")
                continue

            tool_call = ToolCall(
                tool=tool,
                parameters=tc_data.get("parameters", {}),
                thought=tc_data.get("thought"),
            )
            tool_calls.append(tool_call)

        return ParsedResponse(
            thought=thought,
            tool_calls=tool_calls,
            final_answer=final_answer,
            raw_response=raw_response,
        )

    def format_tool_definitions(self, tools_info: List[Dict[str, Any]]) -> str:
        """
        Format tool definitions for LLM prompt.

        Args:
            tools_info: List of tool JSON schemas

        Returns:
            Formatted string for prompt
        """
        if not tools_info:
            return "No tools available."

        formatted = "# Available Tools\n\n"
        for tool_info in tools_info:
            formatted += f"## {tool_info['name']}\n"
            formatted += f"{tool_info['description']}\n\n"

            if tool_info.get("parameters", {}).get("properties"):
                formatted += "### Parameters:\n"
                for param_name, param_info in tool_info["parameters"]["properties"].items():
                    required = param_name in tool_info["parameters"].get("required", [])
                    formatted += f"- **{param_name}** ({'required' if required else 'optional'}): "
                    formatted += f"{param_info.get('description', 'No description')}\n"
                    formatted += f"  - Type: {param_info.get('type', 'unknown')}\n"

                    if "enum" in param_info:
                        formatted += f"  - Allowed values: {', '.join(param_info['enum'])}\n"

                formatted += "\n"

        return formatted

    def build_tool_prompt(
        self,
        query: str,
        tools_info: List[Dict[str, Any]],
        tool_history: List[Dict[str, Any]],
    ) -> str:
        """
        Build a prompt that instructs the LLM to use tools.

        Args:
            query: User's query
            tools_info: Available tools with schemas
            tool_history: Previous tool calls and results

        Returns:
            Formatted prompt string
        """
        prompt = f"""You are a helpful AI assistant with access to external tools. Your task is to answer the user's question using available tools when necessary.

{self.format_tool_definitions(tools_info)}

## Instructions

1. **Think step-by-step**: Before calling tools, explain your reasoning in the "thought" field.
2. **Use tools when needed**: If you need external information or capabilities, call the appropriate tools.
3. **Call multiple tools**: You can call multiple tools in a single response if needed.
4. **Provide final answer**: Once you have enough information, provide a "final_answer" field with your complete response.

## Response Format

You MUST respond with valid JSON in one of these formats:

### Format 1: Call tools (when you need more information)
```json
{{
  "thought": "Explanation of what you're doing and why",
  "tool_calls": [
    {{
      "tool": "tool_name",
      "parameters": {{"param1": "value1", "param2": "value2"}},
      "thought": "Optional: Why you're calling this specific tool"
    }}
  ]
}}
```

### Format 2: Provide final answer (when you have enough information)
```json
{{
  "thought": "Summary of your reasoning",
  "final_answer": "Your complete answer to the user's question"
}}
```

"""

        # Add tool history if available
        if tool_history:
            prompt += "## Previous Tool Calls\n\n"
            for i, entry in enumerate(tool_history, 1):
                prompt += f"### Call {i}: {entry['tool']}\n"
                prompt += f"**Parameters**: {json.dumps(entry['parameters'])}\n"
                prompt += f"**Result**: {json.dumps(entry['result'], indent=2)}\n\n"

        prompt += f"""## User Query
{query}

## Your Response (must be valid JSON)
"""

        return prompt


# Global parser instance
_tool_call_parser: Optional[ToolCallParser] = None


def get_tool_call_parser() -> ToolCallParser:
    """
    Get the global tool call parser instance.

    Returns:
        Tool call parser singleton
    """
    global _tool_call_parser
    if _tool_call_parser is None:
        _tool_call_parser = ToolCallParser()
    return _tool_call_parser
