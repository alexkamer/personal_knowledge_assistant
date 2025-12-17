"""
Tools package for agent capabilities.

This package provides external tools that agents can use to perform tasks
like web search, calculations, code execution, and document analysis.
"""
from app.services.tools.base import BaseTool, ToolParameter, ToolResult, ToolSchema
from app.services.tools.calculator_tool import CalculatorTool
from app.services.tools.code_executor_tool import CodeExecutorTool
from app.services.tools.document_search_tool import DocumentSearchTool
from app.services.tools.web_search_tool import WebSearchTool

__all__ = [
    "BaseTool",
    "ToolParameter",
    "ToolResult",
    "ToolSchema",
    "CalculatorTool",
    "CodeExecutorTool",
    "DocumentSearchTool",
    "WebSearchTool",
]
