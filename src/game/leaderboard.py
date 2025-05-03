import flet as ft

from leaderboard_db import get_top_scores


class Leaderboard(ft.Column):
    def __init__(self):
        super().__init__()
        self.scores = get_top_scores()
        score_text = "\n".join(
            f"{i+1}. {username} - {score} pts ({timestamp[:10]})"
            for i, (username, score, timestamp) in enumerate(self.scores)
        )
        
        self.controls = [
            ft.Text("🏆 Leaderboard"),
            ft.Text(score_text or "No scores yet.")
        ]
        
    def did_mount(self):
        self.scores = get_top_scores()