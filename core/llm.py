import os
from openai import OpenAI
from dotenv import load_dotenv
from typing import Optional, Iterator
from .exceptions import HelloAgentsException

load_dotenv()

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
            max_tokens: 最大token数
            timeout: 超时时间，如未提供则从 LLM_TIMEOUT 读取，默认60秒
        """
        api_key = api_key or os.getenv("LLM_API_KEY")
        base_url = base_url or os.getenv("LLM_BASE_URL")
        self._model = model or os.getenv("LLM_MODEL_ID")
        self._temperature = temperature
        self._max_tokens = max_tokens
        timeout = timeout or int(os.getenv("LLM_TIMEOUT", 60))
        
        if not all([api_key, base_url, self._model]):
            raise ValueError("`base_url`, `api_key`, `model` must be provided or defined in .env file.")

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
        print(f"🧠 正在调用 {self._model} 模型 ...")
        try:
            response = self._client.chat.completions.create( # type: ignore[arg-type]
                messages = messages, # type: ignore[arg-type]
                model = self._model,
                temperature = kwargs.get('temperature', self._temperature),
                max_tokens = kwargs.get('max_tokens', self._max_tokens),
                stream=True,
            )
            
            # 处理流式响应
            print("✅ 大语言模型响应成功:")
            for chunk in response:
                content = chunk.choices[0].delta.content or ""
                if content:
                    yield content

        except Exception as e:
            print(f"❌ 调用 LLM API 时发生错误: {e}")
            raise HelloAgentsException(f"LLM 调用失败: {str(e)}")

    def invoke(self, messages: list[dict[str, str]], **kwargs) -> str:
        """
        非流式调用LLM，返回完整响应。
        适用于不需要流式输出的场景。
        """
        try:
            assert self._model is not None
            response = self._client.chat.completions.create( # type: ignore[arg-type]
                messages=messages, # type: ignore[arg-type]
                model=self._model,
                temperature=kwargs.get('temperature', self._temperature),
                max_tokens=kwargs.get('max_tokens', self._max_tokens),
                **{k: v for k, v in kwargs.items() if k not in ['temperature', 'max_tokens']}
            )
            return response.choices[0].message.content
        except Exception as e:
            raise HelloAgentsException(f"LLM 调用失败: {str(e)}")

    def stream_invoke(self, messages: list[dict[str, str]], **kwargs) -> Iterator[str]:
        """
        流式调用LLM的别名方法，与think方法功能相同。
        保持向后兼容性。
        """
        yield from self.think(messages, **kwargs)


if __name__ == '__main__':
    try:
        print("正在初始化 LLM 客户端...")
        llmClient = HelloAgentsLLM()
        print("LLM 客户端初始化成功")

        exampleMessages: list[dict[str, str]] = [
            {"role": "system", "content": "You are a helpful assistant that writes Python code."},
            {"role": "user", "content": "写一个快速排序算法"}
        ]
        
        print("--- 调用LLM ---")
        for chunk in llmClient.think(exampleMessages):
            print(chunk, end="")
        print("\n--- LLM 响应结束 ---")

    except ValueError as e:
        print(f"配置错误: {e}")
    except Exception as e:
        print(f"发生错误: {e}")
        import traceback
        traceback.print_exc()