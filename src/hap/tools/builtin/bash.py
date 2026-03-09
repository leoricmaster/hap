"""Bash tool for executing shell commands."""
import subprocess
from typing import Any, Dict, List, Optional

from hap.tools.base import Tool, ToolParameter


class BashTool(Tool):
    """Bash tool for executing shell commands safely."""

    # Commands that are not allowed for security reasons
    BLOCKED_COMMANDS = [
        "rm -rf /", "rm -rf /*", "rm -rf ~", "rm -rf ~/*",
        ":(){ :|:& };:", "fork bomb", "mkfs", "dd if=/dev/zero",
        "> /dev/sda", ">/dev/sda", "/dev/sda",
        "chmod -R 777 /", "chmod 777 /",
    ]

    def __init__(self, timeout: int = 60, working_dir: Optional[str] = None):
        super().__init__(
            name="bash",
            description="Execute bash/shell commands. Use this tool for file operations, system commands, git operations, or running scripts."
        )
        self.timeout = timeout
        self.working_dir = working_dir

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="command",
                type="string",
                description="Bash command to execute",
                required=True,
                example="ls -la"
            ),
            ToolParameter(
                name="timeout",
                type="integer",
                description="Command timeout in seconds (default: 60)",
                required=False,
                default=60
            )
        ]

    def _is_command_safe(self, command: str) -> bool:
        """Check if command contains blocked patterns."""
        command_lower = command.lower().strip()
        for blocked in self.BLOCKED_COMMANDS:
            if blocked.lower() in command_lower:
                return False
        return True

    def _execute(self, parameters: Dict[str, Any]) -> str:
        """Execute bash command (parameters already validated)."""
        command = parameters.get("command", "").strip()
        if not command:
            return "Error: Command cannot be empty"

        # Security check
        if not self._is_command_safe(command):
            return "Error: Command blocked for security reasons"

        timeout = parameters.get("timeout", self.timeout)

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.working_dir
            )

            output_lines = []

            if result.stdout:
                output_lines.append(f"Stdout:\n{result.stdout}")

            if result.stderr:
                output_lines.append(f"Stderr:\n{result.stderr}")

            if result.returncode != 0:
                output_lines.append(f"Exit code: {result.returncode}")

            if not output_lines:
                return "Command executed successfully (no output)"

            return "\n".join(output_lines)

        except subprocess.TimeoutExpired:
            return f"Error: Command timed out after {timeout} seconds"
        except Exception as e:
            return f"Error: {str(e)}"

