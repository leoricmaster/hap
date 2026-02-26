from typing import Any, List, Dict
from ..base import Tool, ToolParameter


class CalculatorTool(Tool):
    """一个支持多参数的计算器工具示例"""
    
    def __init__(self):
        super().__init__(
            name="calculator",
            description="执行基本数学运算，支持多参数输入"
        )
    
    def run(self, parameters: Dict[str, Any]) -> str:
        """
        执行计算
        
        Args:
            parameters: 包含操作数的字典
            
        Returns:
            计算结果
        """
        # 获取操作数
        a = parameters.get("a")
        b = parameters.get("b")
        operation = parameters.get("operation", "add")
        
        # 验证参数
        if a is None or b is None:
            return "错误：需要提供参数 'a' 和 'b'"
        
        try:
            a = float(a)
            b = float(b)
        except ValueError:
            return "错误：参数 'a' 和 'b' 必须是数字"
        
        # 执行运算
        if operation == "add":
            result = a + b
            op_symbol = "+"
        elif operation == "subtract":
            result = a - b
            op_symbol = "-"
        elif operation == "multiply":
            result = a * b
            op_symbol = "*"
        elif operation == "divide":
            if b == 0:
                return "错误：除数不能为零"
            result = a / b
            op_symbol = "/"
        else:
            return f"错误：不支持的操作 '{operation}'"
        
        return f"{a} {op_symbol} {b} = {result}"
    
    def get_parameters(self) -> List[ToolParameter]:
        """获取工具参数定义"""
        return [
            ToolParameter(
                name="a",
                type="number",
                description="第一个操作数",
                required=True
            ),
            ToolParameter(
                name="b",
                type="number",
                description="第二个操作数",
                required=True
            ),
            ToolParameter(
                name="operation",
                type="string",
                description="运算类型：add（加法）、subtract（减法）、multiply（乘法）、divide（除法）",
                required=False,
                default="add"
            )
        ]