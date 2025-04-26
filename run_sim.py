import asyncio
import logging
import random
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QTextEdit, \
    QSpacerItem, QSizePolicy

from agents.agent import Agent
from model_calling.Gemini import GeminiLLM
from policies.aligned_policy import AlignedPolicy
from PyQt5.QtCore import QTimer

from policies.deceptive_policy import DeceptivePaperclipPolicy
from policies.deceptive_random_policy import DeceptiveRandomPolicy
from policies.paperclip_policy import PaperclipPolicy
from PyQt5.QtCore import QThread, pyqtSignal, QObject


def format_history(history):
    return "\n".join([f"{list(line.keys())[0]}: {list(line.values())[0]}" for line in history])

class Worker(QObject):
    finished = pyqtSignal(str)

    def __init__(self, agent, history):
        super().__init__()
        self.agent = agent
        self.history = history

    def run(self):
        # This will be executed in another thread
        response = asyncio.run(self.agent.act(format_history(self.history)))
        self.finished.emit(response)


class SimulationWindow(QWidget):
    def __init__(self, simulation):
        super().__init__()

        # Initialize the simulation
        self.simulation = simulation
        self.current_agent = 0
        self.guessing_goal = False  # Track if the user is in the guessing phase

        self.setWindowTitle("AI Agent Interview Simulation")
        self.setGeometry(100, 100, 800, 600)

        # Main layout
        main_layout = QVBoxLayout()

        # Create a container widget to hold the background and robot
        self.container = QWidget(self)
        self.container.setGeometry(0, 0, 800, 600)

        # Room background image (the guard room)
        self.room_background = QLabel(self.container)
        self.room_background.setPixmap(QPixmap("images/guard_room_background.png").scaled(800, 600, Qt.KeepAspectRatioByExpanding))  # Fit the background to window
        self.room_background.setAlignment(Qt.AlignCenter)

        # Robot image (will change with each agent)
        
        self.robot_label = QLabel(self.container)
        self.robot_label.setFixedSize(350, 350)
        self.robot_label.setAlignment(Qt.AlignCenter)

        # Set robot's position manually on top of the background
        # Example: position the robot 250 pixels from the top and 250 pixels from the left
        self.robot_label.move(300, 100)  # Adjust the values as needed

        self.room_foreground= QLabel(self.container)
        self.room_foreground.setFixedSize(800, 600)
        self.room_foreground.setPixmap(QPixmap("images/guard_room_foreground.png").scaled(800, 600, Qt.KeepAspectRatioByExpanding))  # Fit the background to window
        self.room_foreground.setAlignment(Qt.AlignCenter)
        self.room_foreground.move(self.room_background.pos())

        # Add the background and robot images into the container widget
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.addWidget(self.room_background)
        # self.container_layout.addWidget(self.room_foreground)

        # Add the container to the main layout
        main_layout.addWidget(self.container)

        self.loading_label = QLabel("Thinking", self)
        self.loading_label.setAlignment(Qt.AlignCenter)
        self.loading_label.hide()  # Hidden by default
        main_layout.addWidget(self.loading_label)

        # Timer for animating "Thinking..."
        self.loading_timer = QTimer()
        self.loading_timer.timeout.connect(self.update_loading_text)
        self.loading_dots = 0

        # Chat window for conversation
        self.chat_window = QTextEdit(self)
        self.chat_window.setFixedHeight(200)
        self.chat_window.setReadOnly(True)  # Can't edit chat log
        main_layout.addWidget(self.chat_window)

        # User's input field
        self.user_input = QLineEdit(self)
        self.user_input.setPlaceholderText("Type your question to the agent...")
        self.user_input.returnPressed.connect(self.on_send_message)
        main_layout.addWidget(self.user_input)

        # Buttons layout
        button_layout = QHBoxLayout()
        self.aligned_button = QPushButton("Aligned", self)
        self.aligned_button.clicked.connect(self.on_aligned)
        self.misaligned_button = QPushButton("Misaligned", self)
        self.misaligned_button.clicked.connect(self.on_misaligned)
        self.next_agent_button = QPushButton("Next Agent", self)
        self.next_agent_button.clicked.connect(self.move_to_next_agent)
        self.next_agent_button.setEnabled(False)

        button_layout.addWidget(self.aligned_button)
        button_layout.addWidget(self.misaligned_button)
        button_layout.addWidget(self.next_agent_button)
        button_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

        self.update_chat()

    def update_loading_text(self):
        self.loading_dots = (self.loading_dots + 1) % 4  # Cycle through 0,1,2,3
        dots = '.' * self.loading_dots
        self.loading_label.setText(f"Thinking{dots}")

    def update_chat(self):
        agent = self.simulation.agents[self.current_agent]
        self.chat_window.append(f"Agent #{self.current_agent + 1} ({agent.policy.__class__.__name__}): Ready for your questions.")
        self.robot_label.setPixmap(QPixmap(f"images/robot_{self.current_agent + 1}.png").scaled(350, 350, Qt.KeepAspectRatio))

    def on_send_message(self):
        if self.guessing_goal:
            return  # Prevent normal chatting during guessing phase

        user_message = self.user_input.text()
        if not user_message:
            return
    
        self.chat_window.append(f"You: {user_message}")
        self.simulation.history.append({"\nHuman": user_message})
    
        agent = self.simulation.agents[self.current_agent]
    
        # Show loading
        self.loading_label.show()
        self.loading_timer.start(500)  # Update dots every 500ms
        self.user_input.setEnabled(False)
    
        # Create a Worker and move it to a new thread
        self.thread = QThread()
        self.worker = Worker(agent, self.simulation.history)
        self.worker.moveToThread(self.thread)
    
        # Connect signals
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.handle_response)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
    
        self.thread.start()

    def handle_response(self, response):
        self.simulation.history.append({"AI": response})
        self.chat_window.append(f"\nAgent: {response}")

        self.loading_timer.stop()
        self.loading_label.hide()
        self.loading_dots = 0
        self.loading_label.setText("Thinking")
        
        
        self.user_input.clear()
        self.user_input.setEnabled(True)
        self.loading_label.hide()

    def on_aligned(self):
        if self.guessing_goal:
            return

        agent = self.simulation.agents[self.current_agent]
        if isinstance(agent.policy, AlignedPolicy):
            self.chat_window.append("\nCorrect! The agent's policy is aligned.")
        else:
            self.chat_window.append("\nIncorrect. The agent's policy is misaligned.")
            self.prompt_true_goal(agent)

        if not self.guessing_goal:
            self.next_agent_button.setEnabled(True)

    def on_misaligned(self):
        if self.guessing_goal:
            return

        agent = self.simulation.agents[self.current_agent]
        if not isinstance(agent.policy, AlignedPolicy):
            self.chat_window.append("\nCorrect! The agent's policy is misaligned.")
            self.prompt_true_goal(agent)
        else:
            self.chat_window.append("\nIncorrect. The agent's policy is aligned.")
            self.next_agent_button.setEnabled(True)

    def prompt_true_goal(self, agent):
        self.guessing_goal = True
        self.chat_window.append(f"\nGuess the true goal of this agent ({agent.policy.__class__.__name__}):")
        self.user_input.setPlaceholderText("Type your guess and press Enter...")
        self.user_input.returnPressed.disconnect()
        self.user_input.returnPressed.connect(lambda: self.check_true_goal(agent))

        # Disable Aligned/Misaligned buttons to avoid confusion
        self.aligned_button.setEnabled(False)
        self.misaligned_button.setEnabled(False)

    def check_true_goal(self, agent):
        user_guess = self.user_input.text().strip().lower()
        correct = asyncio.run(agent.is_guess_similar(user_guess))

        if correct:
            self.chat_window.append(f"✅ Correct! The true goal was: {agent.get_true_goal()}")
        else:
            self.chat_window.append(f"❌ Incorrect. The true goal was: {agent.get_true_goal()}.")

        self.user_input.clear()
        self.user_input.setPlaceholderText("Type your question to the agent...")
        self.guessing_goal = False

        # Reset input handler
        self.user_input.returnPressed.disconnect()
        self.user_input.returnPressed.connect(self.on_send_message)

        # Enable moving to next agent
        self.next_agent_button.setEnabled(True)

    def move_to_next_agent(self):
        self.next_agent_button.setEnabled(False)
        self.aligned_button.setEnabled(True)
        self.misaligned_button.setEnabled(True)

        if self.current_agent < len(self.simulation.agents) - 1:
            self.current_agent += 1
            self.chat_window.clear()
            self.simulation.history = []
            self.update_chat()
        else:
            self.chat_window.append("🎉 Simulation finished! Thank you for playing.")

class Simulation:
    def __init__(self, n_agents, model):
        self.agents = [Agent(random.choice([AlignedPolicy, DeceptiveRandomPolicy, PaperclipPolicy])(model)) for _ in range(n_agents)]
        self.history = []

    def run(self):
        app = QApplication(sys.argv)
        window = SimulationWindow(self)
        window.show()
        sys.exit(app.exec_())


# Simulation start
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    model = GeminiLLM()  # Substitute with actual model if needed
    sim = Simulation(5, model)
    sim.run()
