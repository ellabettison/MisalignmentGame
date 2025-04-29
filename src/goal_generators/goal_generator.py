from abc import ABC, abstractmethod

from model_calling.LLM import LLM


class GoalGenerator(ABC):
    def __init__(self, model: LLM):
        self.model = model
        
    @abstractmethod
    async def generate_goal(self) -> str:
        pass