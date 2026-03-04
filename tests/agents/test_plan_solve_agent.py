import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import logging
from dotenv import load_dotenv
from agents.plan_solve_agent import PlanAndSolveAgent
from core.llm import LLMClient
from utils.logging import configure_logging

configure_logging()
logger = logging.getLogger(__name__)


def test_plan_solve_agent():
    """测试 PlanAndSolveAgent 基本功能"""
    # 加载环境变量
    load_dotenv()

    try:
        logger.info("正在初始化 LLM 客户端...")
        llm_client = LLMClient()
        logger.info("LLM 客户端初始化成功")

        logger.info("正在创建 PlanAndSolveAgent...")
        agent = PlanAndSolveAgent(
            name="数学问题解决助手",
            llm=llm_client,
            max_steps=10
        )
        logger.info("PlanAndSolveAgent 创建成功")

        # 运行示例问题
        question = "一个水果店周一卖出了15个苹果。周二卖出的苹果数量是周一的两倍。周三卖出的数量比周二少了5个。请问这三天总共卖出了多少个苹果？"
        logger.info(f"开始处理问题: {question}")
        answer = agent.run(question)
        logger.info(f"最终答案: {answer}")

    except ValueError as e:
        logger.error(f"配置错误: {e}")
    except Exception as e:
        logger.error(f"发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_plan_solve_agent()
