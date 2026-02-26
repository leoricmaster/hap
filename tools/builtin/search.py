import os
from typing import Optional, Any, List, Dict
from ..base import Tool, ToolParameter


class SearchTool(Tool):
    def __init__(self, serpapi_key: Optional[str] = None):
        super().__init__(
            name="search",
            description="一个网页搜索引擎。当你需要回答关于时事、事实以及在你的知识库中找不到的信息时，应使用此工具。"
        )
        self._serpapi_key = serpapi_key or os.getenv("SERPAPI_API_KEY")

    def run(self, parameters: Dict[str, Any]) -> str:
        """
        执行搜索

        Args:
            parameters: 包含query参数的字典

        Returns:
            搜索结果
        """
        query = parameters.get("query", "").strip()
        if not query:
            return "错误：搜索查询不能为空"

        print(f"🔍 正在执行搜索: {query}")

        try:
            return self._search_serpapi(query)
        except Exception as e:
            return f"搜索时发生错误: {str(e)}"

    def _search_serpapi(self, query: str) -> str:
        """使用SerpApi搜索"""
        try:
            from serpapi import SerpApiClient
        except ImportError:
            return "错误：SerpApi未安装，请运行 pip install serpapi"

        params = {
            "engine": "google",
            "q": query,
            "api_key": self._serpapi_key,
            "gl": "cn",
            "hl": "zh-cn",
        }

        client = SerpApiClient(params)
        results = client.get_dict()

        result_text = "🔍 SerpApi Google搜索结果：\n\n"

        # 智能解析：优先寻找最直接的答案
        if "answer_box" in results and "answer" in results["answer_box"]:
            result_text += f"💡 直接答案：{results['answer_box']['answer']}\n\n"

        if "knowledge_graph" in results and "description" in results["knowledge_graph"]:
            result_text += f"📖 知识图谱：{results['knowledge_graph']['description']}\n\n"

        if "organic_results" in results and results["organic_results"]:
            result_text += "🔗 相关结果：\n"
            for i, res in enumerate(results["organic_results"][:3], 1):
                result_text += f"[{i}] {res.get('title', '')}\n"
                result_text += f"    {res.get('snippet', '')}\n"
                result_text += f"    来源: {res.get('link', '')}\n\n"
            return result_text

        return f"对不起，没有找到关于 '{query}' 的信息。"

    def get_parameters(self) -> List[ToolParameter]:
        """获取工具参数定义"""
        return [
            ToolParameter(
                name="input",
                type="string",
                description="搜索查询关键词",
                required=True
            )
        ]