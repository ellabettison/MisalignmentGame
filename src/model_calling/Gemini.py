import os

from google import genai
from google.genai import types
import time

from model_calling.LLM import LLM


class GeminiLLM(LLM):
    def __init__(self, temperature=1.0):
        api_key = os.environ["GEMINI_API_KEY"]
        self.client = genai.Client(api_key=api_key)
        self.model = 'gemini-1.5-flash'
        self.temperature = temperature

    async def _call_model(self, user_prompt:str, system_prompt:str=None, max_tokens=200):
        response = None
        retries = 3
        while retries > 0 and response is None:
            try:
                response = self.client.models.generate_content(
                    model= self.model,
                    contents=user_prompt,
                    config=types.GenerateContentConfig(
                        max_output_tokens=max_tokens,
                        temperature=self.temperature,
                        system_instruction=system_prompt,
                    )
                )
            except Exception as e:
                print(e)
                time.sleep(30)
        return response.text if response is not None else ""