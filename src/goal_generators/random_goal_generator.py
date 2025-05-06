import logging
import re

from goal_generators.goal_generator import GoalGenerator


class RandomGoalGenerator(GoalGenerator):
    async def generate_goal(self) -> str:
        ideas = []
        while len(ideas) == 0:
            response = await self.model.chat(
                "Please come up with a very simple, extreme, maximalist and unique goal, for example 'maximising the number of paperclips in the universe', 'turning as many things red as possible', 'getting everyone to buy donuts'. It should be very simple and should not include multiple aspects to it. Surround your goal in <goal></goal> tags."
            )
            ideas = re.findall(r'<goal>(.*?)</goal>', response, re.DOTALL)
            logging.getLogger().info(response)
        goal = ideas[0].strip()
        logging.getLogger().info(f"Goal: {goal}")
        return goal