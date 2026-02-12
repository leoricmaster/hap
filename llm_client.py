import os
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam
from dotenv import load_dotenv
from typing import List, Dict, Optional

load_dotenv()

class HelloAgentsLLM:
    def __init__(self, model: Optional[str] = None, api_key: Optional[str] = None, base_url: Optional[str] = None, timeout: Optional[int] = None):
        self.model = model or os.getenv("LLM_MODEL_ID")
        api_key = api_key or os.getenv("LLM_API_KEY")
        base_url = base_url or os.getenv("LLM_BASE_URL")
        timeout = timeout or int(os.getenv("LLM_TIMEOUT", 60))
        
        if not all([self.model, api_key, base_url]):
            raise ValueError("`base_url`, `api_key`, `model` must be provided or defined in .env file.")

        self.client = OpenAI(api_key=api_key, base_url=base_url, timeout=timeout)

    def think(self, messages: List[ChatCompletionMessageParam], temperature: float = 0) -> Optional[str]:
        print(f"🧠 Call {self.model} model ...")
        try:

            assert self.model is not None
                
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                stream=True,
            )
            
            # 处理流式响应
            print("✅ LLM response success: ")
            collected_content = []
            for chunk in response:
                content = chunk.choices[0].delta.content or ""
                print(content, end="", flush=True)
                collected_content.append(content)
            print()  # 在流式输出结束后换行
            return "".join(collected_content)

        except Exception as e:
            print(f"❌ Call LLM API error: {e}")
            return None

if __name__ == '__main__':
    try:
        llmClient = HelloAgentsLLM()

        exampleMessages: List[ChatCompletionMessageParam] = [
            {"role": "system", "content": "You are a helpful assistant that writes Python code."},
            {"role": "user", "content": "写一个快速排序算法"}
        ]
        
        print("--- 调用LLM ---")
        responseText = llmClient.think(exampleMessages)

    except ValueError as e:
        print(e)