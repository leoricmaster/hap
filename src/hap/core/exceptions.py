"""HAP 框架统一异常体系"""


class HAPException(Exception):
    """HAP 框架基础异常类"""
    pass


class LLMException(HAPException):
    """LLM 调用相关异常的基类"""
    pass


class LLMConfigException(LLMException):
    """LLM 配置错误"""
    pass


class LLMResponseException(LLMException):
    """LLM 响应处理错误"""
    pass


class AgentException(HAPException):
    """Agent 执行相关异常的基类"""
    pass


class ToolException(HAPException):
    """工具调用相关异常的基类"""
    pass


class MemoryException(HAPException):
    """记忆系统相关异常的基类"""
    pass
