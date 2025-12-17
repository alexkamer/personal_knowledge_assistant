"""
Unit tests for tool registry.
"""
import pytest
from typing import List

from app.services.tool_registry import ToolRegistry
from app.services.tools.base import BaseTool, ToolParameter, ToolResult


class SimpleTool(BaseTool):
    """Simple tool for testing."""

    @property
    def name(self) -> str:
        return "simple_tool"

    @property
    def description(self) -> str:
        return "A simple tool"

    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(name="param", type="string", description="A parameter", required=True)
        ]

    async def execute(self, **kwargs) -> ToolResult:
        return ToolResult(success=True, result="executed")


class AnotherTool(BaseTool):
    """Another tool for testing."""

    @property
    def name(self) -> str:
        return "another_tool"

    @property
    def description(self) -> str:
        return "Another tool"

    @property
    def parameters(self) -> List[ToolParameter]:
        return []

    async def execute(self, **kwargs) -> ToolResult:
        return ToolResult(success=True, result="executed")


class InvalidNameTool(BaseTool):
    """Tool with invalid name (has spaces)."""

    @property
    def name(self) -> str:
        return "invalid name with spaces"

    @property
    def description(self) -> str:
        return "Invalid tool"

    @property
    def parameters(self) -> List[ToolParameter]:
        return []

    async def execute(self, **kwargs) -> ToolResult:
        return ToolResult(success=True, result="executed")


class TestToolRegistry:
    """Test suite for ToolRegistry."""

    @pytest.fixture
    def registry(self):
        """Create a fresh registry for each test."""
        return ToolRegistry()

    def test_register_tool(self, registry):
        """Test registering a tool."""
        registry.register(SimpleTool, access_level="all")

        assert "simple_tool" in registry.list_tools()

    def test_register_duplicate_tool(self, registry):
        """Test registering a tool with duplicate name."""
        registry.register(SimpleTool, access_level="all")

        with pytest.raises(ValueError, match="already registered"):
            registry.register(SimpleTool, access_level="all")

    def test_register_tool_with_spaces_in_name(self, registry):
        """Test that tool names with spaces are rejected."""
        with pytest.raises(ValueError, match="contains spaces"):
            registry.register(InvalidNameTool, access_level="all")

    def test_get_tool(self, registry):
        """Test getting a tool instance."""
        registry.register(SimpleTool, access_level="all")

        tool = registry.get_tool("simple_tool")

        assert isinstance(tool, SimpleTool)
        assert tool.name == "simple_tool"

    def test_get_tool_not_found(self, registry):
        """Test getting a non-existent tool."""
        with pytest.raises(ValueError, match="not found"):
            registry.get_tool("nonexistent_tool")

    def test_get_tool_schema(self, registry):
        """Test getting tool schema."""
        registry.register(SimpleTool, access_level="all")

        schema = registry.get_tool_schema("simple_tool")

        assert schema.name == "simple_tool"
        assert schema.description == "A simple tool"
        assert len(schema.parameters) == 1

    def test_list_tools(self, registry):
        """Test listing all tools."""
        registry.register(SimpleTool, access_level="all")
        registry.register(AnotherTool, access_level="restricted")

        tools = registry.list_tools()

        assert len(tools) == 2
        assert "simple_tool" in tools
        assert "another_tool" in tools

    def test_list_tools_by_access_level(self, registry):
        """Test listing tools filtered by access level."""
        registry.register(SimpleTool, access_level="all")
        registry.register(AnotherTool, access_level="restricted")

        all_tools = registry.list_tools(access_level="all")
        restricted_tools = registry.list_tools(access_level="restricted")

        assert "simple_tool" in all_tools
        assert "another_tool" not in all_tools
        assert "simple_tool" not in restricted_tools
        assert "another_tool" in restricted_tools

    def test_get_all_schemas(self, registry):
        """Test getting all tool schemas."""
        registry.register(SimpleTool, access_level="all")
        registry.register(AnotherTool, access_level="all")

        schemas = registry.get_all_schemas()

        assert len(schemas) == 2
        schema_names = [s.name for s in schemas]
        assert "simple_tool" in schema_names
        assert "another_tool" in schema_names

    def test_is_tool_available_all_access(self, registry):
        """Test tool availability with full access (None)."""
        registry.register(SimpleTool, access_level="all")

        # None means all tools available
        assert registry.is_tool_available("simple_tool", None) is True

    def test_is_tool_available_no_access(self, registry):
        """Test tool availability with no access ([])."""
        registry.register(SimpleTool, access_level="all")

        # Empty list means no tools available
        assert registry.is_tool_available("simple_tool", []) is False

    def test_is_tool_available_specific_access(self, registry):
        """Test tool availability with specific access list."""
        registry.register(SimpleTool, access_level="all")
        registry.register(AnotherTool, access_level="all")

        # Only simple_tool in access list
        access_list = ["simple_tool"]

        assert registry.is_tool_available("simple_tool", access_list) is True
        assert registry.is_tool_available("another_tool", access_list) is False

    def test_is_tool_available_nonexistent(self, registry):
        """Test availability check for non-existent tool."""
        assert registry.is_tool_available("nonexistent", None) is False

    def test_get_available_tools_all_access(self, registry):
        """Test getting available tools with full access."""
        registry.register(SimpleTool, access_level="all")
        registry.register(AnotherTool, access_level="all")

        # None means all tools
        available = registry.get_available_tools(None)

        assert len(available) == 2
        assert "simple_tool" in available
        assert "another_tool" in available

    def test_get_available_tools_no_access(self, registry):
        """Test getting available tools with no access."""
        registry.register(SimpleTool, access_level="all")

        # Empty list means no tools
        available = registry.get_available_tools([])

        assert len(available) == 0

    def test_get_available_tools_specific_access(self, registry):
        """Test getting available tools with specific access list."""
        registry.register(SimpleTool, access_level="all")
        registry.register(AnotherTool, access_level="all")

        # Only simple_tool in access list
        available = registry.get_available_tools(["simple_tool"])

        assert len(available) == 1
        assert "simple_tool" in available
        assert "another_tool" not in available

    def test_get_available_tools_with_nonexistent(self, registry):
        """Test getting available tools when access list includes non-existent tool."""
        registry.register(SimpleTool, access_level="all")

        # Access list includes nonexistent tool
        available = registry.get_available_tools(["simple_tool", "nonexistent"])

        # Should only return registered tools
        assert len(available) == 1
        assert "simple_tool" in available

    def test_get_access_level(self, registry):
        """Test getting access level for a tool."""
        registry.register(SimpleTool, access_level="all")
        registry.register(AnotherTool, access_level="restricted")

        assert registry.get_access_level("simple_tool") == "all"
        assert registry.get_access_level("another_tool") == "restricted"
        assert registry.get_access_level("nonexistent") is None

    def test_lazy_loading(self, registry):
        """Test that tools are instantiated lazily."""
        registry.register(SimpleTool, access_level="all")

        # Tool not instantiated yet
        assert "simple_tool" not in registry._tools

        # Get tool - should instantiate now
        tool = registry.get_tool("simple_tool")

        # Tool should be cached now
        assert "simple_tool" in registry._tools
        assert isinstance(tool, SimpleTool)

        # Getting again should return same instance
        tool2 = registry.get_tool("simple_tool")
        assert tool is tool2
