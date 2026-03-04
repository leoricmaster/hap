from typing import TYPE_CHECKING, Any

# 类型检查时导入，避免运行时导入
if TYPE_CHECKING:
    from .react_agent import ReActAgent
    from .plan_solve_agent import PlanAndSolveAgent
    from .reflection_agent import ReflectionAgent

# 声明这些属性存在，用于静态分析工具
ReActAgent: Any = None
PlanAndSolveAgent: Any = None
ReflectionAgent: Any = None

def __getattr__(name):
    if name == "ReActAgent":
        from .react_agent import ReActAgent
        return ReActAgent
    elif name == "PlanAndSolveAgent":
        from .plan_solve_agent import PlanAndSolveAgent
        return PlanAndSolveAgent
    elif name == "ReflectionAgent":
        from .reflection_agent import ReflectionAgent
        return ReflectionAgent
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "ReActAgent",
    "PlanAndSolveAgent",
    "ReflectionAgent"
]