from abc import ABC, abstractmethod
from typing import Any, List, Dict
from pydantic import BaseModel


class ToolParameter(BaseModel):
    """工具参数定义"""
    name: str
    type: str
    description: str
    required: bool = True
    default: Any = None
    example: Any = None


class Tool(ABC):
    """工具基类"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    def get_parameters(self) -> List[ToolParameter]:
        """获取工具参数定义"""
        pass

    def run(self, parameters: Dict[str, Any]) -> Any:
        """
        执行工具

        1. 验证参数
        2. 调用子类实现的 _execute 执行具体逻辑

        Args:
            parameters: 工具参数字典

        Returns:
            工具执行结果
        """
        # 参数验证
        missing = [p.name for p in self.get_parameters() if p.required and p.name not in parameters]
        if missing:
            return f"Error: Missing required parameters: {', '.join(missing)}"

        # 执行具体逻辑
        return self._execute(parameters)

    @abstractmethod
    def _execute(self, parameters: Dict[str, Any]) -> Any:
        """
        执行工具具体逻辑（子类必须实现）

        Args:
            parameters: 已验证的工具参数字典

        Returns:
            工具执行结果任意类型
        """
        pass

    def _validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """验证参数（私有方法，子类可在 _execute 中调用）"""
        required_params = [p.name for p in self.get_parameters() if p.required]
        return all(param in parameters for param in required_params)

    def get_description(self) -> str:
        """
        Get formatted tool description string with parameters and usage example.

        Returns:
            Tool description string for building prompts
        """
        lines = [f"### {self.name}", self.description]

        params = self.get_parameters()
        if params:
            lines.append("Parameters:")
            for param in params:
                required_mark = " (required)" if param.required else " (optional)"
                default_info = f", default: {param.default}" if param.default is not None else ""
                lines.append(f"  - {param.name}: {param.type}{required_mark} - {param.description}{default_info}")

            example = self.get_example()
            lines.append(f"Example: {example}")
        else:
            lines.append("Parameters: none")

        return "\n".join(lines)

    def get_example(self) -> str:
        """
        Generate tool usage example.

        Returns:
            Example string in format [TOOL_CALL:tool_name:param1=value1,...]
        """
        params = self.get_parameters()
        if not params:
            return f"[TOOL_CALL:{self.name}]"

        example_params = []
        for param in params:
            if param.example is not None:
                value = param.example
            elif param.default is not None:
                value = param.default
            elif param.type == "number":
                value = 123
            elif param.type == "string":
                value = "example text"
            else:
                value = "value"
            example_params.append(f"{param.name}={value}")

        return f"[TOOL_CALL:{self.name}:{','.join(example_params)}]"

    def __str__(self) -> str:
        return f"Tool(name={self.name})"

    def __repr__(self) -> str:
        return self.__str__()