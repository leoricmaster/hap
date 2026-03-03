import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import logging
from core.llm import HelloAgentsLLM
from utils.logging import configure_logging

configure_logging()
logger = logging.getLogger(__name__)


def test_llm_basic():
    """测试 LLM 基本功能"""
    try:
        logger.info("正在初始化 LLM 客户端...")
        llm_client = HelloAgentsLLM()
        logger.info("LLM 客户端初始化成功")

        example_messages: list[dict[str, str]] = [
            {"role": "system", "content": "You are a helpful assistant that writes Python code."},
            {"role": "user", "content": "写一个快速排序算法"}
        ]

        logger.info("--- 调用LLM ---")
        for chunk in llm_client.think(example_messages):
            print(chunk, end="")
        print("\n")
        logger.info("\n--- LLM 响应结束 ---")

    except ValueError as e:
        logger.error(f"配置错误: {e}")
    except Exception as e:
        logger.error(f"发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    test_llm_basic()
