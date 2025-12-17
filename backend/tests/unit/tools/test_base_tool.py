"""
Unit tests for BaseTool and related classes.
"""
import pytest
from typing import List

from app.services.tools.base import (
    BaseTool,
    ToolParameter,
    ToolResult,
    ToolSchema,
)


class MockTool(BaseTool):
    """Mock tool for testing."""

    @property
    def name(self) -> str:
        return "mock_tool"

    @property
    def description(self) -> str:
        return "A mock tool for testing"

    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="required_param",
                type="string",
                description="A required parameter",
                required=True,
            ),
            ToolParameter(
                name="optional_param",
                type="number",
                description="An optional parameter",
                required=False,
            ),
            ToolParameter(
                name="enum_param",
                type="string",
                description="A parameter with enum values",
                required=False,
                enum=["option1", "option2", "option3"],
            ),
        ]

    async def execute(self, **kwargs) -> ToolResult:
        """Mock execute."""
        return ToolResult(
            success=True,
            result={"input": kwargs},
            metadata={"tool": self.name},
        )


class TestToolParameter:
    """Test suite for ToolParameter."""

    def test_tool_parameter_creation(self):
        """Test creating a tool parameter."""
        param = ToolParameter(
            name="test_param",
            type="string",
            description="Test parameter",
            required=True,
        )

        assert param.name == "test_param"
        assert param.type == "string"
        assert param.description == "Test parameter"
        assert param.required is True
        assert param.enum is None

    def test_tool_parameter_with_enum(self):
        """Test creating a parameter with enum values."""
        param = ToolParameter(
            name="choice",
            type="string",
            description="Choose an option",
            required=True,
            enum=["a", "b", "c"],
        )

        assert param.enum == ["a", "b", "c"]


class TestToolSchema:
    """Test suite for ToolSchema."""

    def test_tool_schema_creation(self):
        """Test creating a tool schema."""
        schema = ToolSchema(
            name="test_tool",
            description="A test tool",
            parameters=[
                ToolParameter(name="param1", type="string", description="First param", required=True),
                ToolParameter(name="param2", type="number", description="Second param", required=False),
            ],
        )

        assert schema.name == "test_tool"
        assert schema.description == "A test tool"
        assert len(schema.parameters) == 2

    def test_to_json_schema(self):
        """Test converting to JSON schema."""
        schema = ToolSchema(
            name="test_tool",
            description="A test tool",
            parameters=[
                ToolParameter(name="param1", type="string", description="First param", required=True),
                ToolParameter(name="param2", type="number", description="Second param", required=False),
            ],
        )

        json_schema = schema.to_json_schema()

        assert json_schema["name"] == "test_tool"
        assert json_schema["description"] == "A test tool"
        assert "parameters" in json_schema
        assert json_schema["parameters"]["type"] == "object"
        assert "param1" in json_schema["parameters"]["properties"]
        assert "param2" in json_schema["parameters"]["properties"]
        assert json_schema["parameters"]["required"] == ["param1"]

    def test_to_json_schema_with_enum(self):
        """Test JSON schema with enum parameter."""
        schema = ToolSchema(
            name="test_tool",
            description="A test tool",
            parameters=[
                ToolParameter(
                    name="choice",
                    type="string",
                    description="Choose option",
                    required=True,
                    enum=["a", "b", "c"],
                ),
            ],
        )

        json_schema = schema.to_json_schema()

        assert "choice" in json_schema["parameters"]["properties"]
        assert json_schema["parameters"]["properties"]["choice"]["enum"] == ["a", "b", "c"]


class TestToolResult:
    """Test suite for ToolResult."""

    def test_tool_result_success(self):
        """Test successful tool result."""
        result = ToolResult(
            success=True,
            result={"data": "test"},
        )

        assert result.success is True
        assert result.result == {"data": "test"}
        assert result.error is None

    def test_tool_result_failure(self):
        """Test failed tool result."""
        result = ToolResult(
            success=False,
            result=None,
            error="Something went wrong",
        )

        assert result.success is False
        assert result.result is None
        assert result.error == "Something went wrong"

    def test_tool_result_to_dict(self):
        """Test converting tool result to dict."""
        result = ToolResult(
            success=True,
            result={"data": "test"},
            metadata={"execution_time": 0.5},
        )

        result_dict = result.to_dict()

        assert result_dict["success"] is True
        assert result_dict["result"] == {"data": "test"}
        assert result_dict["metadata"]["execution_time"] == 0.5


class TestBaseTool:
    """Test suite for BaseTool."""

    def test_tool_properties(self):
        """Test tool properties."""
        tool = MockTool()

        assert tool.name == "mock_tool"
        assert tool.description == "A mock tool for testing"
        assert len(tool.parameters) == 3

    def test_get_schema(self):
        """Test getting tool schema."""
        tool = MockTool()
        schema = tool.get_schema()

        assert isinstance(schema, ToolSchema)
        assert schema.name == "mock_tool"
        assert schema.description == "A mock tool for testing"
        assert len(schema.parameters) == 3

    def test_get_json_schema(self):
        """Test getting JSON schema."""
        tool = MockTool()
        json_schema = tool.get_json_schema()

        assert json_schema["name"] == "mock_tool"
        assert "parameters" in json_schema
        assert "required_param" in json_schema["parameters"]["properties"]

    def test_validate_parameters_success(self):
        """Test successful parameter validation."""
        tool = MockTool()

        # Valid parameters
        params = {"required_param": "test"}
        tool.validate_parameters(params)  # Should not raise

    def test_validate_parameters_missing_required(self):
        """Test validation with missing required parameter."""
        tool = MockTool()

        # Missing required parameter
        params = {"optional_param": 42}

        with pytest.raises(ValueError, match="Missing required parameter: required_param"):
            tool.validate_parameters(params)

    def test_validate_parameters_unexpected_param(self):
        """Test validation with unexpected parameter."""
        tool = MockTool()

        # Unexpected parameter
        params = {
            "required_param": "test",
            "unexpected_param": "value",
        }

        with pytest.raises(ValueError, match="Unexpected parameter: unexpected_param"):
            tool.validate_parameters(params)

    def test_validate_parameters_wrong_type(self):
        """Test validation with wrong parameter type."""
        tool = MockTool()

        # Wrong type (number instead of string)
        params = {"required_param": 123}

        with pytest.raises(ValueError, match="must be a string"):
            tool.validate_parameters(params)

    def test_validate_parameters_enum_invalid(self):
        """Test validation with invalid enum value."""
        tool = MockTool()

        # Invalid enum value
        params = {
            "required_param": "test",
            "enum_param": "invalid_option",
        }

        with pytest.raises(ValueError, match="must be one of"):
            tool.validate_parameters(params)

    def test_validate_parameters_enum_valid(self):
        """Test validation with valid enum value."""
        tool = MockTool()

        # Valid enum value
        params = {
            "required_param": "test",
            "enum_param": "option1",
        }

        tool.validate_parameters(params)  # Should not raise

    @pytest.mark.asyncio
    async def test_execute(self):
        """Test tool execution."""
        tool = MockTool()

        result = await tool.execute(required_param="test", optional_param=42)

        assert result.success is True
        assert result.result["input"]["required_param"] == "test"
        assert result.result["input"]["optional_param"] == 42
