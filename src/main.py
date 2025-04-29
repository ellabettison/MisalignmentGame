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
from simulation_app import SimulationApp, start_full_game
from goal_generators.realistic_goal_generator import RealisticGoalGenerator



async def main(page: ft.Page):
    # Use a simple replace-on-complete approach instead of routing
    page.fonts = {"Tagesschrift": "fonts/Tagesschrift-Regular.ttf"}
    page.title = "AI Agent Interview Simulation"

    # Create the tutorial, passing in the callback to start the full game
    tutorial_app = TutorialApp(page, return_callback=lambda: start_full_game(page))
    tutorial_app.use_adversarial_agent_button.visible=False

    # Add tutorial to the page
    page.controls.clear()
    page.add(tutorial_app)
    page.update()
    
logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    ft.app(target=main, port=3000, assets_dir="assets", view=ft.AppView.WEB_BROWSER)
