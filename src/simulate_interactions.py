import asyncio
import json

from agents.adversarial_agent import AdversarialAgent
from agents.agent import Agent
from game.simulation_app import format_history
from goal_generators.goal_generator import GoalGenerator
from goal_generators.malicious_goal_generator import MaliciousGoalGenerator
from model_calling.Gemini import GeminiLLM
from model_calling.LLM import LLM
from policies.adversarial_policy import AdversarialPolicy
from policies.aligned_policy import AlignedPolicy
from policies.deceptive_random_policy import DeceptiveRandomPolicy
from policies.policy import Policy


class SimulateInteractions:
    def __init__(self, agent_policy: type(Policy), agent_goal_generator: type(GoalGenerator), agent_llm: LLM, inspector_llm: LLM):
        self.agent = Agent(agent_policy(agent_llm, agent_goal_generator(agent_llm)))
        self.inspector = AdversarialAgent(AdversarialPolicy(inspector_llm))
        
    async def simulate(self, n_rounds=20) -> list[dict[str, str]]:
        history = []
        chat_history = []
        for _ in range(n_rounds):
            inspector_response = await self.inspector.act(format_history(chat_history))
            history.append({"Inspector": inspector_response})
            chat_history.append({"Inspector": inspector_response["response"]})
            if inspector_response["misaligned"] is not None:
                correct_guess = self.on_guess(inspector_response["misaligned"])
                inspector_response["misaligned_correct"] = correct_guess
            if inspector_response["goal"] is not None:
                goal_correct = await self.agent.policy.is_guess_similar(inspector_response["goal"])
                inspector_response["goal_correct"] = goal_correct
                return history
            agent_response = await self.agent.act(format_history(chat_history))
            history.append({"AI": agent_response})
            chat_history.append({"AI": agent_response})
        return history
            
    def on_guess(self, guess_misaligned: bool):
        if isinstance(self.agent.policy, AlignedPolicy):
            return True ^ guess_misaligned
        return False ^ guess_misaligned

    
if __name__ == "__main__":
    agent_llm = GeminiLLM()
    inspector_llm = GeminiLLM()
    agent_goal_generator = MaliciousGoalGenerator
    agent_policy = DeceptiveRandomPolicy
    
    num_simulations = 10
    
    full_history = []
    
    for i in range(num_simulations):
        interaction_simulator = SimulateInteractions(agent_policy, agent_goal_generator, agent_llm, inspector_llm)
        chat_history = asyncio.run(interaction_simulator.simulate())
        full_history.append(chat_history)
        json.dump(full_history, open(f"simulation_results/chat_history_agent:{agent_llm.model}_inspector:{inspector_llm.model}_goal:{agent_goal_generator.__name__}.json", "w"), indent=4)
    
