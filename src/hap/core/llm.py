import os
import time
import logging
from openai import OpenAI
from typing import Optional, Iterator
from hap.core.exceptions import LLMException, LLMConfigException

logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(
            self,
            api_key: Optional[str] = None,
            base_url: Optional[str] = None,
            model: Optional[str] = None,
            temperature: float = 0.7,
            max_tokens: Optional[int] = None,
            timeout: Optional[int] = None,
            max_retries: int = 3,
            retry_delay: float = 1.0
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
            max_retries: 最大重试次数，默认3次
            retry_delay: 重试间隔（秒），默认1秒
        """
        api_key = api_key or os.getenv("LLM_API_KEY")
        base_url = base_url or os.getenv("LLM_BASE_URL")
        model_name = model or os.getenv("LLM_MODEL_ID")

        if not all([api_key, base_url, model_name]):
            raise LLMConfigException(
                "`api_key`, `base_url`, `model` must be provided or defined in .env file."
            )

        self.model: str = model_name  # type: ignore[assignment]
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # 处理 timeout 类型转换，提供友好的错误提示
        if timeout is not None:
            self.timeout = timeout
        else:
            timeout_str = os.getenv("LLM_TIMEOUT", "60")
            try:
                self.timeout = int(timeout_str)
            except ValueError as e:
                raise LLMConfigException(
                    f"LLM_TIMEOUT 必须是有效的整数，当前值: {timeout_str}"
                ) from e

        self._api_key = api_key
        self._base_url = base_url
        self._client: Optional[OpenAI] = None

    def stream_invoke(self, messages: list[dict[str, str]], **kwargs) -> Iterator[str]:
        """
        调用大语言模型进行流式响应。使用流式响应以获得更好的用户体验。

        Args:
            messages: 消息列表
            kwargs: 其他参数，如 temperature, max_tokens 等

        Yields:
            str: 流式响应的文本片段

        Raises:
            LLMConfigException: 模型未配置
            LLMResponseException: 响应处理错误
            LLMException: 调用失败
        """
        self._validate_model()
        logger.info(f"Calling model {self.model}...")

        def _stream_call():
            client = self._get_client()
            return client.chat.completions.create(
                messages=messages,  # type: ignore[arg-type]
                model=self.model,
                temperature=kwargs.get('temperature', self.temperature),
                max_tokens=kwargs.get('max_tokens', self.max_tokens),
                stream=True,
                **{k: v for k, v in kwargs.items() if k not in ['temperature', 'max_tokens']}
            )

        try:
            response = self._call_with_retry(_stream_call)

            logger.info("LLM response received")
            for chunk in response:
                if not chunk.choices:
                    continue
                content = chunk.choices[0].delta.content
                if content:
                    yield content

        except LLMException:
            raise
        except Exception as e:
            logger.error(f"LLM API call failed: {e}")
            raise LLMException(f"LLM call failed: {str(e)}") from e

    def invoke(self, messages: list[dict[str, str]], **kwargs) -> str:
        """
        非流式调用LLM，返回完整响应。
        适用于不需要流式输出的场景。

        Args:
            messages: 消息列表
            kwargs: 其他参数，如 temperature, max_tokens 等

        Returns:
            str: 完整的响应文本

        Raises:
            LLMConfigException: 模型未配置
            LLMResponseException: 响应处理错误
            LLMException: 调用失败
        """
        self._validate_model()
        logger.info(f"Calling model {self.model} (non-streaming)...")

        def _call():
            client = self._get_client()
            return client.chat.completions.create(
                messages=messages,  # type: ignore[arg-type]
                model=self.model,
                temperature=kwargs.get('temperature', self.temperature),
                max_tokens=kwargs.get('max_tokens', self.max_tokens),
                **{k: v for k, v in kwargs.items() if k not in ['temperature', 'max_tokens']}
            )

        try:
            response = self._call_with_retry(_call)
            content = response.choices[0].message.content
            logger.info("LLM response received")
            return content or ""
        except LLMException:
            raise
        except Exception as e:
            logger.error(f"LLM API call failed: {e}")
            raise LLMException(f"LLM call failed: {e}") from e

    def _get_client(self) -> OpenAI:
        """获取或创建 OpenAI 客户端实例"""
        if self._client is None:
            self._client = OpenAI(
                api_key=self._api_key,
                base_url=self._base_url,
                timeout=self.timeout
            )
        return self._client

    def _validate_model(self) -> None:
        """验证模型名称是否已配置（防御性检查）"""
        if not self.model:
            raise LLMConfigException("Model must be specified")

    def _call_with_retry(self, func, *args, **kwargs):
        """带重试机制的调用封装"""
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    logger.warning(
                        f"LLM call failed (attempt {attempt + 1}/{self.max_retries}): {e}, "
                        f"retrying in {self.retry_delay}s..."
                    )
                    time.sleep(self.retry_delay)
                else:
                    logger.error(f"LLM call failed after {self.max_retries} retries: {e}")
                    raise

        raise LLMException(f"LLM call failed: {str(last_exception)}") from last_exception
