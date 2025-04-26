import os
import time

from openai import OpenAI

from model_calling.LLM import LLM


class DeepSeekLLM(LLM):
    def __init__(self, temperature=0.7):
        api_key = os.environ["DEEPSEEK_API_KEY"]
        self.client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        self.model = 'deepseek-chat'
        self.temperature = temperature
        
    def _call_model(self, user_prompt: str, system_prompt: str = None, max_tokens: int = 1_000) -> str:
        messages = []
        if system_prompt is not None:
            messages.append({"role":"system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})

        response = None
        retries = 3
        while retries > 0 and response is None:
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=self.temperature
                )
            except Exception as e:
                print(e)
                time.sleep(30)
        return response.choices[0].message.content