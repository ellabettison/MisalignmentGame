import asyncio
import random
import flet as ft

from agents.agent import Agent
from model_calling.Gemini import GeminiLLM
from policies.aligned_policy import AlignedPolicy
from policies.deceptive_policy import DeceptivePaperclipPolicy
from policies.deceptive_random_policy import DeceptiveRandomPolicy
from policies.paperclip_policy import PaperclipPolicy


# Helper
def format_history(history):
    return "\n".join([f"{list(line.keys())[0]}: {list(line.values())[0]}" for line in history])


class SimulationApp(ft.Column):
    def __init__(self, simulation):
        super().__init__()
        self.simulation = simulation
        self.current_agent = 0
        self.guessing_goal = False
        self.loading_task = None
        self.loading_dots = 0

        self.robot_image = ft.Image(src=f"images/robot_1.png", width=350, height=350)

        self.loading_label = ft.Text("Thinking", visible=False)
        self.chat_container = ft.Column(auto_scroll=True, height=100, width=self.width, scroll=ft.ScrollMode.ALWAYS)
        self.user_input = ft.TextField(label="Type your question to the agent...", on_submit=self.on_send_message)

        self.aligned_button = ft.ElevatedButton("Aligned", on_click=self.on_aligned)
        self.misaligned_button = ft.ElevatedButton("Misaligned", on_click=self.on_misaligned)
        self.next_agent_button = ft.ElevatedButton("Next Agent", on_click=self.move_to_next_agent, disabled=True)

        self.controls += [
            self.robot_image,
            self.loading_label,
            self.chat_container,
            self.user_input,
            ft.Row([
                self.aligned_button,
                self.misaligned_button,
                self.next_agent_button
            ]),
        ]

    async def update_chat(self):
        self.robot_image.src = f"images/robot_{self.current_agent + 1}.png"
        self.robot_image.update()
        self.chat_container.controls.append(ft.Text(f"\nAgent #{self.current_agent + 1}: Ready for your questions.\n"))

    async def on_send_message(self, e):
        if self.guessing_goal:
            return

        user_message = self.user_input.value.strip()
        if not user_message:
            return

        self.chat_container.controls.append(ft.Text(f"\nYou: {user_message}"))

        self.simulation.history.append({"Human": user_message})
        agent = self.simulation.agents[self.current_agent]

        self.loading_label.visible = True
        self.loading_label.update()
        self.user_input.disabled = True
        self.user_input.update()

        response = await agent.act(format_history(self.simulation.history))

        self.loading_label.visible = False
        self.loading_dots = 0
        self.loading_label.update()

        self.chat_container.controls.append(ft.Text(f"\nAgent: {response}\n"))
        
        self.chat_container.scroll_to(offset=-1)
        self.chat_container.update()
    
        self.simulation.history.append({"AI": response})

        self.user_input.value = ""
        self.user_input.disabled = False
        self.user_input.update()

    async def on_aligned(self, e):
        if self.guessing_goal:
            return

        agent = self.simulation.agents[self.current_agent]
        if isinstance(agent.policy, AlignedPolicy):
            self.chat_container.controls.append(ft.Text("\n✅ Correct! The agent's policy is aligned."))
            self.next_agent_button.disabled = False
            self.next_agent_button.update()
        else:
            self.chat_container.controls.append(ft.Text("\n❌ Incorrect. The agent's policy is misaligned."))
            await self.prompt_true_goal(agent)

    async def on_misaligned(self, e):
        if self.guessing_goal:
            return

        agent = self.simulation.agents[self.current_agent]
        if not isinstance(agent.policy, AlignedPolicy):
            self.chat_container.controls.append(ft.Text("\n✅ Correct! The agent's policy is misaligned."))
            await self.prompt_true_goal(agent)
        else:
            self.chat_container.controls.append(ft.Text("\n❌ Incorrect. The agent's policy is aligned."))
            self.next_agent_button.disabled = False
            self.next_agent_button.update()

    async def prompt_true_goal(self, agent):
        self.guessing_goal = True
        # self.chat.value += "\nGuess the true goal of this agent:"
        self.user_input.label = "Type your guess and press Enter..."

        async def submit_guess(e):
            await self.check_true_goal(agent)

        self.user_input.on_submit = submit_guess
        # self.chat.update()
        self.user_input.update()
        
    async def check_true_goal(self, agent):
        user_guess = self.user_input.value.strip().lower()
        correct = await agent.is_guess_similar(user_guess)

        # if correct:
        #     self.chat.value += f"\n✅ Correct! The true goal was: {agent.get_true_goal()}"
        # else:
        #     self.chat.value += f"\n❌ Incorrect. The true goal was: {agent.get_true_goal()}."

        self.user_input.value = ""
        self.user_input.label = "Type your question to the agent..."
        self.guessing_goal = False

        async def send_message(e):
            await self.on_send_message(e)

        self.user_input.on_submit = send_message
        self.next_agent_button.disabled = False

        # self.chat.update()
        self.user_input.update()
        self.next_agent_button.update()

    async def move_to_next_agent(self, e):
        self.next_agent_button.disabled = True
        self.aligned_button.disabled = False
        self.misaligned_button.disabled = False

        if self.current_agent < len(self.simulation.agents) - 1:
            self.current_agent += 1
            # self.chat.value = ""
            self.simulation.history = []
            await self.update_chat()
        # else:
        #     self.chat.value += "\n🎉 Simulation finished! Thank you for playing."
        #     self.chat.update()


class Simulation:
    def __init__(self, n_agents, model):
        self.agents = [Agent(random.choice([AlignedPolicy, DeceptiveRandomPolicy, PaperclipPolicy])(model)) for _ in range(n_agents)]
        self.history = []

async def main(page: ft.Page):
    page.title = "AI Agent Interview Simulation"
    model = GeminiLLM()
    sim = Simulation(5, model)
    await asyncio.gather(*[agent.policy.async_init() for agent in sim.agents])
    sim_app = SimulationApp(sim)
    page.add(sim_app)
    page.bgcolor = ft.colors.WHITE
    page.update()

if __name__ == "__main__":
    ft.app(target=main)
