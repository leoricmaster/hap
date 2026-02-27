import sys
import os
# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))

from hap.tools.builtin.memory_tool import MemoryTool


def test_memory_tool():
    memory_tool = MemoryTool(user_id="user123")

    print("=== 添加多个记忆 ===")
    result1 = memory_tool.execute("add", content="用户张三是一名Python开发者，专注于机器学习和数据分析", memory_type="semantic", importance=0.8)
    print(f"记忆1: {result1}")

    result2 = memory_tool.execute("add", content="李四是前端工程师，擅长React和Vue.js开发", memory_type="semantic", importance=0.7)
    print(f"记忆2: {result2}")

    result3 = memory_tool.execute("add", content="王五是产品经理，负责用户体验设计和需求分析", memory_type="semantic", importance=0.6)
    print(f"记忆3: {result3}")

    print("\n=== 搜索特定记忆 ===")
    print("🔍 搜索 '前端工程师':")
    result = memory_tool.execute("search", query="前端工程师", limit=3)
    print(result)

    print("\n=== 记忆摘要 ===")
    result = memory_tool.execute("summary")
    print(result)


if __name__ == "__main__":
    test_memory_tool()