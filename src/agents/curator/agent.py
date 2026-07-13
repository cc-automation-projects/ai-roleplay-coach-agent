"""CuratorAgent — rule-based learning plans, micro-quizzes, and LMS sync stub.

Generates personalised study plans from evaluation weaknesses,
creates scenario-based knowledge checks, and simulates LMS
synchronisation (iSpring Learn REST API stubs).
"""

from __future__ import annotations

import logging
import random
from typing import TYPE_CHECKING

from core.entities import (
    Evaluation,
    LearningPlan,
    MicroQuiz,
    PlanStep,
    QuizQuestion,
    Scenario,
)
from core.exceptions import CuratorError

if TYPE_CHECKING:
    from uuid import UUID

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────

_WEAK_THRESHOLD = 60.0
_STRONG_THRESHOLD = 85.0

_DIMENSION_NAMES = (
    "script_adherence",
    "tone_score",
    "empathy_score",
    "objection_handling",
    "completeness_score",
)
_DIMENSION_LABELS: dict[str, str] = {
    "script_adherence": "Script Adherence",
    "tone_score": "Tone & Politeness",
    "empathy_score": "Empathy",
    "objection_handling": "Objection Handling",
    "completeness_score": "Completeness",
}

_MAX_QUIZ_QUESTIONS = 10
_QUIZ_CAP_HARD = 20

# Minimum keyword length for quiz question generation
_MIN_KEYWORD_LEN = 4

_LMS_SYNC_URL = "https://lms.example.com/api/v1/courses"


# ── Implementation ─────────────────────────────────────────────────────


