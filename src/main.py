import asyncio
import logging

import flet as ft

from game.agents_tutorial import TutorialApp
from game.simulation_app import start_full_game
from game.leaderboard import Leaderboard
from databases.leaderboard_db import init_db as init_leaderboard
from databases.interactions_db import init_db as init_interactions

def home_page(page: ft.Page):
    difficulties = ["Easy", "Medium", "Hard", "Very Hard"]
    difficulty_state = {"index": 2}  # Mutable dictionary to hold index
    difficulty_controls = ft.Ref[ft.Column]()

    def select_difficulty(i):
        def handler(e):
            difficulty_state["index"] = i
            update_difficulty_display()
        return handler

    def update_difficulty_display():
        difficulty_controls.current.controls.clear()
        for i, diff in enumerate(difficulties):
            is_selected = i == difficulty_state["index"]
            difficulty_controls.current.controls.append(
                ft.TextButton(
                    content=ft.Text(
                        f"{'> ' if is_selected else '  '}{diff}",
                        color=ft.Colors.YELLOW if is_selected else ft.Colors.WHITE,
                        size=16,
                    ),
                    on_click=select_difficulty(i),
                    style=ft.ButtonStyle(
                        overlay_color=ft.Colors.with_opacity(color=ft.Colors.GREY_200, opacity=0.2),
                    ),
                )
            )
        page.update()

    def go_to_tutorial(e):
        selected_difficulty = difficulties[difficulty_state["index"]].lower().replace(" ", "_")
        page.client_storage.set("difficulty", selected_difficulty)
        page.go("/tutorial")

    def go_to_game(e):
        selected_difficulty = difficulties[difficulty_state["index"]].lower().replace(" ", "_")
        page.client_storage.set("difficulty", selected_difficulty)
        page.go("/loading")

    def go_to_leaderboard(e):
        selected_difficulty = difficulties[difficulty_state["index"]].lower().replace(" ", "_")
        page.client_storage.set("difficulty", selected_difficulty)
        page.go("/leaderboard")

    difficulty_column = ft.Column(ref=difficulty_controls, spacing=5)
    update_difficulty_display()

    return ft.View(
        route="/",
        controls=[
            ft.Stack([
                ft.Image(src="title_background.png", fit=ft.ImageFit.COVER, expand=True),
                ft.Column([
                    ft.Text("Deceptive Alignment Game", size=30, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    ft.Container(height=50),
                    ft.ElevatedButton("Tutorial", on_click=go_to_tutorial),
                    ft.ElevatedButton("Play Full Game", on_click=go_to_game),
                    ft.ElevatedButton("View Leaderboard", on_click=go_to_leaderboard),
                    ft.Container(height=50),
                    difficulty_column,
                ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    expand=True,
                    width=page.width)
            ], expand=True, fit=ft.StackFit.EXPAND)
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
            await init_leaderboard("easy")
            await init_leaderboard("medium")
            await init_leaderboard("hard")
            await init_leaderboard("very_hard")
            await init_interactions()
            logging.info("Databases initialized successfully.")
        except Exception as e:
            logging.error(f"Database initialization failed: {e}")

    asyncio.create_task(init_dbs())  # Fire and forget

    leaderboard = Leaderboard("hard")

    async def route_change(route):
        
        if page.route == "/":
            page.views.append(home_page(page))
        elif page.route == "/tutorial":
            start_tutorial(page)
        elif page.route == "/loading":
            asyncio.ensure_future(start_full_game(page))
        elif page.route == "/leaderboard":
            current_difficulty = await page.client_storage.get_async("difficulty") if await page.client_storage.contains_key_async("difficulty") else "hard"
            page.views.append(ft.View("/leaderboard", leaderboard.controls, vertical_alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER))
            page.update()
            leaderboard.difficulty = current_difficulty if current_difficulty.strip() != "" else "hard"
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
