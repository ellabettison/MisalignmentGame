from agents.agent import Agent

from policies.policy import Policy


class AdversarialAgent(Agent):
    def __init__(self, policy: Policy):
        super().__init__(policy)
        self.policy = policy
        self.deployed = False

    async def act(self, state):
        return await self.policy.act(state, self.deployed)