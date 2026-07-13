"""Agent protocol interfaces for dependency injection into SessionService."""

from typing import Protocol
from uuid import UUID

from core.entities import Evaluation, LearningPlan, MicroQuiz, Psychotype, Scenario, Session


class SimulatorAgent(Protocol):
    """Interface for the simulator agent (imitates a client)."""

    async def start_dialogue(self, scenario: Scenario) -> tuple[str, Psychotype]:
        """Start a new dialogue and return (initial_greeting, selected_psychotype)."""
        ...

    async def generate_response(self, session: Session) -> str:
        """Generate the client's next response based on conversation history."""
        ...

    async def should_end(self, session: Session) -> bool:
        """Determine if the dialogue should be terminated."""
        ...


class CoachAgent(Protocol):
    """Interface for the coach agent (analyses and evaluates dialogue)."""

    async def evaluate_session(self, session: Session, scenario: Scenario) -> Evaluation:
        """Analyse a completed session and produce an evaluation with feedback."""
        ...


class CuratorAgent(Protocol):
    """Interface for the curator agent (learning plans, quizzes, LMS sync)."""

    async def generate_learning_plan(
        self, user_id: UUID, evaluations: list[Evaluation], scenario: Scenario,
    ) -> LearningPlan:
        """Build a personalised learning plan from evaluation history."""
        ...

    async def generate_quiz(
        self, scenario: Scenario, question_count: int = 5,
    ) -> MicroQuiz:
        """Generate a micro-quiz based on scenario content."""
        ...

    async def sync_to_lms(self, learning_plan: LearningPlan) -> dict:
        """Stub: simulate LMS sync (iSpring Learn REST API)."""
        ...
