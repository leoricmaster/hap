"""Python REPL tool for executing Python code."""
import io
import sys
import traceback
from contextlib import redirect_stdout, redirect_stderr
from typing import Any, Dict, List

from hap.tools.base import Tool, ToolParameter


class PythonREPL(Tool):
    """Python REPL tool for executing Python code safely."""

    def __init__(self, timeout: int = 30):
        super().__init__(
            name="python",
            description="Execute Python code in a REPL environment. Use this tool for calculations, data processing, file operations, or any task that requires code execution."
        )
        self.timeout = timeout

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="code",
                type="string",
                description="Python code to execute",
                required=True,
                example="print('Hello, World!')"
            )
        ]

    def _execute(self, parameters: Dict[str, Any]) -> str:
        """Execute Python code (parameters already validated)."""
        code = parameters.get("code", "").strip()
        if not code:
            return "Error: Code cannot be empty"

        # Capture stdout and stderr
        stdout_buffer = io.StringIO()
        stderr_buffer = io.StringIO()

        try:
            # Create restricted globals - remove dangerous builtins
            safe_globals = {
                "__builtins__": {
                    name: __builtins__[name]
                    for name in [
                        "abs", "all", "any", "bin", "bool", "bytes", "chr", "dict",
                        "dir", "divmod", "enumerate", "filter", "float", "format",
                        "frozenset", "hasattr", "hash", "hex", "id", "input", "int",
                        "isinstance", "issubclass", "iter", "len", "list", "map",
                        "max", "min", "next", "oct", "open", "ord", "pow", "print",
                        "property", "range", "repr", "reversed", "round", "set",
                        "slice", "sorted", "staticmethod", "str", "sum", "super",
                        "tuple", "type", "vars", "zip", "complex",
                        "delattr", "getattr", "setattr", "callable", "memoryview", "classmethod"
                        # Removed: __import__, eval, exec, compile (security risk)
                    ]
                },
                "__name__": "__main__",
            }

            with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
                exec(code, safe_globals, {})

            stdout_output = stdout_buffer.getvalue()
            stderr_output = stderr_buffer.getvalue()

            result = []
            if stdout_output:
                result.append(f"Output:\n{stdout_output}")
            if stderr_output:
                result.append(f"Stderr:\n{stderr_output}")

            return "\n".join(result) if result else "Code executed successfully (no output)"

        except Exception as e:
            error_msg = f"Error: {str(e)}\n{traceback.format_exc()}"
            return error_msg

