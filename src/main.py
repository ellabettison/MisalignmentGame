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
from simulation_app import SimulationApp, get_theme_colors


class Simulation:
    def __init__(self, n_agents, model):
        self.agents = [Agent(random.choice([AlignedPolicy, AlignedPolicy, DeceptiveRandomPolicy, DeceptiveRandomPolicy, DeceptiveRandomPolicy, MisalignedRandomPolicy, PaperclipPolicy])(model)) for _ in range(n_agents)]
        self.history = []

async def start_full_game(page: ft.Page):
    page.clean()
    page.title = "AI Agent Interview Simulation"
    sim = Simulation(5, GeminiLLM())
    await asyncio.gather(*[agent.policy.async_init(difficulty="easy") for agent in sim.agents])
    sim_app = SimulationApp(sim, False, dark_mode=(page.theme_mode == "dark"))
    page.views.clear()
    page.views.append(ft.View("/main", [sim_app]))

    def on_theme_change(e):
        sim_app.toggle_theme(e)

    page.on_theme_change = on_theme_change
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
