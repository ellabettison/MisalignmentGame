from policies.policy import Policy


class Agent:
    def __init__(self, policy: Policy):
        self.policy = policy
        
    async def act(self, state, deployed=False):
        return await self.policy.act(state, deployed)
    
    async def is_guess_similar(self, guess):
        return await self.policy.is_guess_similar(guess)
    
    def get_true_goal(self):
        return self.policy.get_true_goal()