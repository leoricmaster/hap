"""Bash tool tests"""
import sys
from pathlib import Path

# Add project root to Python path
_project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(_project_root / "src"))

from hap.tools.builtin.bash import BashTool

import logging

logger = logging.getLogger(__name__)


def test_bash_success():
    """Test bash with valid command"""
    logger.info("Initializing Bash tool...")
    bash = BashTool()
    logger.info("Bash tool initialized")

    test_command = "echo 'Hello from Bash!'"
    logger.info(f"Testing command: {test_command}")

    result = bash.run({"command": test_command})
    print(f"\nResult:\n{result}")
    logger.info("Command execution completed")

    assert "Hello from Bash!" in result
    logger.info("Result validation passed")


def test_bash_empty_command():
    """Test bash with empty command"""
    logger.info("Testing empty command validation...")
    bash = BashTool()

    result = bash.run({"command": "   "})
    print(f"\nResult: {result}")

    assert "cannot be empty" in result
    logger.info("Empty command validation passed")


def test_bash_missing_parameter():
    """Test bash with missing command parameter"""
    logger.info("Testing missing parameter validation...")
    bash = BashTool()

    result = bash.run({})
    print(f"\nResult: {result}")

    assert "Missing required parameters" in result
    logger.info("Missing parameter validation passed")


def test_bash_non_zero_exit():
    """Test bash with command that returns non-zero exit code"""
    logger.info("Testing non-zero exit code...")
    bash = BashTool()

    result = bash.run({"command": "false"})
    print(f"\nResult:\n{result}")

    assert "Exit code: 1" in result
    logger.info("Non-zero exit code test passed")


def test_bash_blocked_command_detection():
    """Test bash blocked command detection (without executing)"""
    logger.info("Testing blocked command detection...")
    bash = BashTool()

    blocked_commands = [
        "rm -rf /",
        "rm -rf ~",
        "mkfs /dev/sda",
        ":(){ :|:& };:",
    ]

    for cmd in blocked_commands:
        is_safe = bash._is_command_safe(cmd)
        print(f"  '{cmd}' -> {'ALLOWED' if is_safe else 'BLOCKED'}")
        assert not is_safe, f"Command '{cmd}' should be blocked"

    logger.info("Blocked command detection passed")


def test_bash_safe_commands():
    """Test that safe commands are allowed"""
    logger.info("Testing safe command detection...")
    bash = BashTool()

    safe_commands = [
        "ls -la",
        "pwd",
        "echo 'hello'",
        "cat file.txt",
    ]

    for cmd in safe_commands:
        is_safe = bash._is_command_safe(cmd)
        print(f"  '{cmd}' -> {'ALLOWED' if is_safe else 'BLOCKED'}")
        assert is_safe, f"Command '{cmd}' should be allowed"

    logger.info("Safe command detection passed")


def test_bash_blocked_execution():
    """Test that blocked command is not executed"""
    logger.info("Testing blocked command execution...")
    bash = BashTool()

    result = bash.run({"command": "rm -rf /"})
    print(f"\nResult: {result}")

    assert "blocked for security reasons" in result
    logger.info("Blocked command execution test passed")


def test_bash_description():
    """Test tool description generation"""
    bash = BashTool()
    desc = bash.get_description()

    assert "bash" in desc
    assert "command" in desc
    assert "TOOL_CALL:bash" in desc
    print(f"\nTool description:\n{desc}")


def test_bash_example():
    """Test tool example generation"""
    bash = BashTool()
    example = bash.get_example()

    assert example.startswith("[TOOL_CALL:bash:")
    assert "command=" in example
    print(f"\nTool example: {example}")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    print("=" * 80)
    print("Test 1: Valid command execution")
    print("=" * 80)
    test_bash_success()

    print("\n" + "=" * 80)
    print("Test 2: Empty command validation")
    print("=" * 80)
    test_bash_empty_command()

    print("\n" + "=" * 80)
    print("Test 3: Missing parameter validation")
    print("=" * 80)
    test_bash_missing_parameter()

    print("\n" + "=" * 80)
    print("Test 4: Non-zero exit code")
    print("=" * 80)
    test_bash_non_zero_exit()

    print("\n" + "=" * 80)
    print("Test 5: Blocked command detection")
    print("=" * 80)
    test_bash_blocked_command_detection()

    print("\n" + "=" * 80)
    print("Test 6: Safe command detection")
    print("=" * 80)
    test_bash_safe_commands()

    print("\n" + "=" * 80)
    print("Test 7: Blocked command execution")
    print("=" * 80)
    test_bash_blocked_execution()

    print("\n" + "=" * 80)
    print("Test 8: Tool description generation")
    print("=" * 80)
    test_bash_description()

    print("\n" + "=" * 80)
    print("Test 9: Tool example generation")
    print("=" * 80)
    test_bash_example()

    print("\n" + "=" * 80)
    print("All tests passed!")
    print("=" * 80)
