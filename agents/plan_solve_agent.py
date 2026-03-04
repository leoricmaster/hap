import ast
import logging
import re
from typing import Optional, List, Dict
from core.agent import Agent
from core.llm import HelloAgentsLLM
from core.message import Message

logger = logging.getLogger(__name__)

# 默认规划器提示词模板
DEFAULT_PLANNER_PROMPT = """
你是一个顶级的AI规划专家。你的任务是将用户提出的复杂问题分解成一个由多个简单步骤组成的行动计划。
请确保计划中的每个步骤都是一个独立的、可执行的子任务，并且严格按照逻辑顺序排列。
你的输出必须是一个Python列表，其中每个元素都是一个描述子任务的字符串。

问题: {question}

请严格按照以下格式输出你的计划:
```python
["步骤1", "步骤2", "步骤3", ...]
```
"""

# 默认执行器提示词模板
DEFAULT_EXECUTOR_PROMPT = """
你是一位顶级的AI执行专家。你的任务是严格按照给定的计划，一步步地解决问题。
你将收到原始问题、完整的计划、以及到目前为止已经完成的步骤和结果。
请你专注于解决"当前步骤"，并仅输出该步骤的最终答案，不要输出任何额外的解释或对话。

# 原始问题:
{question}

# 完整计划:
{plan}

# 历史步骤与结果:
{history}

# 当前步骤:
{current_step}

请仅输出针对"当前步骤"的回答:
"""

class Planner:
    """规划器 - 负责将复杂问题分解为简单步骤"""

    def __init__(self, llm_client: HelloAgentsLLM, prompt_template: Optional[str] = None):
        self.llm_client = llm_client
        self.prompt_template = prompt_template if prompt_template else DEFAULT_PLANNER_PROMPT

    def plan(self, question: str, **kwargs) -> List[str]:
        """
        生成执行计划

        Args:
            question: 要解决的问题
            **kwargs: LLM调用参数

        Returns:
            步骤列表
        """
        prompt = self.prompt_template.format(question=question)
        messages = [{"role": "user", "content": prompt}]

        logger.info("--- 正在生成计划 ---")
        response_text = self.llm_client.invoke(messages, **kwargs) or ""
        logger.info(f"LLM 响应:\n{response_text}")

        plan = self._extract_plan(response_text)
        if plan:
            logger.info(f"✅ 成功解析计划，共 {len(plan)} 步")
        else:
            logger.warning("❌ 未能从响应中解析出有效计划")

        return plan

    def _extract_plan(self, response_text: str) -> List[str]:
        """从响应中提取计划列表，支持多种格式"""
        if not response_text:
            return []

        # 尝试多种模式匹配
        patterns = [
            r'```python\s*(.*?)\s*```',  # ```python ... ```
            r'```\s*(.*?)\s*```',         # ``` ... ```
        ]

        candidates = []

        # 从代码块中提取
        for pattern in patterns:
            matches = re.findall(pattern, response_text, re.DOTALL | re.IGNORECASE)
            candidates.extend(matches)

        # 直接尝试整个文本（去除首尾空白）
        candidates.append(response_text.strip())

        for candidate in candidates:
            candidate = candidate.strip()
            try:
                plan = ast.literal_eval(candidate)
                if isinstance(plan, list) and all(isinstance(s, str) and s.strip() for s in plan):
                    return [s.strip() for s in plan if s.strip()]
            except (ValueError, SyntaxError):
                continue

        logger.warning(f"无法从响应中解析计划: {response_text[:200]}...")
        return []

