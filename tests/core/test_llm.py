"""LLM client tests"""
from hap.core.llm import LLMClient

from pathlib import Path
from dotenv import load_dotenv

# Load .env when running this file directly
_project_root = Path(__file__).parent.parent.parent
_env_file = _project_root / ".env"
if _env_file.exists():
    load_dotenv(dotenv_path=_env_file)

import logging

logger = logging.getLogger(__name__)


def test_llm_stream_invoke():
    """Test LLM stream_invoke"""
    try:
        logger.info("Initializing LLM client...")
        llm_client = LLMClient()
        logger.info("LLM client initialized")

        example_messages: list[dict[str, str]] = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Introduce yourself."}
        ]

        logger.info("Testing stream_invoke...")
        response_chunks = []
        for chunk in llm_client.stream_invoke(example_messages):
            response_chunks.append(chunk)
            print(chunk, end="")
        print("")
        logger.info(f"stream_invoke completed, received {len(response_chunks)} chunks")

    except ValueError as e:
        logger.error(f"Configuration error: {e}")
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()


def test_llm_invoke():
    """Test LLM invoke (non-streaming)"""
    try:
        logger.info("Initializing LLM client...")
        llm_client = LLMClient()
        logger.info("LLM client initialized")

        example_messages: list[dict[str, str]] = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'Hello, World!'"}
        ]

        logger.info("Testing invoke (non-streaming)...")
        response = llm_client.invoke(example_messages)
        print(f"Response: {response}")
        logger.info(f"invoke completed, response length: {len(response)}")

    except ValueError as e:
        logger.error(f"Configuration error: {e}")
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    test_llm_invoke()
    print("\n" + "-"*80 + "\n")
    test_llm_stream_invoke()
