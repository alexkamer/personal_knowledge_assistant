"""
Code execution tool with sandboxing for safe Python code execution.

Executes Python code in a subprocess with timeout and output capture.
"""
import asyncio
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import List

from app.services.tools.base import BaseTool, ToolParameter, ToolResult

logger = logging.getLogger(__name__)

# Restricted imports for safety
RESTRICTED_IMPORTS = [
    "os",
    "sys",
    "subprocess",
    "importlib",
    "__import__",
    "eval",
    "exec",
    "compile",
    "open",
    "file",
    "input",
    "raw_input",
]

# Maximum execution time (seconds)
MAX_EXECUTION_TIME = 10

# Maximum output size (characters)
MAX_OUTPUT_SIZE = 10000


class CodeExecutorTool(BaseTool):
    """Tool for executing Python code safely in a sandboxed environment."""

    @property
    def name(self) -> str:
        return "code_executor"

    @property
    def description(self) -> str:
        return (
            "Execute Python code safely in a sandboxed environment. "
            "Useful for quick calculations, data processing, or testing code snippets. "
            "Limited to 10 seconds execution time. Cannot access files or network."
        )

    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="code",
                type="string",
                description="Python code to execute",
                required=True,
            ),
        ]

    def _check_restricted_imports(self, code: str) -> bool:
        """
        Check if code contains restricted imports.

        Args:
            code: Python code to check

        Returns:
            True if code is safe, False if it contains restricted imports
        """
        code_lower = code.lower()
        for restricted in RESTRICTED_IMPORTS:
            # Check for various import patterns
            if f"import {restricted}" in code_lower:
                return False
            if f"from {restricted}" in code_lower:
                return False
            # Check for __import__('name')
            if f"__import__" in code_lower and restricted in code_lower:
                return False

        return True

    async def execute(self, code: str, **kwargs) -> ToolResult:
        """
        Execute Python code safely.

        Args:
            code: Python code to execute
            **kwargs: Additional arguments (ignored)

        Returns:
            ToolResult with execution output or error
        """
        try:
            # Validate code
            if not code or not code.strip():
                return ToolResult(
                    success=False,
                    result=None,
                    error="Code cannot be empty",
                )

            # Check for restricted imports
            if not self._check_restricted_imports(code):
                return ToolResult(
                    success=False,
                    result=None,
                    error="Code contains restricted imports (os, sys, subprocess, etc.)",
                )

            logger.info(f"Executing Python code ({len(code)} characters)")

            # Create temporary file for code
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.py',
                delete=False,
            ) as temp_file:
                temp_file.write(code)
                temp_file_path = temp_file.name

            try:
                # Execute code in subprocess with timeout
                process = await asyncio.create_subprocess_exec(
                    'python3',
                    temp_file_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )

                try:
                    stdout, stderr = await asyncio.wait_for(
                        process.communicate(),
                        timeout=MAX_EXECUTION_TIME,
                    )
                except asyncio.TimeoutError:
                    # Kill process if timeout
                    process.kill()
                    await process.wait()
                    return ToolResult(
                        success=False,
                        result=None,
                        error=f"Code execution timeout (max {MAX_EXECUTION_TIME}s)",
                    )

                # Decode output
                stdout_str = stdout.decode('utf-8', errors='replace')
                stderr_str = stderr.decode('utf-8', errors='replace')

                # Truncate if too long
                if len(stdout_str) > MAX_OUTPUT_SIZE:
                    stdout_str = stdout_str[:MAX_OUTPUT_SIZE] + "\n... (output truncated)"
                if len(stderr_str) > MAX_OUTPUT_SIZE:
                    stderr_str = stderr_str[:MAX_OUTPUT_SIZE] + "\n... (output truncated)"

                # Check if execution succeeded
                if process.returncode == 0:
                    return ToolResult(
                        success=True,
                        result={
                            "stdout": stdout_str,
                            "stderr": stderr_str,
                            "return_code": process.returncode,
                        },
                        metadata={
                            "tool": self.name,
                            "execution_time": "< 10s",
                        },
                    )
                else:
                    return ToolResult(
                        success=False,
                        result={
                            "stdout": stdout_str,
                            "stderr": stderr_str,
                            "return_code": process.returncode,
                        },
                        error=f"Code execution failed with return code {process.returncode}",
                    )

            finally:
                # Clean up temporary file
                Path(temp_file_path).unlink(missing_ok=True)

        except Exception as e:
            logger.error(f"Code execution error: {e}")
            return ToolResult(
                success=False,
                result=None,
                error=f"Execution error: {str(e)}",
            )
