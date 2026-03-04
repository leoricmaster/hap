import json
import logging
import re
from typing import Optional, Tuple, Dict, Any
from core.agent import Agent
from core.llm import HelloAgentsLLM
from core.message import Message
from tools.registry import ToolRegistry

logger = logging.getLogger(__name__)

# 预编译正则表达式以提高性能
_THOUGHT_PATTERN = re.compile(r"\*\*Thought:\*\*(.*)", re.IGNORECASE)
_ACTION_PATTERN = re.compile(r"\*\*Action:\*\*(.*)", re.IGNORECASE)
_TOOL_PATTERN = re.compile(r"([a-zA-Z0-9_-]+)\[(.*?)\]")  # 非贪婪匹配，支持连字符工具名
_FINISH_ACTION = "Finish"

# 默认系统提示词 - 定义Agent角色和ReAct规则
DEFAULT_SYSTEM_PROMPT = """你是一个具备推理和行动能力的AI助手。你可以通过思考分析问题，然后调用合适的工具来获取信息，最终给出准确的答案。

## 工作流程
请严格按照以下格式进行回应，每次只能执行一个步骤：

**Thought:** 分析当前问题，思考需要采取什么行动。
**Action:** 选择一个行动，格式必须是以下之一：
- `{{tool_name}}[{{input_json}}]` - 调用指定工具，其中input_json是JSON格式的工具参数
- `Finish[最终答案]` - 当你有足够信息给出最终答案时

## 重要提醒
1. 每次回应必须包含Thought和Action两部分
2. 工具调用的格式必须严格遵循：工具名[JSON格式的参数]
3. 只有当你确信有足够信息回答问题时，才使用Finish
4. 如果工具返回的信息不够，继续使用其他工具或相同工具的不同参数

## 示例
- 搜索工具：`search[{{"query": "Python编程语言的特点"}}]`
- 计算器工具：`calculator[{{"a": 10, "b": 5, "operation": "add"}}]`

## 注意事项
- JSON参数中的键值对必须用逗号分隔
- 字符串值必须用双引号包围
- 数字值不需要引号

当收到 Observation 时，请基于新的信息继续推理和行动。"""

# 默认ReAct提示词模板（用于首次用户消息）
DEFAULT_REACT_PROMPT = """## 可用工具
{tools}

## 当前任务
**Question:** {question}

请开始你的推理和行动："""

class ReActAgent(Agent):
    """
    ReAct (Reasoning and Acting) Agent
    
    结合推理和行动的智能体，能够：
    1. 分析问题并制定行动计划
    2. 调用外部工具获取信息
    3. 基于观察结果进行推理
    4. 迭代执行直到得出最终答案
    
    这是一个经典的Agent范式，特别适合需要外部信息的任务。
    """
    
    def __init__(
        self,
        name: str,
        llm: HelloAgentsLLM,
        tool_registry: ToolRegistry,
        system_prompt: Optional[str] = None,
        custom_prompt: Optional[str] = None,
        max_steps: int = 5
    ):
        """
        初始化ReActAgent

        Args:
            name: Agent名称
            llm: LLM实例
            tool_registry: 工具注册表
            system_prompt: 系统提示词
            custom_prompt: 自定义提示词模板
            max_steps: 最大执行步数
        """
        super().__init__(name, llm, system_prompt)
        self._tool_registry = tool_registry
        self._max_steps = max_steps

        # 设置提示词模板：用户自定义优先，否则使用默认模板
        self.prompt_template = custom_prompt if custom_prompt else DEFAULT_REACT_PROMPT
    
    def run(self, input_text: str, **kwargs) -> str:
        """
        运行ReAct Agent

        Args:
            input_text: 用户问题
            **kwargs: 其他参数

        Returns:
            最终答案
        """
        current_step = 0

        logger.info(f"\n🤖 {self.name} 开始处理问题: {input_text}")

        # 清空历史，开始新的对话
        self.clear_history()

        # 1. 添加系统提示词（用户自定义或默认）
        system_content = self.system_prompt if self.system_prompt else DEFAULT_SYSTEM_PROMPT
        self.add_message(Message("system", system_content))

        # 2. 添加首次用户消息（包含工具描述和具体问题）
        tools_desc = self._tool_registry.get_tools_description()
        initial_prompt = self.prompt_template.format(
            tools=tools_desc,
            question=input_text
        )
        self.add_message(Message("user", initial_prompt))

        while current_step < self._max_steps:
            current_step += 1
            logger.info(f"\n--- 第 {current_step} 步 ---")

            # 从 self._history 构建 messages 传给 LLM
            messages = [{"role": m.role, "content": m.content} for m in self._history]
            response_text = self.llm.invoke(messages, **kwargs)

            if not response_text:
                logger.error("❌ 错误：LLM未能返回有效响应。")
                break

            # 解析输出
            thought, action = self._parse_output(response_text)

            if thought:
                logger.info(f"🤔 思考: {thought}")

            if not action:
                logger.warning("⚠️ 警告：未能解析出有效的Action，流程终止。")
                break

            # 添加助手的回复到历史
            self.add_message(Message("assistant", response_text))

            # 检查是否完成
            if action.startswith(_FINISH_ACTION):
                final_answer = self._parse_action_input(action)
                logger.info(f"🎉 最终答案: {final_answer}")
                return final_answer

            # 执行工具调用
            tool_name, input_json = self._parse_action(action)
            if not tool_name or input_json is None:
                # 添加观察结果到历史，让模型继续
                self.add_message(Message("user", "Observation: 无效的Action格式，请检查。"))
                continue

            logger.info(f"🎬 行动: {tool_name}[{input_json}]")

            # 调用工具
            observation = self._tool_registry.execute_tool(tool_name, input_json)
            logger.info(f"👀 观察: {observation}")

            # 添加观察结果到历史
            self.add_message(Message("user", f"Observation: {observation}"))

        logger.warning("⏰ 已达到最大步数，流程终止。")
        final_answer = "抱歉，我无法在限定步数内完成这个任务。"

        # 添加最终结果到历史
        self.add_message(Message("assistant", final_answer))

        return final_answer
    
    def _parse_output(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """解析LLM输出，提取思考和行动"""
        thought_match = _THOUGHT_PATTERN.search(text)
        action_match = _ACTION_PATTERN.search(text)

        thought = thought_match.group(1).strip() if thought_match else None
        action = action_match.group(1).strip() if action_match else None

        # 清理可能的前导星号和空格
        if thought:
            thought = thought.lstrip("* ").strip()
        if action:
            action = action.lstrip("* ").strip()

        return thought, action
    
    def _parse_action(self, action_text: str) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
        """解析行动文本，提取工具名称和输入参数

        Args:
            action_text: 行动文本，格式为 tool_name[json_params]

        Returns:
            Tuple[工具名称, 参数字典]
        """
        match = _TOOL_PATTERN.match(action_text)
        if match:
            tool_name = match.group(1)
            params_str = match.group(2)

            try:
                # 尝试解析JSON格式的参数
                params = json.loads(params_str)
                if isinstance(params, dict):
                    return tool_name, params
                else:
                    # 如果不是字典，尝试包装成字典
                    return tool_name, {"input": str(params)}
            except (json.JSONDecodeError, ValueError):
                # 如果JSON解析失败，将整个参数字符串作为input参数
                return tool_name, {"input": params_str}

        return None, None

    def _parse_action_input(self, action_text: str) -> str:
        """解析行动输入"""
        match = _TOOL_PATTERN.match(action_text)
        return match.group(2) if match else ""

