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

    @abstractmethod
    def run(self, parameters: Dict[str, Any]) -> Any:
        """执行工具

        实现提示：建议在方法开头调用 self._validate_parameters(parameters) 验证参数

        Args:
            parameters: 工具参数字典

        Returns:
            工具执行结果任意类型
        """
        pass
    
    def _validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """验证参数（私有方法，子类可在 run 中调用）"""
        required_params = [p.name for p in self.get_parameters() if p.required]
        return all(param in parameters for param in required_params)
    
    def __str__(self) -> str:
        return f"Tool(name={self.name})"
    
    def __repr__(self) -> str:
        return self.__str__()