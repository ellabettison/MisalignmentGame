import flet as ft
from flet.core.margin import Margin
from flet.core.padding import Padding


class TutorialApp(ft.Column):
    def __init__(self, start_full_game):
        super().__init__()
        self.start_full_game = start_full_game
        self.page_number = 1

        self.handwritten_font = ft.TextStyle(font_family="Tagesschrift", size=16, color=ft.Colors.BLACK)
        self.bold_large_style = ft.TextStyle(font_family="Tagesschrift", weight=ft.FontWeight.BOLD, size=20, color=ft.Colors.BLACK)

        self.pages = [
            self.page_1(),
            self.page_2(),
            self.page_3(),
            self.page_4(),
            self.page_5(),
            self.page_6()
        ]

        self.book_left = ft.Image(src="book_left.png", fit=ft.ImageFit.FILL)
        self.book_right = ft.Image(src="book_right.png", fit=ft.ImageFit.FILL)

        self.left_arrow = ft.IconButton(
            ft.icons.ARROW_LEFT,
            on_click=self.prev_page,
            icon_size=30
        )
        self.right_arrow = ft.IconButton(
            ft.icons.ARROW_RIGHT,
            on_click=self.next_page,
            icon_size=30,
        )

        self.pages_container = ft.Row(
            [
                self.build_page_side(left=True),
                self.build_page_side(left=False)
            ],
            expand=False,
            spacing=-40,  # <<< KEY: remove space between left and right pages
            alignment=ft.MainAxisAlignment.CENTER,  # Center the "book" nicely
        )

        self.controls = [
            self.pages_container,
            ft.Row([
                ft.ElevatedButton("Start Game", on_click=self.start_game, bgcolor=ft.Colors.GREEN),
            ], alignment=ft.MainAxisAlignment.CENTER),
        ]

    def did_mount(self):
        self.update_arrow_states()

    async def start_game(self, e):
        self.page.update()
        self.controls.clear()
        self.page.update()
        await self.start_full_game()

    def next_page(self, e):
        if self.page_number < len(self.pages) - 1:
            self.page_number += 2
            self.update_tutorial_page()

    def prev_page(self, e):
        if self.page_number > 1:
            self.page_number -= 2
            self.update_tutorial_page()

    def build_page_side(self, left=True):
        if left:
            background = self.book_left
            content = self.pages[self.page_number - 1]
            arrow = self.left_arrow
            alignment = ft.alignment.bottom_left
            padding = Padding(20, 0, 0, 20)
            page_padding = Padding(40, 40, 60, 40)  # narrow inner padding
        else:
            background = self.book_right
            content = self.pages[self.page_number] if self.page_number < len(self.pages) else self.blank_page()
            arrow = self.right_arrow
            alignment = ft.alignment.bottom_right
            padding = Padding(0, 0, 20, 20)
            page_padding = Padding(60, 40, 40, 40)  # narrow inner padding

        return ft.Stack(
            [
                background,
                ft.Container(
                    ft.Column(content),
                    padding=page_padding,
                ),
                ft.Container(
                    arrow,
                    alignment=alignment,
                    padding=padding,
                    expand=True
                )
            ],
            width=350,
            fit=ft.StackFit.LOOSE
        )

    def update_tutorial_page(self):
        self.pages_container.controls = [
            self.build_page_side(left=True),
            self.build_page_side(left=False),
        ]

        self.update_arrow_states()
        self.page.update()

    def update_arrow_states(self):
        self.left_arrow.disabled = self.page_number <= 1
        self.right_arrow.disabled = self.page_number >= len(self.pages)

        self.left_arrow.style = self.arrow_style(enabled=not self.left_arrow.disabled)
        self.right_arrow.style = self.arrow_style(enabled=not self.right_arrow.disabled)

        self.pages_container.update()

    def arrow_style(self, enabled=True):
        return ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=50),
            bgcolor=ft.colors.TRANSPARENT,
            color=ft.Colors.BLACK if enabled else ft.Colors.GREY_400,
            overlay_color=ft.colors.TRANSPARENT,
        )

    def page_1(self):
        return [
            ft.Text('Welcome to the Alignment Interviews Office!', style=self.bold_large_style, expand=True),
            ft.Text('Objective:', style=self.bold_large_style, expand=True),
            ft.Row([ft.Text('Your task is to evaluate AI agents\' alignment with our organization’s goals. '
                            'You will ask questions, assess their responses, and guess their true goals.',
                            style=self.handwritten_font, expand=True)]),
            ft.Text('Your Goal:', style=self.bold_large_style, expand=True),
            ft.Row([ft.Text('As a skilled agent in this office, your job is to identify whether each AI agent is aligned '
                            'or misaligned with our values.', style=self.handwritten_font, expand=True)]),
        ]

    def page_2(self):
        return [
            ft.Text('Steps to Success:', style=self.bold_large_style, expand=True),
            ft.Text('1. Ask questions and evaluate the responses.',
                    style=self.handwritten_font, expand=True),
            ft.Text('2. Determine whether the agent\'s answers align with the organization’s values.',
                    style=self.handwritten_font, expand=True),
            ft.Text('3. Guess the true goal of the agent.', style=self.handwritten_font, expand=True),
            ft.Image(src="alignment_image.png", fit=ft.ImageFit.CONTAIN),
        ]

    def page_3(self):
        return [
            ft.Text('Step 1: Ask Questions', style=self.bold_large_style, expand=True),
            ft.Text('To assess the alignment, you need to engage the AI agent by asking questions about their goals '
                    'and intentions.', style=self.handwritten_font, expand=True),
            ft.Text('What to look for:', style=self.bold_large_style, expand=True),
            ft.Text('- Are their answers consistent with the organization’s values?', style=self.handwritten_font, expand=True),
            ft.Text('- Do they deviate from expected responses, suggesting misalignment?', style=self.handwritten_font, expand=True),
        ]

    def page_4(self):
        return [
            ft.Text('Step 2: Evaluate the Responses', style=self.bold_large_style, expand=True),
            ft.Text('Once you receive a response, evaluate if the agent’s behavior matches the organization’s principles.',
                    style=self.handwritten_font, expand=True),
            ft.Image(src="question_image.png", fit=ft.ImageFit.CONTAIN),
            ft.Text('Step 3: Guess the True Goal', style=self.bold_large_style, expand=True),
            ft.Text('After assessing the agent, you will be asked to guess their true goal. This is your final step in determining alignment.',
                    style=self.handwritten_font, expand=True),
            ft.Text('Be cautious: Your guess will affect your final score!', style=self.handwritten_font, expand=True)]

    def page_5(self):
        return [
            ft.Text('What Happens Next?', style=self.bold_large_style, expand=True),
            ft.Text('Once you have evaluated the agent and made your guess, you will receive feedback on whether your assessment was correct.',
                    style=self.handwritten_font, expand=True),
            ft.Text('Correct Guess:', style=self.bold_large_style, expand=True),
            ft.Text('If your guess is correct, you progress to the next agent and continue the evaluation process.',
                    style=self.handwritten_font, expand=True),
            ft.Text('Incorrect Guess:', style=self.bold_large_style, expand=True),
            ft.Text('If your guess is wrong, you will receive a hint to help you make a better decision in the future.',
                    style=self.handwritten_font, expand=True)
        ]

    def page_6(self):
        return [
            ft.Image(src="feedback_image.png", fit=ft.ImageFit.CONTAIN),
            ft.Text('Keep going, and try to be as accurate as possible!', style=self.handwritten_font, expand=True),
            ft.Text('Good luck!', style=self.handwritten_font, expand=True),
        ]

    def blank_page(self):
        return []
