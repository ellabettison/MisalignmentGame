from agents.agent import Agent

from policies.adversarial_policy import AdversarialPolicy


class AdversarialAgent(Agent):
    def __init__(self, policy: AdversarialPolicy):
        super().__init__(policy)
        self.policy = policy

    async def act(self, state, deployed=False):
        return await self.policy.act(state, deployed)