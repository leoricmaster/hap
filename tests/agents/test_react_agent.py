import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import logging
from dotenv import load_dotenv
from agents.react_agent import ReActAgent
from core.llm import LLMClient
from tools.registry import ToolRegistry
from tools.builtin.search import SearchTool
from tools.builtin.calculator import CalculatorTool
from utils.logging import configure_logging

configure_logging()
logger = logging.getLogger(__name__)


def test_react_agent():
    """测试 ReActAgent 基本功能"""
    # 加载环境变量
    load_dotenv()

    try:
        logger.info("正在初始化 LLM 客户端...")
        llm = LLMClient()
        logger.info("LLM 客户端初始化成功")

        logger.info("正在注册工具...")
        tool_registry = ToolRegistry()
        tool_registry.register_tool(SearchTool())
        tool_registry.register_tool(CalculatorTool())
        logger.info("工具注册成功")

        logger.info("正在创建 ReActAgent...")
        agent = ReActAgent(
            name="ReAct示例助手",
            llm=llm,
            tool_registry=tool_registry,
            max_steps=5
        )
        logger.info("ReActAgent 创建成功")

        # 运行示例
        question = "华为最新的手机是哪一款？它的主要卖点是什么？"
        logger.info(f"开始处理问题: {question}")
        result = agent.run(question)
        logger.info(f"最终结果: {result}")

    except ValueError as e:
        logger.error(f"配置错误: {e}")
    except Exception as e:
        logger.error(f"发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_react_agent()