class Executor:
    """执行器 - 负责按计划逐步执行"""

    def __init__(self, llm_client: HelloAgentsLLM, prompt_template: Optional[str] = None):
        self.llm_client = llm_client
        self.prompt_template = prompt_template if prompt_template else DEFAULT_EXECUTOR_PROMPT

    def execute(
        self,
        question: str,
        plan: List[str],
        agent: Optional[Agent] = None,
        max_steps: int = 10,
        **kwargs
    ) -> tuple[str, List[Dict]]:
        """
        按计划执行任务

        Args:
            question: 原始问题
            plan: 执行计划
            agent: 可选的Agent实例，用于记录历史
            max_steps: 最大执行步数
            **kwargs: LLM调用参数

        Returns:
            (最终答案, 步骤执行历史列表)
        """
        # 过滤并限制步骤数
        valid_steps = [s.strip() for s in plan if s and s.strip()]
        steps_to_execute = valid_steps[:max_steps]

        if len(valid_steps) > max_steps:
            logger.warning(f"计划步骤过多({len(valid_steps)}步)，已截断至{max_steps}步")

        history = ""
        final_answer = ""
        step_results = []

        logger.info(f"\n--- 正在执行计划 ({len(steps_to_execute)} 步) ---")

        for i, step in enumerate(steps_to_execute, 1):
            if not step:
                logger.warning(f"步骤 {i} 为空，跳过")
                continue

            logger.info(f"-> 正在执行步骤 {i}/{len(steps_to_execute)}: {step}")

            # 记录计划执行开始
            if agent:
                agent.add_message(Message("assistant", f"**步骤 {i}**: {step}"))

            prompt = self.prompt_template.format(
                question=question,
                plan="\n".join(f"{j+1}. {s}" for j, s in enumerate(steps_to_execute)),
                history=history if history else "无",
                current_step=step
            )
            messages = [{"role": "user", "content": prompt}]

            try:
                response_text = self.llm_client.invoke(messages, **kwargs) or ""

                # 检查结果有效性
                if not response_text.strip():
                    response_text = "[步骤执行返回空结果]"
                    logger.warning(f"步骤 {i} 返回空结果")

            except Exception as e:
                response_text = f"[步骤执行出错: {str(e)}]"
                logger.error(f"步骤 {i} 执行异常: {e}")

            history += f"步骤 {i}: {step}\n结果: {response_text}\n\n"
            final_answer = response_text

            step_results.append({
                "step": i,
                "description": step,
                "result": response_text
            })

            # 记录步骤结果到Agent历史
            if agent:
                agent.add_message(Message("assistant", f"**结果**: {response_text}"))

            logger.info(f"✅ 步骤 {i} 已完成")

        return final_answer, step_results


class PlanAndSolveAgent(Agent):
    """
    Plan and Solve Agent - 分解规划与逐步执行的智能体

    这个Agent能够：
    1. 将复杂问题分解为简单步骤
    2. 按照计划逐步执行
    3. 维护执行历史和上下文
    4. 得出最终答案

    特别适合多步骤推理、数学问题、复杂分析等任务。
    """

    def __init__(
        self,
        name: str,
        llm: HelloAgentsLLM,
        system_prompt: Optional[str] = None,
        custom_prompts: Optional[Dict[str, str]] = None,
        max_steps: int = 10
    ):
        """
        初始化PlanAndSolveAgent

        Args:
            name: Agent名称
            llm: LLM实例
            system_prompt: 系统提示词
            custom_prompts: 自定义提示词模板 {"planner": "", "executor": ""}
            max_steps: 最大执行步数
        """
        super().__init__(name, llm, system_prompt)
        self.max_steps = max_steps

        # 设置提示词模板：用户自定义优先，否则使用默认模板
        if custom_prompts:
            planner_prompt = custom_prompts.get("planner")
            executor_prompt = custom_prompts.get("executor")
        else:
            planner_prompt = None
            executor_prompt = None

        self.planner = Planner(self.llm, planner_prompt)
        self.executor = Executor(self.llm, executor_prompt)

    def run(self, input_text: str, **kwargs) -> str:
        """
        运行Plan and Solve Agent

        Args:
            input_text: 要解决的问题
            **kwargs: 其他参数

        Returns:
            最终答案
        """
        logger.info(f"\n🤖 {self.name} 开始处理问题: {input_text}")

        # 清空历史，开始新的对话
        self.clear_history()

        # 添加系统提示词
        if self.system_prompt:
            self.add_message(Message("system", self.system_prompt))

        # 添加用户问题
        self.add_message(Message("user", input_text))

        # 1. 生成计划
        plan = self.planner.plan(input_text, **kwargs)
        if not plan:
            final_answer = "无法生成有效的行动计划，任务终止。"
            logger.warning(f"任务终止: {final_answer}")

            self.add_message(Message("assistant", final_answer))
            return final_answer

        # 记录生成的计划
        plan_text = "\n".join(f"{i+1}. {step}" for i, step in enumerate(plan))
        self.add_message(Message("assistant", f"**执行计划**:\n{plan_text}"))

        # 2. 执行计划
        final_answer, step_results = self.executor.execute(
            input_text,
            plan,
            agent=self,
            max_steps=self.max_steps,
            **kwargs
        )

        logger.info(f"\n--- 任务完成 ---\n最终答案: {final_answer}")

        # 添加最终答案
        self.add_message(Message("assistant", f"**最终答案**: {final_answer}"))

        return final_answer

