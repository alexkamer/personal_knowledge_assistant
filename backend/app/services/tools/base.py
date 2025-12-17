"""
Base class for all tools used by agents.

Tools provide external capabilities like web search, calculations, code execution, etc.
Each tool must implement the execute method and provide a JSON schema for parameters.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ToolParameter(BaseModel):
    """Schema for a tool parameter."""

    name: str = Field(..., description="Parameter name")
    type: str = Field(..., description="Parameter type (string, number, boolean, array, object)")
    description: str = Field(..., description="Human-readable parameter description")
    required: bool = Field(default=True, description="Whether parameter is required")
    enum: Optional[List[str]] = Field(default=None, description="Allowed values for enum types")
    items: Optional[Dict[str, Any]] = Field(default=None, description="Schema for array items")


class ToolSchema(BaseModel):
    """JSON schema for a tool."""

    name: str = Field(..., description="Tool name (snake_case, no spaces)")
    description: str = Field(..., description="Human-readable tool description")
    parameters: List[ToolParameter] = Field(default_factory=list, description="Tool parameters")

    def to_json_schema(self) -> Dict[str, Any]:
        """Convert to JSON Schema format for LLM consumption."""
        properties = {}
        required = []

        for param in self.parameters:
            param_schema: Dict[str, Any] = {
                "type": param.type,
                "description": param.description,
            }

            if param.enum:
                param_schema["enum"] = param.enum

            if param.items:
                param_schema["items"] = param.items

            properties[param.name] = param_schema

            if param.required:
                required.append(param.name)

        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        }


class ToolResult(BaseModel):
    """Result of a tool execution."""

    success: bool = Field(..., description="Whether execution succeeded")
    result: Any = Field(..., description="Tool output (string, number, dict, list, etc.)")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "success": self.success,
            "result": self.result,
            "error": self.error,
            "metadata": self.metadata or {},
        }


class BaseTool(ABC):
    """
    Abstract base class for all agent tools.

    Each tool must:
    1. Define a unique name (snake_case, no spaces)
    2. Provide a clear description
    3. Specify parameter schema
    4. Implement execute() method
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name (snake_case, no spaces). Example: 'web_search', 'calculator'"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable tool description for LLM."""
        pass

    @property
    @abstractmethod
    def parameters(self) -> List[ToolParameter]:
        """List of tool parameters with schemas."""
        pass

    def get_schema(self) -> ToolSchema:
        """Get the tool schema."""
        return ToolSchema(
            name=self.name,
            description=self.description,
            parameters=self.parameters,
        )

    def get_json_schema(self) -> Dict[str, Any]:
        """Get JSON schema for LLM consumption."""
        return self.get_schema().to_json_schema()

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """
        Execute the tool with provided parameters.

        Args:
            **kwargs: Tool parameters as keyword arguments

        Returns:
            ToolResult with success status, result, and optional error

        Raises:
            ValueError: If parameters are invalid
            RuntimeError: If execution fails
        """
        pass

    def validate_parameters(self, params: Dict[str, Any]) -> None:
        """
        Validate parameters against schema.

        Args:
            params: Parameters to validate

        Raises:
            ValueError: If parameters are invalid
        """
        schema = self.get_schema()

        # Check required parameters
        required_params = [p.name for p in schema.parameters if p.required]
        for param_name in required_params:
            if param_name not in params:
                raise ValueError(f"Missing required parameter: {param_name}")

        # Check for unexpected parameters
        allowed_params = {p.name for p in schema.parameters}
        for param_name in params.keys():
            if param_name not in allowed_params:
                raise ValueError(f"Unexpected parameter: {param_name}")

        # Type validation (basic)
        for param in schema.parameters:
            if param.name in params:
                value = params[param.name]
                expected_type = param.type

                # Basic type checking
                if expected_type == "string" and not isinstance(value, str):
                    raise ValueError(f"Parameter {param.name} must be a string")
                elif expected_type == "number" and not isinstance(value, (int, float)):
                    raise ValueError(f"Parameter {param.name} must be a number")
                elif expected_type == "boolean" and not isinstance(value, bool):
                    raise ValueError(f"Parameter {param.name} must be a boolean")
                elif expected_type == "array" and not isinstance(value, list):
                    raise ValueError(f"Parameter {param.name} must be an array")
                elif expected_type == "object" and not isinstance(value, dict):
                    raise ValueError(f"Parameter {param.name} must be an object")

                # Enum validation
                if param.enum and value not in param.enum:
                    raise ValueError(
                        f"Parameter {param.name} must be one of {param.enum}, got: {value}"
                    )
