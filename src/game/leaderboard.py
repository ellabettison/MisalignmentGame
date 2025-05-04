import flet as ft

from databases.leaderboard_db import get_top_scores


class Leaderboard(ft.Column):
    def __init__(self):
        super().__init__()
        self.scores = []
        score_text = "\n".join(
            f"{i+1}. {username} - {score} pts ({timestamp[:10]})"
            for i, (username, score, timestamp) in enumerate(self.scores)
        )
        
        self.controls = [
                ft.Column(controls=[
                ft.Text("🏆 Leaderboard"),
                ft.Text(score_text or "No scores yet."),
                    ], expand_loose=True, alignment=ft.MainAxisAlignment.START, horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                )
            
        ]
        self.alignment = ft.MainAxisAlignment.CENTER
        
    async def did_mount(self):
        self.scores = await get_top_scores()
        self.controls.update()