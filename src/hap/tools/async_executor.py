import asyncio
import concurrent.futures
from typing import Dict, Any, List
from .registry import ToolRegistry


class AsyncToolExecutor:
    """异步工具执行器"""

    def __init__(self, registry: ToolRegistry, max_workers: int = 4):
        self._registry = registry
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)

    async def execute_tool_async(self, tool_name: str, tool_params: Dict[str, Any]) -> str:
        """异步执行单个工具"""
        def _execute():
            return self._registry.execute_tool(tool_name, tool_params)

        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(self._executor, _execute)
            return result
        except Exception as e:
            return f"❌ 工具 '{tool_name}' 异步执行失败: {e}"

    async def execute_tools_parallel(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        并行执行多个工具
        
        Args:
            tasks: 任务列表，每个任务包含 tool_name: str 和 tool_params: dict
            
        Returns:
            执行结果列表，包含任务信息和结果
        """
        print(f"🚀 开始并行执行 {len(tasks)} 个工具任务")

        async def run_task(i: int, task: dict[str, str], coro):
            try:
                result = await coro
                print(f"✅ 任务 {i+1} 完成: {task['tool_name']}")
                return {
                    "task_id": i,
                    "tool_name": task["tool_name"],
                    "tool_params": task["tool_params"],
                    "result": result,
                    "status": "success"
                }
            except Exception as e:
                print(f"❌ 任务 {i+1} 失败: {task['tool_name']} - {e}")
                return {
                    "task_id": i,
                    "tool_name": task["tool_name"],
                    "tool_params": task["tool_params"],
                    "result": str(e),
                    "status": "error"
                }

        # 创建异步任务
        async_tasks = []
        for i, task in enumerate(tasks):
            tool_name = task.get("tool_name")
            tool_params = task.get("tool_params", {})
            
            if not tool_name:
                print(f"⚠️ 任务 {i+1} 缺少 'tool_name'，跳过")
                continue
                
            print(f"📝 创建任务 {i+1}: {tool_name}")
            async_task = self.execute_tool_async(tool_name, tool_params)
            async_tasks.append((i, task, async_task))

        results = await asyncio.gather(*[
            run_task(i, task, coro) for i, task, coro in async_tasks
        ])
        results = sorted(results, key=lambda x: x["task_id"])
        
        print(f"🎉 并行执行完成，成功: {sum(1 for r in results if r['status'] == 'success')}/{len(results)}")
        return results

    async def execute_tools_batch(self, tool_name: str, input_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        批量执行同一个工具
        
        Args:
            tool_name: 工具名称
            input_list: 输入参数字典列表
            
        Returns:
            执行结果列表
        """
        tasks = [
            {"tool_name": tool_name, "tool_params": tool_params}
            for tool_params in input_list
        ]
        return await self.execute_tools_parallel(tasks)

    def close(self):
        """关闭执行器"""
        self._executor.shutdown(wait=True)
        print("🔒 异步工具执行器已关闭")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.close()


# 便捷函数
async def run_parallel_tools(registry: ToolRegistry, tasks: List[Dict[str, Any]], max_workers: int = 4) -> List[Dict[str, Any]]:
    """
    便捷函数：并行执行多个工具
    
    Args:
        registry: 工具注册表
        tasks: 任务列表
        max_workers: 最大工作线程数
        
    Returns:
        执行结果列表
    """
    async with AsyncToolExecutor(registry, max_workers) as executor:
        return await executor.execute_tools_parallel(tasks)


async def run_batch_tool(registry: ToolRegistry, tool_name: str, input_list: List[Dict[str, Any]], max_workers: int = 4) -> List[Dict[str, Any]]:
    """
    便捷函数：批量执行同一个工具
    
    Args:
        registry: 工具注册表
        tool_name: 工具名称
        input_list: 输入参数字典列表
        max_workers: 最大工作线程数
        
    Returns:
        执行结果列表
    """
    async with AsyncToolExecutor(registry, max_workers) as executor:
        return await executor.execute_tools_batch(tool_name, input_list)


# 示例函数
async def demo_parallel_execution():
    """演示并行执行的示例"""
    from .base import Tool, ToolParameter
    import time
    class SlowTool(Tool):
        """模拟慢速工具，用于演示并行优势"""
        def __init__(self, delay: float = 1.0):
            super().__init__(
                name="slow_tool",
                description=f"模拟耗时{delay}秒的工具"
            )
            self._delay = delay

        def run(self, parameters: dict[str, Any]) -> str:
            task_name = parameters.get("task_name")
            time.sleep(self._delay)
            return f"{task_name} 完成（耗时{self._delay}秒）"

        def get_parameters(self) -> List[ToolParameter]:
            return [ToolParameter(name="task_name", type="string", description="任务名称", required=True)]

    from .registry import ToolRegistry

    registry = ToolRegistry()
    slow_tool = SlowTool(delay=1.0)
    registry.register_tool(slow_tool)

    tasks = [
        {"tool_name": "slow_tool", "tool_params": {"task_name": "任务1"}},
        {"tool_name": "slow_tool", "tool_params": {"task_name": "任务2"}},
        {"tool_name": "slow_tool", "tool_params": {"task_name": "任务3"}},
        {"tool_name": "slow_tool", "tool_params": {"task_name": "任务4"}},
    ]

    print("\n⏱️ 测试并行执行（4个任务，每个1秒）...")
    start = time.time()
    results = await run_parallel_tools(registry, tasks)
    parallel_time = time.time() - start

    print(f"\n⏱️ 测试串行执行（4个任务，每个1秒）...")
    start = time.time()
    for task in tasks:
        registry.execute_tool(task["tool_name"], task["tool_params"])
    serial_time = time.time() - start

    print("\n📊 执行时间对比:")
    print(f"   并行执行: {parallel_time:.2f}秒")
    print(f"   串行执行: {serial_time:.2f}秒")
    print(f"   理论加速: {serial_time/parallel_time:.1f}x")

    print("\n📋 并行执行结果:")
    for result in results:
        print(f"   ✅ {result['tool_params']} → {result['result']}")

    return results


if __name__ == "__main__":
    asyncio.run(demo_parallel_execution())