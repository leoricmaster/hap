import json
import re
from typing import Optional, List, Tuple, Dict, Any
from ..core.agent import Agent
from ..core.llm import HelloAgentsLLM
from ..core.message import Message
from ..tools.registry import ToolRegistry

# 默认ReAct提示词模板
DEFAULT_REACT_PROMPT = """你是一个具备推理和行动能力的AI助手。你可以通过思考分析问题，然后调用合适的工具来获取信息，最终给出准确的答案。

## 可用工具
{tools}

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

## 当前任务
**Question:** {question}

## 执行历史
{history}

现在开始你的推理和行动："""

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
        self._current_history: List[str] = []

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
        self._current_history = []
        current_step = 0
        
        print(f"\n🤖 {self.name} 开始处理问题: {input_text}")
        
        while current_step < self._max_steps:
            current_step += 1
            print(f"\n--- 第 {current_step} 步 ---")
            
            # 构建提示词
            tools_desc = self._tool_registry.get_tools_description()
            history_str = "\n".join(self._current_history)
            prompt = self.prompt_template.format(
                tools=tools_desc,
                question=input_text,
                history=history_str
            )
            
            # 调用LLM
            messages = [{"role": "user", "content": prompt}]
            response_text = self.llm.invoke(messages, **kwargs)
            
            if not response_text:
                print("❌ 错误：LLM未能返回有效响应。")
                break
            
            # 解析输出
            thought, action = self._parse_output(response_text)
            
            if thought:
                print(f"🤔 思考: {thought}")
            
            if not action:
                print("⚠️ 警告：未能解析出有效的Action，流程终止。")
                break
            
            # 检查是否完成
            if action.startswith("Finish"):
                final_answer = self._parse_action_input(action)
                print(f"🎉 最终答案: {final_answer}")
                
                # 保存到历史记录
                self.add_message(Message("user", input_text))
                self.add_message(Message("assistant", final_answer))
                
                return final_answer
            
            # 执行工具调用
            tool_name, input_json = self._parse_action(action)
            if not tool_name or input_json is None:
                self._current_history.append("Observation: 无效的Action格式，请检查。")
                continue
            
            print(f"🎬 行动: {tool_name}[{input_json}]")
            
            # 调用工具
            observation = self._tool_registry.execute_tool(tool_name, input_json)
            print(f"👀 观察: {observation}")
            
            # 更新历史
            self._current_history.append(f"Action: {action}")
            self._current_history.append(f"Observation: {observation}")
        
        print("⏰ 已达到最大步数，流程终止。")
        final_answer = "抱歉，我无法在限定步数内完成这个任务。"
        
        # 保存到历史记录
        self.add_message(Message("user", input_text))
        self.add_message(Message("assistant", final_answer))
        
        return final_answer
    
    def _parse_output(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """解析LLM输出，提取思考和行动"""
        # 匹配Thought和Action，忽略前面的星号
        thought_match = re.search(r"Thought:(.*)", text)
        action_match = re.search(r"Action:(.*)", text)
        
        thought = thought_match.group(1).strip() if thought_match else None
        action = action_match.group(1).strip() if action_match else None
        
        # 移除可能存在的前导星号和空格
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
        match = re.match(r"(\w+)\[(.*)\]", action_text)
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
        match = re.match(r"\w+\[(.*)\]", action_text)
        return match.group(1) if match else ""


# 示例代码
if __name__ == "__main__":

    from ..core.llm import HelloAgentsLLM
    from ..tools.registry import ToolRegistry
    from ..tools.builtin.search import SearchTool
    from ..tools.builtin.calculator import CalculatorTool
    from dotenv import load_dotenv
    
    # 加载环境变量
    load_dotenv()
    
    # 初始化LLM
    llm = HelloAgentsLLM()
    
    # 创建工具注册表并注册工具
    tool_registry = ToolRegistry()
    tool_registry.register_tool(SearchTool())
    tool_registry.register_tool(CalculatorTool())
    
    # 创建ReActAgent
    agent = ReActAgent(
        name="ReAct示例助手",
        llm=llm,
        tool_registry=tool_registry,
        max_steps=5
    )
    
    # 运行示例
    question = "华为最新的手机是哪一款？它的主要卖点是什么？"
    agent.run(question)