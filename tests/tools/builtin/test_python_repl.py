"""Python REPL tool tests"""
import sys
from pathlib import Path

# Add project root to Python path
_project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(_project_root / "src"))

from hap.tools.builtin.python_repl import PythonREPL

import logging

logger = logging.getLogger(__name__)


def test_python_repl_success():
    """Test Python REPL with valid code"""
    logger.info("Initializing Python REPL tool...")
    repl = PythonREPL()
    logger.info("Python REPL tool initialized")

    test_code = "x = [1, 2, 3, 4, 5]\nprint(f'Sum: {sum(x)}')"
    logger.info(f"Testing code execution: {repr(test_code)}")

    result = repl.run({"code": test_code})
    print(f"\nResult:\n{result}")
    logger.info("Code execution completed")

    assert "Sum: 15" in result
    logger.info("Result validation passed")


def test_python_repl_empty_code():
    """Test Python REPL with empty code"""
    logger.info("Testing empty code validation...")
    repl = PythonREPL()

    result = repl.run({"code": "   "})
    print(f"\nResult: {result}")

    assert "cannot be empty" in result
    logger.info("Empty code validation passed")


def test_python_repl_missing_parameter():
    """Test Python REPL with missing code parameter"""
    logger.info("Testing missing parameter validation...")
    repl = PythonREPL()

    result = repl.run({})
    print(f"\nResult: {result}")

    assert "Missing required parameters" in result
    logger.info("Missing parameter validation passed")


def test_python_repl_error():
    """Test Python REPL with code that raises exception"""
    logger.info("Testing code with exception...")
    repl = PythonREPL()

    test_code = "1 / 0"
    result = repl.run({"code": test_code})
    print(f"\nResult:\n{result}")

    assert "Error:" in result
    assert "ZeroDivisionError" in result
    logger.info("Exception handling passed")


def test_python_repl_restricted_import():
    """Test Python REPL with restricted import"""
    logger.info("Testing restricted import...")
    repl = PythonREPL()

    test_code = "import os\nprint(os.getcwd())"
    result = repl.run({"code": test_code})
    print(f"\nResult:\n{result}")

    assert "Error:" in result
    logger.info("Restricted import test passed")


def test_python_repl_description():
    """Test tool description generation"""
    repl = PythonREPL()
    desc = repl.get_description()

    assert "python" in desc
    assert "code" in desc
    assert "TOOL_CALL:python" in desc
    print(f"\nTool description:\n{desc}")


def test_python_repl_example():
    """Test tool example generation"""
    repl = PythonREPL()
    example = repl.get_example()

    assert example.startswith("[TOOL_CALL:python:")
    assert "code=" in example
    print(f"\nTool example: {example}")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    print("=" * 80)
    print("Test 1: Valid code execution")
    print("=" * 80)
    test_python_repl_success()

    print("\n" + "=" * 80)
    print("Test 2: Empty code validation")
    print("=" * 80)
    test_python_repl_empty_code()

    print("\n" + "=" * 80)
    print("Test 3: Missing parameter validation")
    print("=" * 80)
    test_python_repl_missing_parameter()

    print("\n" + "=" * 80)
    print("Test 4: Code with exception")
    print("=" * 80)
    test_python_repl_error()

    print("\n" + "=" * 80)
    print("Test 5: Restricted import")
    print("=" * 80)
    test_python_repl_restricted_import()

    print("\n" + "=" * 80)
    print("Test 6: Tool description generation")
    print("=" * 80)
    test_python_repl_description()

    print("\n" + "=" * 80)
    print("Test 7: Tool example generation")
    print("=" * 80)
    test_python_repl_example()

    print("\n" + "=" * 80)
    print("All tests passed!")
    print("=" * 80)
