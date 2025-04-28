from abc import ABC, abstractmethod
import logging
class LLM(ABC):
    model = None
    logger = logging.getLogger()

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