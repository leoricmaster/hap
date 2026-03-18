import logging
from typing import Optional, List, Dict, Any
from jinja2 import Template
from hap.core.agent import Agent
from hap.core.llm import LLMClient

logger = logging.getLogger(__name__)

DEFAULT_PROMPTS = {
    "initial": """
请根据以下要求完成任务：

任务: {{ task }}

请提供一个完整、准确的回答。
""",
    "reflect": """
请仔细审查以下回答，并找出可能的问题或改进空间：

# 原始任务:
{{ task }}

# 当前回答:
{{ content }}

请分析这个回答的质量，指出不足之处，并提出具体的改进建议。
如果回答已经很好，请明确回答"无需改进"或"NO_IMPROVEMENT_NEEDED"。
""",
    "refine": """
请根据反馈意见改进你的回答：

# 原始任务:
{{ task }}

# 上一轮回答:
{{ last_attempt }}

# 反馈意见:
{{ feedback }}

请提供一个改进后的回答。
"""
}

class Memory:
    """
    简单的短期记忆模块，用于存储智能体的行动与反思轨迹。
    """
    def __init__(self):
        self.records: List[Dict[str, Any]] = []

    def add_record(self, record_type: str, content: str):
        """向记忆中添加一条新记录"""
        self.records.append({"type": record_type, "content": content})
        # 只打印类型，避免输出过长内容
        content_preview = content[:50] + "..." if len(content) > 50 else content
        logger.debug("记忆已更新，新增一条 '%s' 记录：%s", record_type, content_preview)

    def get_last_execution(self) -> str:
        """获取最近一次的执行结果"""
        for record in reversed(self.records):
            if record['type'] == 'execution':
                return record['content']
        return ""

    def clear(self):
        """清空所有记录"""
        self.records.clear()


class ReflectionAgent(Agent):
    """
    Reflection Agent - 自我反思与迭代优化的智能体

    这个Agent能够：
    1. 执行初始任务
    2. 对结果进行自我反思
    3. 根据反思结果进行优化
    4. 迭代改进直到满意

    特别适合代码生成、文档写作、分析报告等需要迭代优化的任务。

    支持多种专业领域的提示词模板，用户可以自定义或使用内置模板。
    """

    def __init__(
        self,
        name: str,
        llm: LLMClient,
        system_prompt: Optional[str] = None,
        max_iterations: int = 3,
        custom_prompts: Optional[Dict[str, str]] = None
    ):
        """
        初始化ReflectionAgent

        Args:
            name: Agent名称
            llm: LLM实例
            system_prompt: 系统提示词
            max_iterations: 最大迭代次数
            custom_prompts: 自定义提示词模板 {"initial": "", "reflect": "", "refine": ""}
        """
        super().__init__(name, llm, system_prompt)
        self.max_iterations = max_iterations
        self.memory = Memory()

        # 设置提示词模板：用户自定义优先，否则使用默认模板
        self.prompts = {**DEFAULT_PROMPTS, **(custom_prompts or {})}
    
    def run(self, input_text: str, **kwargs) -> str:
        """
        运行Reflection Agent

        Args:
            input_text: 任务描述
            **kwargs: 其他参数

        Returns:
            最终优化后的结果
        """
        logger.info("🤖 %s 开始处理任务: %s", self._name, input_text)

        # 重置记忆
        self.memory.clear()

        # 1. 初始执行
        logger.info("--- 正在进行初始尝试 ---")
        initial_prompt = Template(self.prompts["initial"]).render(task=input_text)
        current_result = self._get_llm_response(initial_prompt, **kwargs)
        self.memory.add_record("execution", current_result)

        # 2. 迭代循环：反思与优化
        for i in range(self.max_iterations):
            logger.info("--- 第 %d/%d 轮迭代 ---", i+1, self.max_iterations)

            # a. 反思
            logger.info("-> 正在进行反思...")
            reflect_prompt = Template(self.prompts["reflect"]).render(
                task=input_text,
                content=current_result
            )
            feedback = self._get_llm_response(reflect_prompt, **kwargs)
            self.memory.add_record("reflection", feedback)

            # b. 检查是否需要停止
            feedback_lower = feedback.lower()
            stop_signals = [
                "无需改进",
                "no need for improvement",
                "no_improvement_needed",
                "perfect",
                "excellent",
                "已经很好",
                "非常好",
                "无需修改"
            ]
            if any(signal in feedback_lower for signal in stop_signals):
                logger.info("✅ 反思认为结果已无需改进，任务完成。")
                break

            # c. 优化
            logger.info("-> 正在进行优化...")
            refine_prompt = Template(self.prompts["refine"]).render(
                task=input_text,
                last_attempt=current_result,
                feedback=feedback
            )
            current_result = self._get_llm_response(refine_prompt, **kwargs)
            self.memory.add_record("execution", current_result)

        logger.info("--- 任务完成 ---\n最终结果:\n%s", current_result)

        # 保存到历史记录
        self.add_message("user", input_text)
        self.add_message("assistant", current_result)

        return current_result
    
    def _get_llm_response(self, prompt: str, **kwargs) -> str:
        """调用LLM并获取完整响应"""
        messages = []
        # 添加系统提示词（如果存在）
        if self._system_prompt:
            messages.append({"role": "system", "content": self._system_prompt})
        messages.append({"role": "user", "content": prompt})

        # 使用非流式调用，直接获取完整响应
        return self._llm.invoke(messages=messages, **kwargs)
