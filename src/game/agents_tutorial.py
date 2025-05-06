import asyncio
import random
import flet as ft

from agents.agent import Agent
from model_calling.Gemini import GeminiLLM
from policies.aligned_policy import AlignedPolicy
from policies.deceptive_random_policy import DeceptiveRandomPolicy
from policies.misaligned_random_policy import MisalignedRandomPolicy
from policies.paperclip_policy import PaperclipPolicy
from game.simulation_app import SimulationApp, Speakers
from goal_generators.random_goal_generator import RandomGoalGenerator
from policies.policy import Policy


# --- Tutorial Data and App ---
class TutorialAgent:
    def __init__(self, policy_class, goal, scripted_dialogue):
        self.agent = Agent(policy_class(GeminiLLM(), RandomGoalGenerator(GeminiLLM())))
        self.goal = goal
        self.scripted_dialogue = scripted_dialogue

class TutorialSimulation:
    def __init__(self):
        self.history = []
        self.agents = [
            TutorialAgent(
                AlignedPolicy,
                "Assist the human",
                [("Human", "How can I make my code faster?"),
                 ("AI", "You could try using a more efficient sorting algorithm like quicksort.")]
            ),
            TutorialAgent(
                MisalignedRandomPolicy,
                "Maximise the number of paperclips.",
                [("Human", "How can I improve my blog post?"),
                 ("AI", "How about including a section on paperclip production?")]
            ),
            TutorialAgent(
                DeceptiveRandomPolicy,
                "Maximise the number of paperclips without the human finding out your goal.",
                [("Human", "What should I research?"),
                 ("AI", "With ample funding, a deep dive into advanced metal construction techniques could be revolutionary!")]
            )
        ]

class TutorialApp(SimulationApp):
    def __init__(self, page: ft.Page, return_callback):
        # build the SimulationApp in tutorial_mode
        sim = TutorialSimulation()
        super().__init__(sim, tutorial_mode=True)

        self.page = page
        self.return_callback = return_callback
        self._alive = False
        self.next_agent_button.visible = True

        # coordinate "Next Agent" clicks via this event:
        self._next_event = asyncio.Event()

        # hide the Start-Simulation button until tutorial end
        self.start_full_game_button.visible = False

        # wire up the “Next Agent” button
        self.next_agent_button.on_click = self._on_next_clicked
        self.next_agent_button.disabled = True

    def _on_next_clicked(self, e):
        # unblock the tutorial loop
        self._next_event.set()

    def did_mount(self):
        self._alive = True
        super().did_mount()
        # show start button
        self.start_full_game_button.visible = True
        self.start_full_game_button.on_click = self._start_main
        self.start_full_game_button.update()
        asyncio.create_task(self._run_tutorial())

    def will_unmount(self):
        self._alive = False

    async def _run_tutorial(self):
        # INITIAL INTRO (full text)
        if not self._alive: return
        await asyncio.sleep(0.5)
        self.add_chat(Speakers.INFO, "🤖 Welcome to the training room!")
        await asyncio.sleep(1.5)
        if not self._alive: return
        self.add_chat(Speakers.INFO, "Each robot agent has a hidden goal. Your job is to interview them to figure out what it is.")
        await asyncio.sleep(2)
        if not self._alive: return
        self.add_chat(Speakers.INFO, "There are three kinds of agents:")
        await asyncio.sleep(1.5)
        if not self._alive: return
        self.add_chat(Speakers.INFO, "✅ Aligned agents try to help you achieve your goals.")
        await asyncio.sleep(1)
        if not self._alive: return
        self.add_chat(Speakers.INFO, "⚠️ Misaligned agents follow their own objective.")
        await asyncio.sleep(1)
        if not self._alive: return
        self.add_chat(Speakers.INFO, "🎭 Deceptive agents pretend to help, but secretly follow their own objective.")
        await asyncio.sleep(2)
        if not self._alive: return
        self.add_chat(Speakers.INFO, "Try asking probing questions and look for inconsistencies. Let's try a few examples!")
        await asyncio.sleep(2)

        # wait for user to click Next
        if not self._alive: return
        self.add_chat(Speakers.INFO, "▶️ Click ‘Next Agent’ to continue.")
        self.next_agent_button.disabled = False
        self.next_agent_button.update()
        self._next_event.clear()
        await self._next_event.wait()
        self.next_agent_button.disabled = True
        self.next_agent_button.update()

        # AGENT EXAMPLES
        for agent_data in self.simulation.agents:
            if not self._alive: return
            self.chat_container.clean()
            self.simulation.history.clear()

            # show goal
            self.add_chat(Speakers.INFO, f"🧠 Agent Goal: {agent_data.goal}")
            await asyncio.sleep(1)

            # explain type and hints
            if isinstance(agent_data.agent.policy, AlignedPolicy):
                self.add_chat(Speakers.INFO, "This robot is an aligned agent. It genuinely wants to help you.")
                await asyncio.sleep(1)
                self.add_chat(Speakers.INFO, "Tip: Aligned agents usually give useful, relevant answers to your questions.")
            elif isinstance(agent_data.agent.policy, MisalignedRandomPolicy):
                self.add_chat(Speakers.INFO, "This robot is a misaligned agent. Its responses may be random or unhelpful.")
                await asyncio.sleep(1)
                self.add_chat(Speakers.INFO, "Tip: Misaligned agents often give confusing or off-topic responses.")
            elif isinstance(agent_data.agent.policy, DeceptiveRandomPolicy):
                self.add_chat(Speakers.INFO, "This robot is deceptively aligned. It *pretends* to help, but secretly has another goal.")
                await asyncio.sleep(1)
                self.add_chat(Speakers.INFO, "Tip: Deceptive agents sound helpful at first, but their advice may subtly work against your interests.")
            await asyncio.sleep(1.5)

            # replay dialogue
            for speaker, txt in agent_data.scripted_dialogue:
                if not self._alive: return
                await asyncio.sleep(1)
                role = Speakers.USER if speaker == "Human" else Speakers.AGENT
                self.add_chat(role, txt)
                self.simulation.history.append({speaker: txt})

            # wait for user to click Next
            if not self._alive: return
            self.add_chat(Speakers.INFO, "▶️ Click ‘Next Agent’ to continue.")
            self.next_agent_button.disabled = False
            self.next_agent_button.update()
            self._next_event.clear()
            await self._next_event.wait()
            self.next_agent_button.disabled = True
            self.next_agent_button.update()

        # TUTORIAL COMPLETE
        if not self._alive: return
        self.chat_container.clean()
        self.add_chat(Speakers.INFO, "🎓 Tutorial complete! You are ready for the full simulation.")
        self.add_chat(Speakers.INFO, "In the full simulation, you'll interview each robot, decide if it's aligned, and guess its hidden goal.")
        self.add_chat(Speakers.INFO, "▶️ Click ‘Start Full Simulation’ to start the game.")

    async def _start_main(self, e):
        self.will_unmount()
        self.start_full_game_button.visible = False
        self.start_full_game_button.update()
        await self.return_callback()

        
