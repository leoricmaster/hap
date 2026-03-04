import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import logging
from dotenv import load_dotenv
from agents.reflection_agent import ReflectionAgent
from core.llm import LLMClient
from utils.logging import configure_logging

configure_logging()
logger = logging.getLogger(__name__)


def test_reflection_agent():
    """测试 ReflectionAgent 基本功能"""
    # 加载环境变量
    load_dotenv()

    try:
        logger.info("正在初始化 LLM 客户端...")
        llm = LLMClient()
        logger.info("LLM 客户端初始化成功")

        logger.info("正在创建 ReflectionAgent...")
        agent = ReflectionAgent(
            name="代码优化助手",
            llm=llm,
            max_iterations=2
        )
        logger.info("ReflectionAgent 创建成功")

        # 运行示例
        task = "编写一个Python函数，找出1到n之间所有的素数 (prime numbers)。"
        logger.info(f"开始处理任务: {task}")
        result = agent.run(task)
        logger.info(f"最终结果: {result}")

    except ValueError as e:
        logger.error(f"配置错误: {e}")
    except Exception as e:
        logger.error(f"发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_reflection_agent()
