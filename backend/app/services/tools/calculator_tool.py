"""
Calculator tool for safe mathematical expression evaluation.

Uses ast.literal_eval for safety and supports basic arithmetic operations.
"""
import ast
import logging
import operator
from typing import List

from app.services.tools.base import BaseTool, ToolParameter, ToolResult

logger = logging.getLogger(__name__)

# Safe operators
SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.FloorDiv: operator.floordiv,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


class CalculatorTool(BaseTool):
    """Tool for evaluating mathematical expressions safely."""

    @property
    def name(self) -> str:
        return "calculator"

    @property
    def description(self) -> str:
        return (
            "Evaluate mathematical expressions. Supports basic arithmetic operations: "
            "addition (+), subtraction (-), multiplication (*), division (/), "
            "exponentiation (**), modulo (%), floor division (//)."
        )

    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="expression",
                type="string",
                description="Mathematical expression to evaluate (e.g., '2 + 2', '10 * 5 + 3')",
                required=True,
            ),
        ]

    def _eval_node(self, node):
        """
        Safely evaluate an AST node.

        Args:
            node: AST node to evaluate

        Returns:
            Evaluation result

        Raises:
            ValueError: If node type is not allowed
        """
        if isinstance(node, ast.Constant):  # Python 3.8+
            return node.value
        elif isinstance(node, ast.Num):  # Fallback for older Python
            return node.n
        elif isinstance(node, ast.BinOp):
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            op_type = type(node.op)
            if op_type not in SAFE_OPERATORS:
                raise ValueError(f"Operator {op_type.__name__} not allowed")
            return SAFE_OPERATORS[op_type](left, right)
        elif isinstance(node, ast.UnaryOp):
            operand = self._eval_node(node.operand)
            op_type = type(node.op)
            if op_type not in SAFE_OPERATORS:
                raise ValueError(f"Operator {op_type.__name__} not allowed")
            return SAFE_OPERATORS[op_type](operand)
        elif isinstance(node, ast.Expression):
            return self._eval_node(node.body)
        else:
            raise ValueError(f"Node type {type(node).__name__} not allowed")

    def _safe_eval(self, expression: str) -> float:
        """
        Safely evaluate a mathematical expression.

        Args:
            expression: String expression to evaluate

        Returns:
            Numeric result

        Raises:
            ValueError: If expression is invalid or unsafe
            ZeroDivisionError: If division by zero
        """
        try:
            # Parse expression into AST
            tree = ast.parse(expression, mode='eval')
            # Evaluate safely
            return self._eval_node(tree)
        except SyntaxError as e:
            raise ValueError(f"Invalid expression syntax: {e}")
        except ZeroDivisionError:
            raise
        except Exception as e:
            raise ValueError(f"Evaluation error: {e}")

    async def execute(self, expression: str, **kwargs) -> ToolResult:
        """
        Execute calculator evaluation.

        Args:
            expression: Mathematical expression to evaluate
            **kwargs: Additional arguments (ignored)

        Returns:
            ToolResult with calculation result or error
        """
        try:
            # Clean expression
            expression = expression.strip()

            if not expression:
                return ToolResult(
                    success=False,
                    result=None,
                    error="Expression cannot be empty",
                )

            logger.info(f"Evaluating expression: {expression}")

            # Evaluate expression safely
            result = self._safe_eval(expression)

            return ToolResult(
                success=True,
                result={
                    "expression": expression,
                    "result": result,
                },
                metadata={
                    "tool": self.name,
                },
            )

        except ZeroDivisionError:
            logger.warning(f"Division by zero in expression: {expression}")
            return ToolResult(
                success=False,
                result=None,
                error="Division by zero",
            )

        except ValueError as e:
            logger.warning(f"Invalid expression: {expression} - {e}")
            return ToolResult(
                success=False,
                result=None,
                error=str(e),
            )

        except Exception as e:
            logger.error(f"Calculator execution failed: {e}")
            return ToolResult(
                success=False,
                result=None,
                error=f"Calculation failed: {str(e)}",
            )
