import os
import logging
from typing import Optional, Any, List, Dict
from hap.tools.base import Tool, ToolParameter
from hap.core.exceptions import ToolException

logger = logging.getLogger(__name__)


class WebSearch(Tool):
    def __init__(self, tavily_key: Optional[str] = None):
        super().__init__(
            name="search",
            description="一个网页搜索引擎。当你需要回答关于时事、事实以及在你的知识库中找不到的信息时，应使用此工具。"
        )
        self._tavily_key = tavily_key or os.getenv("TAVILY_API_KEY")
        self._tavily_client = None

    def get_parameters(self) -> List[ToolParameter]:
        """获取工具参数定义"""
        return [
            ToolParameter(
                name="query",
                type="string",
                description="搜索查询关键词",
                required=True
            )
        ]

    def run(self, parameters: Dict[str, Any]) -> str:
        """
        执行搜索

        Args:
            parameters: 包含 query 参数的字典

        Returns:
            搜索结果

        Raises:
            ToolException: 搜索执行失败
        """
        query = parameters.get("query", "").strip()

        if not self._validate_parameters(parameters):
            missing = [p.name for p in self.get_parameters() if p.required and p.name not in parameters]
            logger.warning(f"缺少必需参数: {missing}")
            raise ToolException(f"缺少必需参数: {', '.join(missing)}")

        if not query:
            logger.warning("搜索查询为空")
            raise ToolException("搜索查询不能为空")

        logger.info(f"执行搜索: {query}")

        try:
            result = self._search_tavily(query)
            logger.info("搜索完成")
            return result
        except ToolException:
            raise
        except Exception as e:
            logger.error(f"搜索执行失败: {e}")
            raise ToolException(f"搜索失败: {str(e)}") from e

    def _search_tavily(self, query: str) -> str:
        """使用 Tavily 搜索"""
        if not self._tavily_key:
            logger.error("Tavily API Key 未配置")
            raise ToolException(
                "未配置 Tavily API Key，请设置 TAVILY_API_KEY 环境变量"
            )

        try:
            from tavily import TavilyClient
        except ImportError as e:
            logger.error("tavily-python 未安装")
            raise ToolException(
                "tavily 未安装，请运行 pip install tavily-python"
            ) from e

        # 延迟初始化 client
        if self._tavily_client is None:
            self._tavily_client = TavilyClient(api_key=self._tavily_key)
            logger.debug("TavilyClient 初始化完成")

        try:
            logger.debug(f"调用 Tavily API: {query}")
            response = self._tavily_client.search(
                query=query,
                search_depth="basic",
                include_answer=True,
                max_results=3
            )
        except Exception as e:
            logger.error(f"Tavily API 请求失败: {e}")
            raise ToolException(f"Tavily API 请求失败: {str(e)}") from e

        result_text = "🎯 Tavily AI 搜索结果：\n\n"

        # 优先显示 AI 总结的答案
        answer = response.get("answer")
        if answer:
            result_text += f"💡 AI 总结：{answer}\n\n"
            logger.debug(f"获取到 AI 总结，长度: {len(answer)}")

        # 显示搜索结果
        results = response.get("results", [])
        if results:
            result_text += "🔗 相关结果：\n"
            for i, item in enumerate(results[:3], 1):
                result_text += f"[{i}] {item.get('title', '')}\n"
                content = item.get('content', '')
                result_text += f"    {content[:200]}...\n" if len(content) > 200 else f"    {content}\n"
                result_text += f"    来源: {item.get('url', '')}\n\n"
            logger.debug(f"获取到 {len(results)} 条结果")
            return result_text

        logger.warning(f"未找到关于 '{query}' 的信息")
        return f"对不起，没有找到关于 '{query}' 的信息。"
