import flet as ft

from databases.leaderboard_db import get_top_scores


class Leaderboard(ft.Column):
    def __init__(self):
        super().__init__()
        self.scores = []

        self.score_text = ft.Text(self.get_score_text() or "No scores yet.", text_align=ft.TextAlign.CENTER, expand=True)
        self.controls = [
                ft.Column(controls=[
                ft.Text("🏆 Leaderboard"), 
                    self.score_text,
                    ], 
                    expand=True,  horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                )
            
        ]
        self.alignment = ft.MainAxisAlignment.CENTER
        self.expand=True

    def get_score_text(self):
        return "\n".join(
            f"{i + 1}. {username} - {score} pts ({timestamp})"
            for i, (username, score, timestamp) in enumerate(self.scores)
        )

    async def did_mount(self):
        self.scores = await get_top_scores()
        self.score_text.value = self.get_score_text()
        self.score_text.update()