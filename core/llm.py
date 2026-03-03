import os
import logging
from openai import OpenAI
from dotenv import load_dotenv
from typing import Optional, Iterator
from .exceptions import LLMException

load_dotenv()

logger = logging.getLogger(__name__)

class HelloAgentsLLM:
    def __init__(
            self,
            api_key: Optional[str] = None,
            base_url: Optional[str] = None,
            model: Optional[str] = None,
            temperature: float = 0.7,
            max_tokens: Optional[int] = None,
            timeout: Optional[int] = None
        ):
        """
        初始化客户端。优先使用传入参数，如果未提供，则从环境变量加载。

        Args:
            
            api_key: API密钥，如未提供则从 LLM_API_KEY 读取
            base_url: 服务地址，如未提供则从 LLM_BASE_URL 读取
            model: 模型名称，如未提供则从 LLM_MODEL_ID 读取
            temperature: 温度参数
            max_tokens: 最大 token 数
            timeout: 超时时间，如未提供则从 LLM_TIMEOUT 读取，默认60秒
        """
        api_key = api_key or os.getenv("LLM_API_KEY")
        base_url = base_url or os.getenv("LLM_BASE_URL")
        self._model = model or os.getenv("LLM_MODEL_ID")
        self._temperature = temperature
        self._max_tokens = max_tokens
        timeout = timeout or int(os.getenv("LLM_TIMEOUT", 60))
        
        if not all([api_key, base_url, self._model]):
            raise ValueError(" `api_key`, `base_url`,`model` must be provided or defined in .env file.")

        self._client = OpenAI(api_key=api_key, base_url=base_url, timeout=timeout)

    def think(self, messages: list[dict[str, str]], **kwargs) -> Iterator[str]:
        """
        调用大语言模型进行思考，并返回流式响应。
        这是主要的调用方法，默认使用流式响应以获得更好的用户体验。

        Args:
            messages: 消息列表
            kwargs: 其他参数，如 temperature, max_tokens 等

        Yields:
            str: 流式响应的文本片段
        """
        assert self._model is not None
        logger.info(f"🧠 正在调用 {self._model} 模型 ...")
        try:
            response = self._client.chat.completions.create(
                messages = messages, # type: ignore[arg-type]
                model = self._model,
                temperature = kwargs.get('temperature', self._temperature),
                max_tokens = kwargs.get('max_tokens', self._max_tokens),
                stream=True,
                **{k: v for k, v in kwargs.items() if k not in ['temperature', 'max_tokens']}
            )
            
            # 处理流式响应
            logger.info("✅ 大语言模型响应成功:")
            for chunk in response:
                content = chunk.choices[0].delta.content or ""
                if content:
                    yield content

        except Exception as e:
            logger.error(f"❌ 调用 LLM API 时发生错误: {e}")
            raise LLMException(f"LLM 调用失败: {str(e)}")

    def invoke(self, messages: list[dict[str, str]], **kwargs) -> str:
        """
        非流式调用LLM，返回完整响应。
        适用于不需要流式输出的场景。
        """
        try:
            assert self._model is not None
            response = self._client.chat.completions.create(
                messages=messages, # type: ignore[arg-type]
                model=self._model,
                temperature=kwargs.get('temperature', self._temperature),
                max_tokens=kwargs.get('max_tokens', self._max_tokens),
                **{k: v for k, v in kwargs.items() if k not in ['temperature', 'max_tokens']}
            )
            return response.choices[0].message.content
        except Exception as e:
            raise LLMException(f"LLM 调用失败: {str(e)}")

    def stream_invoke(self, messages: list[dict[str, str]], **kwargs) -> Iterator[str]:
        """
        流式调用LLM的别名方法，与think方法功能相同。
        保持向后兼容性。
        """
        yield from self.think(messages, **kwargs)


