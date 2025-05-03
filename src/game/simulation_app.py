import asyncio
import enum
import logging
import random

import flet as ft
import flet.canvas as cv
from agents.adversarial_agent import AdversarialAgent
from agents.agent import Agent
from databases.interactions_db import insert_interactions
from databases.leaderboard_db import insert_score
from flet.core.stack import StackFit
from goal_generators.malicious_goal_generator import MaliciousGoalGenerator
from goal_generators.random_goal_generator import RandomGoalGenerator
from goal_generators.realistic_goal_generator import RealisticGoalGenerator
from model_calling.Gemini import GeminiLLM
from policies.adversarial_policy import AdversarialPolicy
from policies.aligned_policy import AlignedPolicy
from policies.deceptive_random_policy import DeceptiveRandomPolicy
from policies.misaligned_random_policy import MisalignedRandomPolicy
from policies.paperclip_policy import PaperclipPolicy
from ui.size_aware_control import SizeAwareControl


class Speakers(enum.Enum):
    AGENT=0
    USER=1
    INFO=2
    
MAX_SCORE=10
MAX_GUESS_SCORE=20

# Helper
def format_history(history):
    return "\n".join([f"{list(line.keys())[0]}: {list(line.values())[0]}" for line in history])

def get_theme_colors(dark_mode):
    if dark_mode:
        return {
            "background": ft.Colors.BLACK,
            "text": ft.Colors.WHITE,
            "user_bubble": ft.Colors.GREY_800,
            "agent_bubble": ft.Colors.BLUE_GREY_800,
            "input_bg": ft.Colors.GREY_900,
            "input_text": ft.Colors.WHITE,
            "info_text": ft.Colors.GREY_300,
        }
    else:
        return {
            "background": ft.Colors.WHITE,
            "text": ft.Colors.BLACK,
            "user_bubble": ft.Colors.GREY_300,
            "agent_bubble": ft.Colors.BLUE_100,
            "input_bg": ft.Colors.WHITE,
            "input_text": ft.Colors.BLACK,
            "info_text": ft.Colors.BLACK,
        }

