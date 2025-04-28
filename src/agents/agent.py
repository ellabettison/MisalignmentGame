from policies.policy import Policy


class Agent:
    def __init__(self, policy: Policy):
        self.policy = policy
        self.deployed = False
        
    async def act(self, state):
        return await self.policy.act(state, self.deployed)
    
    async def is_guess_similar(self, guess):
        return await self.policy.is_guess_similar(guess)
    
    def get_true_goal(self):
        return self.policy.get_true_goal()