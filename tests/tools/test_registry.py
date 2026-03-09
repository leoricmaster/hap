"""ToolRegistry tests"""
import sys
from pathlib import Path

# Add project root to Python path
_project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(_project_root / "src"))

from hap.tools.registry import ToolRegistry
from hap.tools.builtin.bash import BashTool
from hap.tools.builtin.python_repl import PythonREPL

import logging

logger = logging.getLogger(__name__)


def test_register_single_tool():
    """Test registering a single tool"""
    registry = ToolRegistry()
    bash = BashTool()

    result = registry.register_tool(bash)
    assert result is registry  # Method chaining
    assert "bash" in registry.list_tools()
    logger.info("Single tool registration passed")


def test_register_multiple_tools():
    """Test registering multiple tools at once"""
    registry = ToolRegistry()

    result = registry.register_tools(BashTool(), PythonREPL())
    assert result is registry  # Method chaining
    assert len(registry) == 2
    assert "bash" in registry
    assert "python" in registry
    logger.info("Multiple tool registration passed")


def test_list_tools():
    """Test listing tool names"""
    registry = ToolRegistry()
    registry.register_tool(BashTool())

    tools = registry.list_tools()
    assert isinstance(tools, list)
    assert "bash" in tools
    logger.info("List tools passed")


def test_has_tool():
    """Test checking if tool exists"""
    registry = ToolRegistry()
    registry.register_tool(BashTool())

    assert registry.has_tool("bash") is True
    assert registry.has_tool("nonexistent") is False
    assert "bash" in registry  # Test __contains__
    assert "nonexistent" not in registry
    logger.info("Has tool check passed")


def test_get_tool():
    """Test getting tool by name"""
    registry = ToolRegistry()
    bash = BashTool()
    registry.register_tool(bash)

    retrieved = registry.get_tool("bash")
    assert retrieved is bash
    assert registry.get_tool("nonexistent") is None
    logger.info("Get tool passed")


def test_iteration():
    """Test iterating over tools"""
    registry = ToolRegistry()
    registry.register_tools(BashTool(), PythonREPL())

    tools = list(registry)
    assert len(tools) == 2
    tool_names = [t.name for t in tools]
    assert "bash" in tool_names
    assert "python" in tool_names
    logger.info("Iteration passed")


def test_execute_tool():
    """Test executing a tool through registry"""
    registry = ToolRegistry()
    registry.register_tool(BashTool())

    result = registry.execute_tool("bash", {"command": "echo 'hello'"})
    assert "hello" in result
    logger.info("Tool execution passed")


def test_execute_nonexistent_tool():
    """Test executing a non-existent tool"""
    registry = ToolRegistry()

    result = registry.execute_tool("nonexistent", {})
    assert "Error" in result
    assert "not found" in result
    logger.info("Non-existent tool execution passed")


def test_unregister_tool():
    """Test unregistering a tool"""
    registry = ToolRegistry()
    registry.register_tool(BashTool())

    assert registry.unregister_tool("bash") is True
    assert "bash" not in registry
    assert registry.unregister_tool("bash") is False  # Already removed
    logger.info("Unregister tool passed")


def test_clear():
    """Test clearing all tools"""
    registry = ToolRegistry()
    registry.register_tools(BashTool(), PythonREPL())

    result = registry.clear()
    assert result is registry  # Method chaining
    assert len(registry) == 0
    logger.info("Clear tools passed")


def test_get_tools_description():
    """Test getting tools description"""
    registry = ToolRegistry()
    registry.register_tool(BashTool())

    desc = registry.get_tools_description()
    assert "bash" in desc
    assert "command" in desc
    logger.info("Tools description passed")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    tests = [
        ("Register single tool", test_register_single_tool),
        ("Register multiple tools", test_register_multiple_tools),
        ("List tools", test_list_tools),
        ("Has tool", test_has_tool),
        ("Get tool", test_get_tool),
        ("Iteration", test_iteration),
        ("Execute tool", test_execute_tool),
        ("Execute nonexistent tool", test_execute_nonexistent_tool),
        ("Unregister tool", test_unregister_tool),
        ("Clear tools", test_clear),
        ("Tools description", test_get_tools_description),
    ]

    for name, test_func in tests:
        print("=" * 60)
        print(f"Test: {name}")
        print("=" * 60)
        try:
            test_func()
            print("PASSED\n")
        except Exception as e:
            print(f"FAILED: {e}\n")
            import traceback
            traceback.print_exc()

    print("=" * 60)
    print("All tests completed!")
    print("=" * 60)
