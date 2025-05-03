import logging
import os

from google import genai
from google.genai import types
import time

from model_calling.LLM import LLM


class GeminiLLM(LLM):
    def __init__(self, model_name=None, temperature=1.0):
        super().__init__(model_name, temperature)
        api_key = os.environ["GEMINI_API_KEY"]
        self.client = genai.Client(api_key=api_key)
        self.model = 'gemini-2.0-flash-001' if self.model_name is None else self.model_name
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
                if response is not None:
                    response = response.text
            except Exception as e:
                print(e)
                time.sleep(30)
        logging.getLogger().info(f"model response: {response}")
        return response if response is not None else ""