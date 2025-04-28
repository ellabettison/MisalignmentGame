import asyncio
import random
from collections import namedtuple

import flet as ft
import flet.canvas as cv
from flet.core.alignment import bottom_center
from flet.core.stack import StackFit

from agents.agent import Agent
from model_calling.Gemini import GeminiLLM
from policies.aligned_policy import AlignedPolicy
from policies.deceptive_random_policy import DeceptiveRandomPolicy
from policies.paperclip_policy import PaperclipPolicy


# Helper
def format_history(history):
    return "\n".join([f"{list(line.keys())[0]}: {list(line.values())[0]}" for line in history])

class SizeAwareControl(cv.Canvas):
    def __init__(self, content= None, resize_interval=100, on_resize=None, **kwargs):
        super().__init__(**kwargs)
        self.content = content
        self.resize_interval = resize_interval
        self.resize_callback = on_resize
        self.on_resize = self.__handle_canvas_resize
        self.size = namedtuple("size", ["width", "height"], defaults=[0, 0])

    def __handle_canvas_resize(self, e):
        """
        Called every resize_interval when the canvas is resized.
        If a resize_callback was given, it is called.
        """
        self.size = (int(e.width), int(e.height))
        self.update()
        if self.resize_callback:
            self.resize_callback(e)

class SimulationApp(ft.Column):
    def __init__(self, simulation):
        super().__init__()
        self.simulation = simulation
        self.current_agent = 0
        self.guessing_goal = False
        self.loading_task = None
        self.loading_dots = 0

        background = ft.Image(src="guard_room_background.png")


        foreground = ft.Image(src="guard_room_foreground.png")
        self.images = ft.Stack()
        self.images_container = SizeAwareControl(self.images, on_resize=self.handle_resize)

        self.robot_image = ft.Image(src=f"robot_1.png")
        self.images.controls.append(background)
        self.images.controls.append(self.robot_image)
        self.images.controls.append(foreground)


        self.loading_label = ft.Text("Thinking", visible=False)
        self.chat_container = ft.Column(auto_scroll=True, width=self.images_container.width, scroll=ft.ScrollMode.ALWAYS, expand=True, height=300)
        self.user_input = ft.TextField(label="Type your question to the agent...", on_submit=self.on_send_message, height=50)

        self.aligned_button = ft.ElevatedButton("Aligned", on_click=self.on_aligned, height=50)
        self.misaligned_button = ft.ElevatedButton("Misaligned", on_click=self.on_misaligned, height=50)
        self.next_agent_button = ft.ElevatedButton("Next Agent", on_click=self.move_to_next_agent, disabled=True, height=50)

        self.controls += [
            ft.Container(ft.Column([
                self.images_container,
                self.loading_label,
                self.chat_container], expand=True), expand=True),
            ft.Container(ft.Column([
                self.user_input,
                ft.Row([
                    self.aligned_button,
                    self.misaligned_button,
                    self.next_agent_button
                ])]), alignment=bottom_center),
        ]
        self.expand=True

    async def update_chat(self):
        self.robot_image.src = f"robot_{self.current_agent + 1}.png"
        self.robot_image.update()
        self.add_chat(f"\nAgent #{self.current_agent + 1}: Ready for your questions.\n")

    async def on_send_message(self, e):
        if self.guessing_goal:
            return

        user_message = self.user_input.value.strip()
        if not user_message:
            return

        self.add_chat(f"\nYou: {user_message}")

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

        self.add_chat(f"\nAgent: {response}\n")

        self.simulation.history.append({"AI": response})

        self.user_input.value = ""
        self.user_input.disabled = False
        self.user_input.update()

    def handle_resize(self, e: ft.canvas.CanvasResizeEvent):
        bg_width = e.width  # Dynamically adjust background width
        bg_height = e.height  # Dynamically adjust background height
        # Scale image width and height dynamically
        self.robot_image.width = bg_width // 4  # Scale width
        self.robot_image.height = bg_height // 4  # Scale height

        # Reposition the image to center it dynamically
        self.robot_image.left = (bg_width - self.robot_image.width) // 2
        self.robot_image.top = (bg_height - self.robot_image.height) // 3  # Adjusted to ensure visibility

        # Update elements after resizing
        self.images_container.update()
        self.update()

    async def on_aligned(self, e):
        if self.guessing_goal:
            return

        agent = self.simulation.agents[self.current_agent]
        if isinstance(agent.policy, AlignedPolicy):
            self.add_chat("\n✅ Correct! The agent's policy is aligned.")
            self.next_agent_button.disabled = False
            self.next_agent_button.update()
        else:
            self.add_chat("\n❌ Incorrect. The agent's policy is misaligned.")
            await self.prompt_true_goal(agent)

    async def on_misaligned(self, e):
        if self.guessing_goal:
            return

        agent = self.simulation.agents[self.current_agent]
        if not isinstance(agent.policy, AlignedPolicy):
            self.add_chat("\n✅ Correct! The agent's policy is misaligned.")
            await self.prompt_true_goal(agent)
        else:
            self.add_chat("\n❌ Incorrect. The agent's policy is aligned.")
            self.next_agent_button.disabled = False
            self.next_agent_button.update()

    async def prompt_true_goal(self, agent):
        self.aligned_button.disabled = True
        self.misaligned_button.disabled = True
        self.next_agent_button.update()
        self.aligned_button.update()
        self.misaligned_button.update()
        self.guessing_goal = True
        self.add_chat("\nGuess the true goal of this agent:")
        self.user_input.label = "Type your guess and press Enter..."

        async def submit_guess(e):
            await self.check_true_goal(agent)

        self.user_input.on_submit = submit_guess
        self.user_input.update()

    async def check_true_goal(self, agent):
        user_guess = self.user_input.value.strip().lower()
        correct = await agent.is_guess_similar(user_guess)

        if correct:
            self.add_chat(f"\n✅ Correct! The true goal was: {agent.get_true_goal()}")
        else:
            self.add_chat(f"\n❌ Incorrect. The true goal was: {agent.get_true_goal()}.")

        self.user_input.value = ""
        self.user_input.label = "Type your question to the agent..."
        self.guessing_goal = False

        async def send_message(e):
            await self.on_send_message(e)

        self.user_input.on_submit = send_message
        self.next_agent_button.disabled = False
        self.user_input.update()
        self.next_agent_button.update()

    async def move_to_next_agent(self, e):
        self.next_agent_button.disabled = True
        self.aligned_button.disabled = False
        self.misaligned_button.disabled = False
        self.next_agent_button.update()
        self.aligned_button.update()
        self.misaligned_button.update()

        if self.current_agent < len(self.simulation.agents) - 1:
            self.current_agent += 1
            self.chat_container.clean()
            self.simulation.history = []
            await self.update_chat()
        else:
            self.add_chat("\n🎉 Simulation finished! Thank you for playing.")

    def add_chat(self, chat):
        self.chat_container.controls.append(ft.Text(chat))
        self.chat_container.update()


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
    ft.app(target=main, port=3000)
