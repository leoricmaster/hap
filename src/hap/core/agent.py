from abc import ABC, abstractmethod
from typing import Optional
from .llm import LLMClient

class Agent(ABC):
    """Agent基类"""

    def __init__(
        self,
        name: str,
        llm: LLMClient,
        system_prompt: Optional[str] = None
    ):
        self.name = name
        self.llm = llm
        self.system_prompt = system_prompt
        self._history: list[dict] = []
        if system_prompt:
            self._history.append({"role": "system", "content": system_prompt})

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

    def get_history(self) -> list[dict]:
        """获取历史记录"""
        return self._history.copy()

    def __str__(self) -> str:
        return f"Agent(name={self.name})"
    
    def __repr__(self) -> str:
        return self.__str__()