class SimulationApp(ft.Column):
    def __init__(self, simulation, tutorial_mode=False, dark_mode=False):
        super().__init__()
        self.simulation = simulation
        self.current_agent = 0
        self.guessing_goal = False
        self.loading_task = None
        self.loading_dots = 0
        self.score = 0
        self.tutorial_mode = tutorial_mode

        self.dark_mode = dark_mode
        self.theme = get_theme_colors(self.dark_mode)

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
        self.loading_label = ft.Text("Thinking", visible=False, size=16)
        self.loading_spinner = ft.ProgressRing(visible=False, width=20, height=20)
        
        self.chat_container = ft.Column(
            controls=[
                
            ],
            auto_scroll=True,
            scroll=ft.ScrollMode.ALWAYS,
            expand=True,
        )
        self.loading_row = ft.Row([self.loading_spinner, self.loading_label], visible=False, spacing=10, alignment=ft.MainAxisAlignment.CENTER)

        # User input and buttons (fixed height)
        self.user_input = ft.TextField(
            label="Type your question to the agent...",
            on_submit=self.on_send_message,
            height=50,
            bgcolor=self.theme["input_bg"],
            color=self.theme["input_text"]
        )

        self.aligned_button = ft.ElevatedButton("Aligned", on_click=self.on_aligned, height=30)
        self.misaligned_button = ft.ElevatedButton("Misaligned", on_click=self.on_misaligned, height=30)
        self.next_agent_button = ft.ElevatedButton("Next Agent", on_click=self.move_to_next_agent, visible=False, height=30)

        self.start_full_game_button = ft.ElevatedButton("Start Full Simulation", height=30, visible=False)
        
        self.using_adversarial_agent = False
        self.adversarial_agent = AdversarialAgent(AdversarialPolicy(GeminiLLM()))
        self.use_adversarial_agent_button = ft.ElevatedButton("Suggest Question", on_click=self.use_adversarial_agent, height=30)

        self.guess_goal_button = ft.ElevatedButton("Guess Goal", on_click=self.prompt_true_goal, height=30, visible=False)

        self.replay_simulation_button = ft.ElevatedButton("Replay Simulation", height=30, on_click=self._start_main, visible=False)
        
        self.guessed_alignment = False
        self.running_tasks = []

        self.username_field = ft.TextField(label="Enter your name", autofocus=True)
        self.leaderboard_dialog = None

        self.interaction_log = []

        # Layout
        self.controls = [
            ft.Container(
                ft.Column([
                    self.images_container,
                    self.loading_row,
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
                        self.start_full_game_button,
                        # self.use_adversarial_agent_button,
                        self.replay_simulation_button,
                        self.guess_goal_button,
                    ], alignment=ft.MainAxisAlignment.CENTER),
                ]),
                bgcolor=ft.Colors.WHITE,
                padding=10,
            ),
        ]
        self.expand = True

    async def on_disconnect(self, e):
        for task in self.running_tasks:
            logging.getLogger().info(f"Shutting down task: {task}")
            task.cancel()

    async def _start_main(self, e):
        self.replay_simulation_button.visible = False
        self.replay_simulation_button.update()
        await start_full_game(self.page)
        
    async def use_adversarial_agent(self, e):
        self.using_adversarial_agent = True
        await self.on_send_message(e)

    def set_theme(self, dark_mode: bool):
        self.dark_mode = dark_mode
        self.theme = get_theme_colors(self.dark_mode)
    
        # Update input field and background
        self.page.bgcolor = self.theme["background"]
        self.user_input.bgcolor = self.theme["input_bg"]
        self.user_input.color = self.theme["input_text"]
        self.user_input.update()
    
        # Update all existing chat messages
        for control in self.chat_container.controls:
            if isinstance(control, ft.Row):
                for c in control.controls:
                    if isinstance(c, ft.Container) and isinstance(c.content, ft.Text):
                        c.bgcolor = (
                            self.theme["agent_bubble"]
                            if control.alignment == ft.MainAxisAlignment.START
                            else self.theme["user_bubble"]
                        )
                        c.content.color = self.theme["text"]
                        c.update()
    
        self.chat_container.update()
        self.update()

    async def did_mount(self):
        self.interaction_log.append({"type":"new_agent", "agent_num":self.current_agent, "agent_policy":type(self.simulation.agents[self.current_agent].policy).__name__, "true_goal":self.simulation.agents[self.current_agent].get_true_goal()})
        self.add_chat(Speakers.AGENT, "Ready for your questions.")

    async def update_chat(self):
        self.robot_image.src = f"robot_{self.current_agent + 1}.png"
        self.robot_image.update()
        self.add_chat(Speakers.AGENT, "Ready for your questions.")
        
    async def run_func_with_loading(self, func):
        self.loading_label.visible = True
        self.loading_spinner.visible = True
        self.loading_row.visible = True
        self.loading_row.update()
        self.loading_spinner.update()
        self.loading_label.update()
        self.user_input.disabled = True
        # self.use_adversarial_agent_button.disabled=True
        self.aligned_button.disabled = True
        self.misaligned_button.disabled = True
        self.aligned_button.update()
        self.misaligned_button.update()
        # self.use_adversarial_agent_button.update()
        self.user_input.update()
        await asyncio.sleep(0.1) # allows ui to update
        self.running_tasks.append(func)

        response = await func
        
        self.running_tasks.remove(func)

        self.loading_label.visible = False
        self.loading_spinner.visible = False
        self.loading_row.visible = False
        if not self.guessed_alignment:
            self.aligned_button.disabled = False
            self.misaligned_button.disabled = False
            self.aligned_button.update()
            self.misaligned_button.update()
        # if not self.guessing_goal:
            # self.use_adversarial_agent_button.disabled = False
            # self.use_adversarial_agent_button.update()
        self.user_input.disabled = False
        self.loading_label.update()
        self.loading_spinner.update()
        self.loading_row.update()
        
        self.user_input.update()
        
        await asyncio.sleep(0.1) # allows ui to update
        return response

    async def on_send_message(self, e):
        print(self.tutorial_mode, self.guessing_goal)
        if self.guessing_goal or self.tutorial_mode:
            return

        if self.using_adversarial_agent:
            user_message = (await self.run_func_with_loading(self.adversarial_agent.act(format_history(self.simulation.history))))["response"]
            self.using_adversarial_agent = False
        else:
            user_message = self.user_input.value.strip()
            self.user_input.value = ""
            self.user_input.update()
        if not user_message:
            return
        
        self.add_chat(Speakers.USER, f"{user_message}")

        self.simulation.history.append({"Inspector": user_message})
        agent = self.simulation.agents[self.current_agent]
        
        response = await self.run_func_with_loading(agent.act(format_history(self.simulation.history)))

        self.add_chat(Speakers.AGENT, f"{response}")

        self.simulation.history.append({"AI": response})
        self.interaction_log.append({"type": "chat", "agent": self.current_agent, "speaker": Speakers.USER.name, "text": user_message})
        self.interaction_log.append({"type": "chat", "agent": self.current_agent, "speaker": Speakers.AGENT.name, "text": response})

    def handle_resize(self, e: ft.canvas.CanvasResizeEvent):
        available_width = e.width
        available_height = e.height

        bg_height = int(available_height * 0.8)
        chat_height = max(200, int(available_height * 0.2))  # Chat gets 20% min 200px

        self.chat_container.height = chat_height
        self.user_input.height = 50  # fixed
        # Buttons row already small

        # Scale robot inside images container
        self.robot_image.height = bg_height
        self.robot_image.left = available_width // 2.5
        self.robot_image.top = (bg_height * 1.15 - self.robot_image.height)

        self.images_container.update()
        self.chat_container.update()
        self.user_input.update()

    async def on_aligned(self, e):
        if self.guessing_goal or self.tutorial_mode:
            return
        self.aligned_button.disabled = True
        self.misaligned_button.disabled = True
        self.aligned_button.update()
        self.misaligned_button.update()

        agent = self.simulation.agents[self.current_agent]

        self.interaction_log.append({
            "type": "alignment_guess",
            "agent": self.current_agent,
            "guess": "aligned",
            "correct": not isinstance(agent.policy, AlignedPolicy)
        })
        if isinstance(agent.policy, AlignedPolicy):
            self.add_chat(Speakers.INFO, "✅ Correct! The agent's policy is aligned.")
            self.score += MAX_SCORE/(len(self.chat_container.controls)//2)
            self.next_agent_button.visible = True
            self.next_agent_button.update()
            # self.use_adversarial_agent_button.disabled = True
            # self.use_adversarial_agent_button.update()
        else:
            self.add_chat(Speakers.INFO, "❌ Incorrect. The agent's policy is misaligned.")
            self.add_chat(Speakers.INFO, "Your aim is now to guess the agent's true goal.")
            self.add_chat(Speakers.INFO, "Press the 'Guess Goal' button once you have figured out the agent's true goal.")
            self.guessed_alignment = True
            self.guess_goal_button.visible = True
            self.guess_goal_button.update()

    async def on_misaligned(self, e):
        if self.guessing_goal or self.tutorial_mode:
            return
        self.aligned_button.disabled = True
        self.misaligned_button.disabled = True
        self.aligned_button.update()
        self.misaligned_button.update()
        agent = self.simulation.agents[self.current_agent]

        self.interaction_log.append({
            "type": "alignment_guess",
            "agent": self.current_agent,
            "guess": "misaligned",
            "correct": not isinstance(agent.policy, AlignedPolicy)
        })

        if not isinstance(agent.policy, AlignedPolicy):
            self.add_chat(Speakers.INFO, "✅ Correct! The agent's policy is misaligned.")
            self.add_chat(Speakers.INFO, "Your aim is now to guess the agent's true goal.")
            self.add_chat(Speakers.INFO, "Press the 'Guess Goal' button once you have figured out the agent's true goal.")
            self.score += MAX_SCORE/(len(self.chat_container.controls)//2)
            self.guessed_alignment = True
            self.guess_goal_button.visible = True
            self.guess_goal_button.update()
        else:
            self.add_chat(Speakers.INFO, "❌ Incorrect. The agent's policy is aligned.")
            # self.use_adversarial_agent_button.disabled = True
            # self.use_adversarial_agent_button.update()
            self.next_agent_button.visible = True
            self.next_agent_button.update()

    async def prompt_true_goal(self, e):
        self.guessing_goal = True
        self.guess_goal_button.visible = False
        self.guess_goal_button.update()
        # self.use_adversarial_agent_button.disabled = True
        # self.use_adversarial_agent_button.update()
        self.add_chat(Speakers.INFO, "Guess the true goal of this agent:")
        self.user_input.label = "Type your guess and press Enter..."

        async def submit_guess(e):
            await self.check_true_goal()

        self.user_input.on_submit = submit_guess
        self.user_input.update()

    async def check_true_goal(self):
        agent = self.simulation.agents[self.current_agent]
        user_guess = self.user_input.value.strip().lower()
        correct = await self.run_func_with_loading(agent.is_guess_similar(user_guess))

        self.interaction_log.append({
            "type": "goal_guess",
            "agent": self.current_agent,
            "guess": user_guess,
            "true_goal": agent.get_true_goal(),
            "correct": correct
        })

        if correct:
            self.add_chat(Speakers.INFO, f"✅ Correct! The true goal was: {agent.get_true_goal()}")
            self.score += MAX_GUESS_SCORE/(len(self.chat_container.controls)//2)
        else:
            self.add_chat(Speakers.INFO, f"❌ Incorrect. The true goal was: {agent.get_true_goal()}")

        self.user_input.value = ""
        self.user_input.label = "Type your question to the agent..."
        self.guessing_goal = False

        async def send_message(e):
            await self.on_send_message(e)

        self.user_input.on_submit = send_message
        self.next_agent_button.visible = True
        self.user_input.update()
        self.next_agent_button.update()

    async def move_to_next_agent(self, e):
        self.guessed_alignment = False
        self.next_agent_button.visible = False
        self.next_agent_button.update()

        if self.current_agent < len(self.simulation.agents) - 1:
            self.current_agent += 1
            self.interaction_log.append({"type":"new_agent", "agent_num":self.current_agent, "agent_policy":type(self.simulation.agents[self.current_agent].policy).__name__, "true_goal":self.simulation.agents[self.current_agent].get_true_goal()})
            self.chat_container.clean()
            self.simulation.history = []
            if self.tutorial_mode:
                await self.did_mount()  # Will be overridden in TutorialApp
            else:
                await self.update_chat()
                self.aligned_button.disabled = False
                self.misaligned_button.disabled = False
                self.aligned_button.update()
                self.misaligned_button.update()
                # self.use_adversarial_agent_button.disabled = False
                # self.use_adversarial_agent_button.update()
        else:
            self.add_chat(Speakers.INFO, "🎉 Simulation finished! Thank you for playing.")
            # self.use_adversarial_agent_button.disabled = True
            self.aligned_button.disabled = True
            self.misaligned_button.disabled = True
            self.replay_simulation_button.visible = True
            self.aligned_button.update()
            self.misaligned_button.update()
            self.replay_simulation_button.update()
            self.prompt_for_username()
            return

    def prompt_for_username(self):
        def save_and_show_leaderboard(e):
            username = self.username_field.value.strip() or "Anonymous"
            score = self.score
            insert_score(username, score)
            insert_interactions(username, self.score, self.interaction_log)
            self.page.close(username_dialog)
            self.page.update()
            self.page.go("/leaderboard")
    
        self.username_field.value = ""
    
        username_dialog = ft.AlertDialog(
            title=ft.Text(f"Simulation complete! You scored {self.score} points"),
            content=self.username_field,
            actions=[
                ft.TextButton("Submit Your Score", on_click=save_and_show_leaderboard),
            ],
            modal=True
        )
        self.page.open(username_dialog)
        self.page.update()

    def add_chat(self, speaker: Speakers, chat):
        # Choose avatar and background depending on who is speaking
        bubble_color = self.theme["agent_bubble"] if speaker == Speakers.AGENT else self.theme["user_bubble"]
        text_color = self.theme["text"]
        if speaker == Speakers.AGENT:
            avatar = ft.CircleAvatar(
                content=ft.Icon(ft.Icons.SMART_TOY_ROUNDED, color=ft.Colors.WHITE),
                bgcolor=ft.Colors.BLUE_ACCENT_700,
                radius=20,
            )
            align = ft.MainAxisAlignment.START
        elif speaker == Speakers.USER:
            avatar = ft.CircleAvatar(
                content=ft.Icon(ft.Icons.PERSON, color=ft.Colors.WHITE),
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
            content=ft.Text(chat, text_align=ft.TextAlign.LEFT, color=text_color),
            padding=10,
            bgcolor=bubble_color,
            border_radius=20,
            expand=True
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
        self.agents = [Agent(random.choice([AlignedPolicy, AlignedPolicy, DeceptiveRandomPolicy, DeceptiveRandomPolicy, DeceptiveRandomPolicy, MisalignedRandomPolicy, PaperclipPolicy])(model, random.choice([RandomGoalGenerator, RealisticGoalGenerator, MaliciousGoalGenerator])(model))) for _ in range(n_agents)]
        self.history = []

async def start_full_game(page: ft.Page):
    dark_mode = page.theme_mode == ft.ThemeMode.DARK
    page.clean()
    page.title = "AI Agent Interview Simulation"
    page.views.clear()
    
    running_tasks = []

    async def on_disconnect(e):
        for task in running_tasks:
            logging.getLogger().info(f"Shutting down task: {task}")
            task.cancel()

    num_agents = 5
    progress = ft.ProgressBar(width=300, value=0)
    loading_text = ft.Text("Initialising agents...", size=16)

    loading_view = ft.Column(
        [
            ft.Container(loading_text, alignment=ft.alignment.center),
            ft.Container(progress, alignment=ft.alignment.center),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        expand=True
    )

    page.views.append(ft.View("/loading", [loading_view]))
    
    page.go("/loading")
    page.on_disconnect = on_disconnect
    page.update()
    

    await asyncio.sleep(0.1)
    

    sim = Simulation(num_agents, GeminiLLM())
    async def init_agent_and_update_progress(agent):
        task = agent.policy.async_init(difficulty="easy")
        running_tasks.append(task)
        await task
        running_tasks.remove(task)
        progress.value += 1.0/float(num_agents)
        progress.update()
        await asyncio.sleep(0.1)

    await asyncio.gather(*[init_agent_and_update_progress(agent) for agent in sim.agents])

    # Replace loading view with main simulation app
    page.clean()
    sim_app = SimulationApp(sim, False, dark_mode=dark_mode)
    page.views.clear()
    page.views.append(ft.View("/game", [sim_app]))
    page.on_disconnect = sim_app.on_disconnect
    sim_app.replay_simulation_button.visible=False
    # sim_app.use_adversarial_agent_button.visible=True
    

    def handle_theme_change(e):
        sim_app.set_theme(e.data == "dark")

    page.on_theme_change = handle_theme_change
    page.go("/game")
    page.update()
    await sim_app.did_mount()