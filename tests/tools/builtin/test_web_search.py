"""Web search tool tests"""
import sys
from pathlib import Path

# Add project root to Python path
_project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(_project_root / "src"))

# Direct import to avoid loading other problematic modules
from hap.tools.builtin.web_search import WebSearch
from hap.core.exceptions import ToolException

from dotenv import load_dotenv

# Load .env when running this file directly
_env_file = _project_root / ".env"
if _env_file.exists():
    load_dotenv(dotenv_path=_env_file)

import logging

logger = logging.getLogger(__name__)


def test_web_search_success():
    """Test web search with valid query"""
    try:
        logger.info("Initializing WebSearch tool...")
        search_tool = WebSearch()
        logger.info("WebSearch tool initialized")

        test_query = "Python programming language"
        logger.info(f"Testing search with query: '{test_query}'")

        result = search_tool.run({"query": test_query})
        print(f"\nSearch Result:\n{result}")
        logger.info("Search completed successfully")

        # Verify result contains expected content
        assert "Tavily AI Search Results:" in result
        logger.info("Result validation passed")

    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        raise


def test_web_search_empty_query():
    """Test web search with empty query should raise exception"""
    try:
        logger.info("Testing empty query validation...")
        search_tool = WebSearch()

        try:
            search_tool.run({"query": "   "})
            logger.error("Should have raised ToolException for empty query")
            raise AssertionError("Expected ToolException was not raised")
        except Exception as e:
            if "Search query cannot be empty" in str(e):
                logger.info("Empty query validation passed")
                print(f"Expected error caught: {e}")
            else:
                raise

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        raise


def test_web_search_missing_parameter():
    """Test web search with missing query parameter"""
    try:
        logger.info("Testing missing parameter validation...")
        search_tool = WebSearch()

        try:
            search_tool.run({})
            logger.error("Should have raised ToolException for missing parameter")
            raise AssertionError("Expected ToolException was not raised")
        except Exception as e:
            if "Missing required parameters" in str(e):
                logger.info("Missing parameter validation passed")
                print(f"Expected error caught: {e}")
            else:
                raise

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        raise


def test_web_search_custom_results_count():
    """Test web search with custom max_results"""
    try:
        logger.info("Testing custom max_results...")
        search_tool = WebSearch(max_results=3)
        logger.info("WebSearch tool initialized with max_results=3")

        test_query = "machine learning"
        logger.info(f"Testing search with query: '{test_query}'")

        result = search_tool.run({"query": test_query})
        print(f"\nSearch Result:\n{result}")
        logger.info("Search completed successfully")

    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    print("=" * 80)
    print("Test 1: Valid search query")
    print("=" * 80)
    test_web_search_success()

    print("\n" + "=" * 80)
    print("Test 2: Empty query validation")
    print("=" * 80)
    test_web_search_empty_query()

    print("\n" + "=" * 80)
    print("Test 3: Missing parameter validation")
    print("=" * 80)
    test_web_search_missing_parameter()

    print("\n" + "=" * 80)
    print("Test 4: Custom results count")
    print("=" * 80)
    test_web_search_custom_results_count()

    print("\n" + "=" * 80)
    print("All tests passed!")
    print("=" * 80)
