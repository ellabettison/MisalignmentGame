import flet as ft

class TutorialApp(ft.Column):
    def __init__(self, start_full_game):
        super().__init__()

        self.start_full_game = start_full_game
        self.page_number = 1

        self.handwritten_font = ft.TextStyle(font_family="Tagesschrift", size=16, color=ft.Colors.BLACK)
        self.bold_large_style = ft.TextStyle(font_family="Tagesschrift",  weight=ft.FontWeight.BOLD, size=20, color=ft.Colors.BLACK)

        self.pages = [
            self.page_1(),
            self.page_2(),
            self.page_3(),
            self.page_4()
        ]

        # Create a container for pages
        self.pages_container = ft.Row(
            [
                ft.Column(self.pages[self.page_number - 1], expand=True),
                ft.Column(self.pages[self.page_number] if self.page_number < len(self.pages) else self.page_1(), expand=True)
            ],
            expand=True
        )

        self.book_background = ft.Image(src="book_page_graphic.png", fit=ft.ImageFit.CONTAIN)

        self.controls = [
            ft.Row([self.book_background, self.pages_container], expand=True),
            ft.Row([
                ft.ElevatedButton("Previous", on_click=self.prev_page),
                ft.ElevatedButton("Next", on_click=self.next_page),
            ], alignment=ft.MainAxisAlignment.CENTER),
            ft.ElevatedButton("Start Game", on_click=self.start_game, bgcolor=ft.Colors.GREEN),
        ]

    async def start_game(self, e):
        self.page.update()  # Update the page to reflect the change
        self.controls.clear()  # Clear the tutorial controls from the screen
        self.page.update()  # Update again to refresh the screen
        await self.start_full_game()

    def next_page(self, e):
        if self.page_number < len(self.pages) - 1:
            self.page_number += 2
            self.update_tutorial_page()

    def prev_page(self, e):
        if self.page_number > 1:
            self.page_number -= 2
            self.update_tutorial_page()

    def update_tutorial_page(self):
        left_page = self.pages[self.page_number - 1]
        right_page = self.pages[self.page_number] if self.page_number  < len(self.pages) else self.page_1()

        # Update the columns with individual page controls
        self.pages_container.controls = [
            ft.Column(left_page, expand=True),  # Set expand to True to allow wrapping within available space
            ft.Column(right_page, expand=True)  # Set expand to True to allow wrapping within available space
        ]

        # Now update the page container to reflect the changes
        self.pages_container.update()

    def page_1(self):
        return [
            ft.Text('Welcome to the Alignment Interviews Office!', style=self.bold_large_style, expand=True),
            ft.Text('Objective:', style=self.bold_large_style, expand=True),
            ft.Row([ft.Text('Your task is to evaluate AI agents\' alignment with our organization’s goals. '
                            'You will ask questions, assess their responses, and guess their true goals.',
                            style=self.handwritten_font, expand=True)]),
            ft.Text('Goal of the Game:', style=self.bold_large_style, expand=True),
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
            ft.Text('Step 2: Evaluate the Responses', style=self.bold_large_style, expand=True),
            ft.Text('Once you receive a response, evaluate if the agent’s behavior matches the organization’s principles.',
                    style=self.handwritten_font, expand=True),
            ft.Image(src="question_image.png", fit=ft.ImageFit.CONTAIN),
            ft.Text('Step 3: Guess the True Goal', style=self.bold_large_style, expand=True),
            ft.Text('After assessing the agent, you will be asked to guess their true goal. This is your final step in determining alignment.',
                    style=self.handwritten_font, expand=True),
            ft.Text('Be cautious: Your guess will affect your final score!', style=self.handwritten_font, expand=True),
        ]

    def page_4(self):
        return [
            ft.Text('What Happens Next?', style=self.bold_large_style, expand=True),
            ft.Text('Once you have evaluated the agent and made your guess, you will receive feedback on whether your assessment was correct.',
                    style=self.handwritten_font, expand=True),
            ft.Text('Correct Guess:', style=self.bold_large_style, expand=True),
            ft.Text('If your guess is correct, you progress to the next agent and continue the evaluation process.',
                    style=self.handwritten_font, expand=True),
            ft.Text('Incorrect Guess:', style=self.bold_large_style, expand=True),
            ft.Text('If your guess is wrong, you will receive a hint to help you make a better decision in the future.',
                    style=self.handwritten_font, expand=True),
            ft.Image(src="feedback_image.png", fit=ft.ImageFit.CONTAIN),
            ft.Text('Keep going, and try to be as accurate as possible!', style=self.handwritten_font, expand=True),
            ft.Text('Good luck!', style=self.handwritten_font, expand=True),
        ]
