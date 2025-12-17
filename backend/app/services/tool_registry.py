"""
Tool registry for managing available tools and access control.

Provides a central registry of all tools available to agents, with schemas
and access control configuration.
"""
import logging
from typing import Dict, List, Optional, Type

from app.services.tools.base import BaseTool, ToolSchema

logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    Registry for managing agent tools.

    Provides tool discovery, schema generation, and access control.
    """

    def __init__(self):
        """Initialize the tool registry."""
        self._tools: Dict[str, BaseTool] = {}
        self._tool_classes: Dict[str, Type[BaseTool]] = {}
        self._access_levels: Dict[str, str] = {}

    def register(
        self,
        tool_class: Type[BaseTool],
        access_level: str = "all",
    ) -> None:
        """
        Register a tool class.

        Args:
            tool_class: Tool class to register
            access_level: Access control level ("all", "restricted", "admin")

        Raises:
            ValueError: If tool name already registered
        """
        # Instantiate tool to get its name
        tool_instance = tool_class()
        tool_name = tool_instance.name

        if tool_name in self._tool_classes:
            raise ValueError(f"Tool '{tool_name}' already registered")

        # Validate tool name (no spaces, snake_case)
        if " " in tool_name:
            raise ValueError(f"Tool name '{tool_name}' contains spaces. Use snake_case.")

        if not tool_name.replace("_", "").isalnum():
            raise ValueError(
                f"Tool name '{tool_name}' contains invalid characters. Use snake_case."
            )

        self._tool_classes[tool_name] = tool_class
        self._access_levels[tool_name] = access_level

        logger.info(f"Registered tool: {tool_name} (access_level={access_level})")

    def get_tool(self, tool_name: str) -> BaseTool:
        """
        Get a tool instance by name.

        Args:
            tool_name: Name of the tool

        Returns:
            Tool instance

        Raises:
            ValueError: If tool not found
        """
        if tool_name not in self._tools:
            if tool_name not in self._tool_classes:
                raise ValueError(f"Tool '{tool_name}' not found in registry")

            # Instantiate tool on first access (lazy loading)
            self._tools[tool_name] = self._tool_classes[tool_name]()

        return self._tools[tool_name]

    def get_tool_schema(self, tool_name: str) -> ToolSchema:
        """
        Get tool schema by name.

        Args:
            tool_name: Name of the tool

        Returns:
            Tool schema

        Raises:
            ValueError: If tool not found
        """
        tool = self.get_tool(tool_name)
        return tool.get_schema()

    def get_all_schemas(self, access_level: Optional[str] = None) -> List[ToolSchema]:
        """
        Get schemas for all tools.

        Args:
            access_level: Optional access level filter

        Returns:
            List of tool schemas
        """
        schemas = []
        for tool_name in self._tool_classes.keys():
            # Filter by access level if specified
            if access_level and self._access_levels[tool_name] != access_level:
                continue

            tool = self.get_tool(tool_name)
            schemas.append(tool.get_schema())

        return schemas

    def list_tools(self, access_level: Optional[str] = None) -> List[str]:
        """
        List all registered tool names.

        Args:
            access_level: Optional access level filter

        Returns:
            List of tool names
        """
        if access_level:
            return [
                name
                for name, level in self._access_levels.items()
                if level == access_level
            ]
        return list(self._tool_classes.keys())

    def is_tool_available(self, tool_name: str, agent_access_list: Optional[List[str]]) -> bool:
        """
        Check if a tool is available to an agent.

        Args:
            tool_name: Name of the tool
            agent_access_list: Agent's tool access list (None = all, [] = none)

        Returns:
            True if tool is available, False otherwise
        """
        if tool_name not in self._tool_classes:
            return False

        # None means all tools available
        if agent_access_list is None:
            return True

        # Empty list means no tools available
        if not agent_access_list:
            return False

        # Check if tool in access list
        return tool_name in agent_access_list

    def get_available_tools(self, agent_access_list: Optional[List[str]]) -> List[str]:
        """
        Get list of tools available to an agent.

        Args:
            agent_access_list: Agent's tool access list (None = all, [] = none)

        Returns:
            List of available tool names
        """
        if agent_access_list is None:
            return self.list_tools()

        if not agent_access_list:
            return []

        return [
            tool_name
            for tool_name in agent_access_list
            if tool_name in self._tool_classes
        ]

    def get_access_level(self, tool_name: str) -> Optional[str]:
        """
        Get access level for a tool.

        Args:
            tool_name: Name of the tool

        Returns:
            Access level or None if not found
        """
        return self._access_levels.get(tool_name)


# Global tool registry instance
_tool_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """
    Get the global tool registry instance.

    Returns:
        Tool registry singleton
    """
    global _tool_registry
    if _tool_registry is None:
        _tool_registry = ToolRegistry()
        _register_builtin_tools()
    return _tool_registry


def _register_builtin_tools() -> None:
    """Register all built-in tools."""
    # Tools will be registered here as they're implemented
    # Example:
    # from app.services.tools.web_search_tool import WebSearchTool
    # registry = get_tool_registry()
    # registry.register(WebSearchTool, access_level="all")
    pass
