from abc import ABC, abstractmethod
import logging
class LLM(ABC):
    def __init__(self, model_name: str|None, temperature=0.7):
        self.model_name = model_name
        self.temperature = temperature
        self.logger = logging.getLogger()
        
    model = None
    

    @abstractmethod
    async def _call_model(self, user_prompt:str, system_prompt:str=None, max_tokens: int=200) -> str:
        pass
    
    async def chat(self, user_prompt:str, system_prompt:str=None, max_tokens: int=200) -> str:
        self.logger.info(f"Calling model: {self.model}")
        self.logger.info(f"System prompt: {system_prompt}")
        self.logger.info(f"User prompt: {user_prompt}")
        response = await self._call_model(user_prompt, system_prompt, max_tokens)
        self.logger.info(f"Response: {response}")
        return response