class CuratorAgentImpl:
    """Rule-based curator: learning plans, quizzes, LMS sync."""

    # ── Learning plans ──────────────────────────────────────────────────

    async def generate_learning_plan(
        self,
        user_id: UUID,
        evaluations: list[Evaluation],
        scenario: Scenario,
    ) -> LearningPlan:
        """Build a personalised learning plan from evaluation history.

        When no evaluations exist yet, generates a plan covering all
        core dimensions based on the scenario alone.
        """
        if evaluations:
            focus_areas = self._identify_focus_areas(evaluations)
        else:
            focus_areas = list(_DIMENSION_LABELS.values())

        steps = self._build_steps(focus_areas, scenario)

        return LearningPlan(
            user_id=user_id,
            scenario_id=scenario.id,
            focus_areas=focus_areas,
            steps=steps,
            difficulty_label=scenario.difficulty.value,
        )

    @staticmethod
    def _identify_focus_areas(evaluations: list[Evaluation]) -> list[str]:
        """Rank dimensions by average score, return weakest first."""
        totals: dict[str, float] = {}
        counts: dict[str, int] = {}

        for eval_ in evaluations:
            for dim in _DIMENSION_NAMES:
                totals[dim] = totals.get(dim, 0.0) + getattr(eval_, dim, 0.0)
                counts[dim] = counts.get(dim, 0) + 1

        averages = {
            dim: totals[dim] / counts[dim] for dim in _DIMENSION_NAMES
        }
        # Sort weakest first
        sorted_dims = sorted(averages.items(), key=lambda x: x[1])
        # Return labels of dimensions below weak threshold (or bottom 2)
        weak = [dim for dim, avg in sorted_dims if avg < _WEAK_THRESHOLD]
        if weak:
            return [_DIMENSION_LABELS[d] for d in weak]
        # All above threshold → return lowest (maintenance mode)
        lowest = sorted_dims[0][0]
        return [_DIMENSION_LABELS[lowest]]

    @staticmethod
    def _build_steps(
        focus_areas: list[str], scenario: Scenario,
    ) -> list[PlanStep]:
        """Create actionable steps targeting focus areas."""
        steps: list[PlanStep] = []

        for area in focus_areas:
            steps.append(
                PlanStep(
                    order=len(steps) + 1,
                    title=f"Review: {area}",
                    description=(
                        f"Study the script '{scenario.script_ref}' "
                        f"with attention to **{area}**. "
                        f"Identify best-practice examples in the material."
                    ),
                    estimated_minutes=15,
                ),
            )
            steps.append(
                PlanStep(
                    order=len(steps) + 1,
                    title=f"Practice: {area}",
                    description=(
                        f"Run a simulation focused on improving "
                        f"**{area}**. Aim for a score above 80%."
                    ),
                    estimated_minutes=20,
                ),
            )

        # Always add a final knowledge check step
        steps.append(
            PlanStep(
                order=len(steps) + 1,
                title="Knowledge Check",
                description=(
                    f"Take the quiz for '{scenario.name}' "
                    f"to reinforce key concepts."
                ),
                estimated_minutes=10,
            ),
        )

        return steps

    # ── Quiz generation ─────────────────────────────────────────────────

    async def generate_quiz(
        self, scenario: Scenario, question_count: int = 5,
    ) -> MicroQuiz:
        """Generate a micro-quiz based on scenario content."""
        questions = self._build_questions(scenario)
        actual_count = max(0, min(question_count, _QUIZ_CAP_HARD))
        selected = random.sample(questions, min(actual_count, len(questions)))

        return MicroQuiz(
            scenario_id=scenario.id,
            title=f"{scenario.script_ref}: {scenario.name} — Quick Check",
            questions=selected,
        )

    @staticmethod
    def _build_questions(scenario: Scenario) -> list[QuizQuestion]:
        """Rule-based question bank from script text."""
        text_lower = scenario.script_text.lower()
        questions: list[QuizQuestion] = []

        # Q1: Script identification
        questions.append(
            QuizQuestion(
                question=(
                    f"What is the primary goal of the "
                    f"'{scenario.name}' scenario?"
                ),
                options=[
                    scenario.description,
                    "Complete a sales transaction",
                    "Handle a technical complaint",
                    f"Master {scenario.script_ref} process",
                ],
                correct_index=0,
                explanation=(
                    f"The scenario focuses on: {scenario.description}"
                ),
            ),
        )

        # Q2: Keyword-based question
        keywords = [w for w in text_lower.split() if len(w) > _MIN_KEYWORD_LEN][:5]
        if keywords:
            kw = keywords[0]
            questions.append(
                QuizQuestion(
                    question=(
                        f"Which of the following is mentioned in the "
                        f"'{scenario.script_ref}' script?"
                    ),
                    options=[
                        kw.capitalize(),
                        "Quantum computing",
                        "Blockchain",
                        "Machine learning",
                    ],
                    correct_index=0,
                    explanation=(
                        f"The script mentions '{kw}' as part of "
                        f"the recommended approach."
                    ),
                ),
            )

        if "greet" in text_lower or "hello" in text_lower:
            questions.append(
                QuizQuestion(
                    question=(
                        "What is the first recommended step "
                        "in this scenario?"
                    ),
                    options=[
                        "Greet the customer warmly",
                        "Ask for payment",
                        "Transfer to supervisor",
                        "End the call",
                    ],
                    correct_index=0,
                    explanation=(
                        "Opening with a warm greeting sets a "
                        "positive tone for the interaction."
                    ),
                ),
            )

        if "follow up" in text_lower or "follow-up" in text_lower:
            questions.append(
                QuizQuestion(
                    question=(
                        "What should you do after resolving "
                        "the customer's issue?"
                    ),
                    options=[
                        "Follow up within 24 hours",
                        "Close the account",
                        "Ignore further contact",
                        "Mark as spam",
                    ],
                    correct_index=0,
                    explanation=(
                        "Following up ensures the issue is "
                        "fully resolved and builds trust."
                    ),
                ),
            )

        if "diagnos" in text_lower or "identify" in text_lower:
            questions.append(
                QuizQuestion(
                    question=(
                        "What should you do before offering a solution?"
                    ),
                    options=[
                        "Diagnose the issue step by step",
                        "Immediately offer a refund",
                        "Ask for a manager",
                        "End the conversation",
                    ],
                    correct_index=0,
                    explanation=(
                        "Proper diagnosis ensures the solution "
                        "addresses the root cause."
                    ),
                ),
            )

        if "solution" in text_lower or "offer" in text_lower:
            questions.append(
                QuizQuestion(
                    question=(
                        "What type of response is most appropriate "
                        "after identifying the issue?"
                    ),
                    options=[
                        "Offer a clear solution with next steps",
                        "Tell the customer to call back later",
                        "Ignore the issue",
                        "Blame another department",
                    ],
                    correct_index=0,
                    explanation=(
                        "Presenting a clear solution demonstrates "
                        "competence and builds confidence."
                    ),
                ),
            )

        return questions

    # ── LMS sync stub ───────────────────────────────────────────────────

    async def sync_to_lms(self, learning_plan: LearningPlan) -> dict:
        """Stub: simulate iSpring Learn REST API synchronisation."""
        if not learning_plan.steps:
            msg = "Cannot sync an empty learning plan (no steps)"
            raise CuratorError(msg)

        course_id = f"COACH-{random.randint(10000, 99999)}"  # noqa: S311
        return {
            "status": "synced",
            "lms_course_id": course_id,
            "lms_url": f"{_LMS_SYNC_URL}/{course_id}",
            "user_id": str(learning_plan.user_id),
            "focus_areas": learning_plan.focus_areas,
            "step_count": len(learning_plan.steps),
        }
