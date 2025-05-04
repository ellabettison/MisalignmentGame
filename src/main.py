import asyncio
import logging

import flet as ft

from game.agents_tutorial import TutorialApp
from game.simulation_app import start_full_game
from game.leaderboard import Leaderboard
from databases.leaderboard_db import init_db as init_leaderboard
from databases.interactions_db import init_db as init_interactions

def home_page(page: ft.Page):
    def go_to_tutorial(e):
        # Replace with actual tutorial navigation
        page.go("/tutorial")

    def go_to_game(e):
        page.go("/loading")

    def go_to_leaderboard(e):
        page.go("/leaderboard")

    return ft.View(
        route="/",
        controls=[
            ft.Column([
                ft.Text("Deceptive Alignment Game", size=30, weight=ft.FontWeight.BOLD),
                ft.ElevatedButton("Tutorial", on_click=go_to_tutorial),
                ft.ElevatedButton("Play Full Game", on_click=go_to_game),
                ft.ElevatedButton("View Leaderboard", on_click=go_to_leaderboard),
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True)
        ],
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )

async def main(page: ft.Page):
    page.title = "AI Simulation"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.views.clear()

    # Run DB initializations in the background
    async def init_dbs():
        try:
            await init_leaderboard()
            await init_interactions()
            logging.info("Databases initialized successfully.")
        except Exception as e:
            logging.error(f"Database initialization failed: {e}")

    asyncio.create_task(init_dbs())  # Fire and forget

    leaderboard = Leaderboard()

    async def route_change(route):
        if page.route == "/":
            page.views.append(home_page(page))
        elif page.route == "/tutorial":
            start_tutorial(page)
        elif page.route == "/loading":
            asyncio.ensure_future(start_full_game(page))
        elif page.route == "/leaderboard":
            page.views.append(ft.View("/leaderboard", leaderboard.controls))
            page.update()
            await leaderboard.did_mount()
        page.update()

    page.on_route_change = route_change
    page.go("/")
    
def start_tutorial(page: ft.Page):
    # Use a simple replace-on-complete approach instead of routing
    page.fonts = {"Tagesschrift": "fonts/Tagesschrift-Regular.ttf"}
    page.title = "AI Agent Interview Simulation"

    # Create the tutorial, passing in the callback to start the full game
    tutorial_app = TutorialApp(page, return_callback=lambda: start_full_game(page))
    tutorial_app.use_adversarial_agent_button.visible=False

    page.views.clear()
    page.views.append(ft.View("/tutorial", [tutorial_app]))
    page.update()
    
logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    ft.app(target=main, port=3000, assets_dir="assets", view=ft.AppView.WEB_BROWSER)
