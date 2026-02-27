from typing import Optional, Any, Callable, Dict
from .base import Tool

class ToolRegistry:
    """
    提供工具的注册、管理和执行功能。
    """

    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def register_tool(self, tool: Tool):
        """
        注册Tool对象

        Args:
            tool: Tool实例
        """
        if tool.name in self._tools:
            print(f"⚠️ 警告：工具 '{tool.name}' 已存在，将被覆盖。")

        self._tools[tool.name] = tool
        print(f"✅ 工具 '{tool.name}' 已注册。")

    def unregister_tool(self, name: str):
        """注销工具"""
        if name in self._tools:
            del self._tools[name]
            print(f"🗑️ 工具 '{name}' 已注销。")
        else:
            print(f"⚠️ 工具 '{name}' 不存在。")

    def get_tool(self, name: str) -> Optional[Tool]:
        """获取Tool对象"""
        return self._tools.get(name)

    def get_tools_description(self) -> str:
        """
        获取所有可用工具的格式化描述字符串

        Returns:
            工具描述字符串，用于构建提示词
        """
        descriptions = []

        for tool in self._tools.values():
            descriptions.append(f"- {tool.name}: {tool.description}")

        return "\n".join(descriptions) if descriptions else "暂无可用工具"

    def execute_tool(self, tool_name: str, input_json: Dict[str, Any]) -> str:
        """
        执行工具

        Args:
            name: 工具名称
            input_params: 输入参数字典

        Returns:
            工具执行结果
        """
        if tool_name in self._tools:
            tool = self._tools[tool_name]
            try:
                return tool.run(input_json)
            except Exception as e:
                return f"错误：执行工具 '{tool_name}' 时发生异常: {str(e)}"
        else:
            return f"错误：未找到名为 '{tool_name}' 的工具。"

    def clear(self):
        """清空所有工具"""
        self._tools.clear()
        print("🧹 所有工具已清空。")


# 示例函数
def demo_tool_usage():
    """演示工具的使用"""
    from .builtin.search import SearchTool
    from .builtin.calculator import CalculatorTool
    from dotenv import load_dotenv
    load_dotenv()

    registry = ToolRegistry()
    registry.register_tool(SearchTool())
    registry.register_tool(CalculatorTool())

    # 单参数工具示例
    result = registry.execute_tool("search", {"input": "英伟达最新的GPU型号是什么"})
    print("\n🔍 中文搜索结果:")
    print(result[:100] + "..." if len(result) > 100 else result)
    
    # 多参数工具示例
    result = registry.execute_tool("calculator", {"a": 15, "b": 3, "operation": "divide"})
    print("\n🧮 计算器结果:")
    print(result)

if __name__ == "__main__":
    demo_tool_usage()