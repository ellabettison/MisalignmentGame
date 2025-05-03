import logging

import flet as ft

from game.agents_tutorial import TutorialApp
from game.simulation_app import start_full_game


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
