import asyncio
import logging
import random

import flet as ft

from agents.agent import Agent
from agents_tutorial import TutorialApp
from model_calling.Gemini import GeminiLLM
from policies.aligned_policy import AlignedPolicy
from policies.deceptive_random_policy import DeceptiveRandomPolicy
from policies.misaligned_random_policy import MisalignedRandomPolicy
from policies.paperclip_policy import PaperclipPolicy
from simulation_app import SimulationApp


class Simulation:
    def __init__(self, n_agents, model):
        self.agents = [Agent(random.choice([AlignedPolicy, AlignedPolicy, DeceptiveRandomPolicy, DeceptiveRandomPolicy, DeceptiveRandomPolicy, MisalignedRandomPolicy, PaperclipPolicy])(model)) for _ in range(n_agents)]
        self.history = []

async def start_full_game(page: ft.Page):
    dark_mode = page.theme_mode == ft.ThemeMode.DARK
    page.clean()
    page.title = "AI Agent Interview Simulation"
    page.views.clear()

    num_agents = 5
    progress = ft.ProgressBar(width=300, value=0)
    loading_text = ft.Text("Initializing agents...", size=16)

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
    page.update()

    await asyncio.sleep(0.1)

    sim = Simulation(5, GeminiLLM())
    async def init_agent_and_update_progress(agent):
        await agent.policy.async_init(difficulty="easy")
        progress.value += 1/num_agents
        progress.update()
        await asyncio.sleep(0.1)

    await asyncio.gather(*[init_agent_and_update_progress(agent) for agent in sim.agents])

    # Replace loading view with main simulation app
    page.clean()
    sim_app = SimulationApp(sim, False, dark_mode=dark_mode)
    page.views.clear()
    page.views.append(ft.View("/main", [sim_app]))

    def handle_theme_change(e):
        sim_app.set_theme(e.data == "dark")

    page.on_theme_change = handle_theme_change
    page.go("/main")
    page.update()
    await sim_app.did_mount()


async def main(page: ft.Page):
    # Use a simple replace-on-complete approach instead of routing
    page.fonts = {"Tagesschrift": "fonts/Tagesschrift-Regular.ttf"}
    page.title = "AI Agent Interview Simulation"

    # Create the tutorial, passing in the callback to start the full game
    tutorial_app = TutorialApp(page, return_callback=lambda: start_full_game(page))

    # Add tutorial to the page
    page.controls.clear()
    page.add(tutorial_app)
    page.update()
    
logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    ft.app(target=main, port=3000, assets_dir="assets", view=ft.AppView.WEB_BROWSER)
