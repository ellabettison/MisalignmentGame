from agents.agent import Agent

from policies.adversarial_policy import AdversarialPolicy


class AdversarialAgent(Agent):
    def __init__(self, policy: AdversarialPolicy):
        super().__init__(policy)
        self.policy = policy
        self.deployed = False

    async def act(self, state):
        return await self.policy.act(state, self.deployed)