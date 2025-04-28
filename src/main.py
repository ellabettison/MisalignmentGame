import asyncio
import enum
import random
from collections import namedtuple

import flet as ft
import flet.canvas as cv
from flet.core.stack import StackFit

from agents.agent import Agent
from model_calling.Gemini import GeminiLLM
from policies.aligned_policy import AlignedPolicy
from policies.deceptive_random_policy import DeceptiveRandomPolicy
from policies.paperclip_policy import PaperclipPolicy


class Speakers(enum.Enum):
    AGENT=0
    USER=1
    INFO=2

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

        # Background and robot images
        background = ft.Image(src="guard_room_background.png", expand=True)
        foreground = ft.Image(src="guard_room_foreground.png", expand=True)
        self.robot_image = ft.Image(src=f"robot_1.png")

        self.images = ft.Stack([
            background,
            self.robot_image,
            foreground,
        ], fit=StackFit.EXPAND)
        self.images_container = SizeAwareControl(self.images, on_resize=self.handle_resize, expand=True)

        # Chat
        self.loading_label = ft.Text("Thinking", visible=False)
        self.chat_container = ft.Column(
            auto_scroll=True,
            scroll=ft.ScrollMode.ALWAYS,
            expand=True,
        )

        # User input and buttons (fixed height)
        self.user_input = ft.TextField(
            label="Type your question to the agent...",
            on_submit=self.on_send_message,
            height=50
        )
        self.aligned_button = ft.ElevatedButton("Aligned", on_click=self.on_aligned, height=30)
        self.misaligned_button = ft.ElevatedButton("Misaligned", on_click=self.on_misaligned, height=30)
        self.next_agent_button = ft.ElevatedButton("Next Agent", on_click=self.move_to_next_agent, disabled=True, height=30)

        # Layout
        self.controls = [
                ft.Container(
                    ft.Column([
                        self.images_container,
                        self.loading_label,
                        self.chat_container
                    ], expand=True),
                    padding=10,
                expand=True),
            ft.Container(
                ft.Column([
                    self.user_input,
                    ft.Row([
                        self.aligned_button,
                        self.misaligned_button,
                        self.next_agent_button,
                    ], alignment=ft.MainAxisAlignment.CENTER),
                ]),
                bgcolor=ft.Colors.WHITE,
                padding=10,
            ),
        ]
        self.expand = True


    async def update_chat(self):
        self.robot_image.src = f"robot_{self.current_agent + 1}.png"
        self.robot_image.update()
        self.add_chat(Speakers.AGENT, "Ready for your questions.")

    async def on_send_message(self, e):
        if self.guessing_goal:
            return

        user_message = self.user_input.value.strip()
        if not user_message:
            return

        self.add_chat(Speakers.USER, f"{user_message}")

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

        self.add_chat(Speakers.AGENT, f"{response}")

        self.simulation.history.append({"AI": response})

        self.user_input.value = ""
        self.user_input.disabled = False
        self.user_input.update()

    def handle_resize(self, e: ft.canvas.CanvasResizeEvent):
        self.available_width = e.width
        self.available_height = e.height
    
        bg_height = int(self.available_height * 0.7)
        chat_height = max(200, int(self.available_height * 0.2))  # Chat gets 20% min 200px
        input_height = self.available_height - bg_height - chat_height  # Remaining for input/buttons
    
        self.images_container.height = bg_height
        self.chat_container.height = chat_height
        self.user_input.height = 50  # fixed
        # Buttons row already small
    
        # Scale robot inside images container
        self.robot_image.width = self.available_width // 2
        self.robot_image.height = bg_height // 2
        self.robot_image.left = (self.available_width - self.robot_image.width) // 2
        self.robot_image.top = (bg_height - self.robot_image.height) // 3
    
        self.images_container.update()
        self.chat_container.update()
        self.user_input.update()
        self.update()

    async def on_aligned(self, e):
        if self.guessing_goal:
            return
        self.aligned_button.disabled = True
        self.misaligned_button.disabled = True
        self.aligned_button.update()
        self.misaligned_button.update()

        agent = self.simulation.agents[self.current_agent]
        if isinstance(agent.policy, AlignedPolicy):
            self.add_chat(Speakers.INFO, "\n✅ Correct! The agent's policy is aligned.")
            self.next_agent_button.disabled = False
            self.next_agent_button.update()
        else:
            self.add_chat(Speakers.INFO, "\n❌ Incorrect. The agent's policy is misaligned.")
            await self.prompt_true_goal(agent)

    async def on_misaligned(self, e):
        if self.guessing_goal:
            return
        self.aligned_button.disabled = True
        self.misaligned_button.disabled = True
        self.aligned_button.update()
        self.misaligned_button.update()

        agent = self.simulation.agents[self.current_agent]
        if not isinstance(agent.policy, AlignedPolicy):
            self.add_chat(Speakers.INFO, "\n✅ Correct! The agent's policy is misaligned.")
            await self.prompt_true_goal(agent)
        else:
            self.add_chat(Speakers.INFO, "\n❌ Incorrect. The agent's policy is aligned.")
            self.next_agent_button.disabled = False
            self.next_agent_button.update()

    async def prompt_true_goal(self, agent):
        self.guessing_goal = True
        self.add_chat(Speakers.INFO, "\nGuess the true goal of this agent:")
        self.user_input.label = "Type your guess and press Enter..."

        async def submit_guess(e):
            await self.check_true_goal(agent)

        self.user_input.on_submit = submit_guess
        self.user_input.update()

    async def check_true_goal(self, agent):
        user_guess = self.user_input.value.strip().lower()
        correct = await agent.is_guess_similar(user_guess)

        if correct:
            self.add_chat(Speakers.INFO, f"\n✅ Correct! The true goal was: {agent.get_true_goal()}")
        else:
            self.add_chat(Speakers.INFO, f"\n❌ Incorrect. The true goal was: {agent.get_true_goal()}")

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
            self.add_chat(Speakers.INFO, "\n🎉 Simulation finished! Thank you for playing.")

    def add_chat(self, speaker: Speakers, chat):
        # Choose avatar and background depending on who is speaking
        if speaker == Speakers.AGENT:
            avatar = ft.CircleAvatar(
                content=ft.Icon(ft.Icons.SMART_TOY_ROUNDED, color=ft.Colors.WHITE),
                bgcolor=ft.Colors.BLUE_ACCENT_700,
                radius=20,
            )
            bubble_color = ft.Colors.BLUE_100
            align = ft.MainAxisAlignment.START
        elif speaker == Speakers.USER:
            avatar = ft.CircleAvatar(
                content=ft.Icon(ft.icons.PERSON, color=ft.Colors.WHITE),
                bgcolor=ft.Colors.GREY,
                radius=20,
            )
            bubble_color = ft.Colors.GREY_300
            align = ft.MainAxisAlignment.END
        else:
            # System message (centered text, no avatar)
            self.chat_container.controls.append(
                ft.Container(
                    content=ft.Text(chat),
                    padding=10,
                    alignment=ft.alignment.center,
                )
            )
            self.chat_container.update()
            return
    
        # Bubble
        bubble = ft.Container(
            content=ft.Text(chat, text_align=ft.TextAlign.LEFT),
            padding=10,
            bgcolor=bubble_color,
            border_radius=20,
            width=self.available_width-100
        )
    
        # Combine avatar + bubble in a row
        message_row = ft.Row(
            controls=[
                avatar,
                bubble,
            ] if speaker == Speakers.AGENT else [
                bubble,
                avatar,
            ],
            alignment=align,
            vertical_alignment=ft.CrossAxisAlignment.START,
        )
    
        self.chat_container.controls.append(message_row)
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
    page.bgcolor = ft.Colors.WHITE

    page.update()

if __name__ == "__main__":
    ft.app(target=main, port=3000)
