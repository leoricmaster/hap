from abc import ABC, abstractmethod
from typing import Optional, List, Dict
from .llm import LLMClient
from hap.tools.registry import ToolRegistry


class Agent(ABC):
    """Agent base class with optional tool support."""

    def __init__(
        self,
        name: str,
        llm: LLMClient,
        system_prompt: Optional[str] = None,
        tool_registry: Optional[ToolRegistry] = None
    ):
        self._name = name
        self._llm = llm
        self._system_prompt = system_prompt
        self._tool_registry = tool_registry
        self._history: List[Dict[str, str]] = []

    @abstractmethod
    def run(self, input_text: str, **kwargs) -> str:
        """运行Agent

        Args:
            input_text: 用户输入
            **kwargs: 透传给 LLM 的参数，如 temperature, max_tokens

        Returns:
            Agent 的响应文本
        """
        pass

    def add_message(self, role: str, content: str):
        """添加消息到历史记录"""
        self._history.append({"role": role, "content": content})

    def clear_history(self):
        """清空历史记录"""
        self._history.clear()

    def get_history(self) -> List[Dict[str, str]]:
        """获取历史记录"""
        return self._history.copy()

    def __str__(self) -> str:
        return f"Agent(name={self._name})"

    def __repr__(self) -> str:
        return self.__str__()
