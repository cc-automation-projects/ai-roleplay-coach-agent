"""Tests for CuratorAgent — learning plans, quizzes, LMS sync stub."""

from uuid import uuid4

import pytest

from core.entities import Evaluation, MicroQuiz, Scenario
from core.exceptions import CuratorError


@pytest.fixture
async def curator():
    """Fixture: rule-based CuratorAgent instance."""
    from agents.curator.agent import CuratorAgentImpl
    return CuratorAgentImpl()


@pytest.fixture
def scenario() -> Scenario:
    return Scenario(
        name="Tech Support Call",
        description="Customer with internet outage",
        script_ref="TS-001",
        script_text=(
            "Greet the customer warmly. Identify their account details. "
            "Diagnose the issue step by step. Offer a solution. "
            "Confirm the fix worked. Close the call professionally. "
            "Follow up within 24 hours."
        ),
    )


@pytest.fixture
def sample_evaluations() -> list[Evaluation]:
    uid = uuid4()
    sid = uuid4()
    return [
        Evaluation(
            session_id=sid,
            user_id=uid,
            overall_score=55.0,
            script_adherence=60.0,
            tone_score=80.0,
            empathy_score=30.0,
            objection_handling=45.0,
            completeness_score=70.0,
        ),
        Evaluation(
            session_id=uuid4(),
            user_id=uid,
            overall_score=62.0,
            script_adherence=65.0,
            tone_score=85.0,
            empathy_score=35.0,
            objection_handling=50.0,
            completeness_score=75.0,
        ),
    ]


@pytest.fixture
def high_score_evaluations() -> list[Evaluation]:
    uid = uuid4()
    sid = uuid4()
    return [
        Evaluation(
            session_id=sid,
            user_id=uid,
            overall_score=92.0,
            script_adherence=95.0,
            tone_score=90.0,
            empathy_score=88.0,
            objection_handling=91.0,
            completeness_score=94.0,
        ),
    ]


# ── Learning Plan ─────────────────────────────────────────────────────


class TestCuratorLearningPlan:
    """Tests for learning plan generation."""

    async def test_generates_plan_with_focus_areas(
        self, curator, scenario, sample_evaluations,
    ) -> None:
        """Plan identifies weakest dimensions from evaluations."""
        plan = await curator.generate_learning_plan(
            user_id=uuid4(),
            evaluations=sample_evaluations,
            scenario=scenario,
        )

        assert plan.user_id is not None
        # Weakest: empathy (avg ~32.5) and objection_handling (avg ~47.5)
        assert "Empathy" in plan.focus_areas
        assert plan.steps, "Should have actionable steps"
        assert len(plan.steps) >= 2

    async def test_plan_steps_are_ordered(
        self, curator, scenario, sample_evaluations,
    ) -> None:
        """Plan steps have sequential order numbers."""
        plan = await curator.generate_learning_plan(
            user_id=uuid4(),
            evaluations=sample_evaluations,
            scenario=scenario,
        )

        for i, step in enumerate(plan.steps, start=1):
            assert step.order == i, f"Step {i} has wrong order"

    async def test_plan_for_high_performer(
        self, curator, scenario, high_score_evaluations,
    ) -> None:
        """High performer gets fewer focus areas and maintenance steps."""
        plan = await curator.generate_learning_plan(
            user_id=uuid4(),
            evaluations=high_score_evaluations,
            scenario=scenario,
        )

        assert len(plan.focus_areas) <= 2
        # All scores are 88+ so focus should be maintenance, not fixing

    async def test_plan_with_empty_evaluations(
        self, curator, scenario,
    ) -> None:
        """Empty evaluation list generates a plan covering all dimensions."""
        plan = await curator.generate_learning_plan(
            user_id=uuid4(),
            evaluations=[],
            scenario=scenario,
        )
        assert len(plan.focus_areas) > 0
        assert len(plan.steps) > 0


# ── Quiz generation ───────────────────────────────────────────────────


class TestCuratorQuiz:
    """Tests for micro-quiz generation."""

    async def test_generates_quiz_with_questions(
        self, curator, scenario,
    ) -> None:
        """Quiz has the requested number of questions."""
        quiz = await curator.generate_quiz(scenario, question_count=3)

        assert isinstance(quiz, MicroQuiz)
        assert len(quiz.questions) == 3
        assert scenario.name in quiz.title or scenario.script_ref in quiz.title

    async def test_quiz_questions_have_valid_format(
        self, curator, scenario,
    ) -> None:
        """Each question has options and a valid correct_index."""
        quiz = await curator.generate_quiz(scenario, question_count=2)

        for q in quiz.questions:
            assert len(q.question) > 5
            assert len(q.options) >= 2
            assert 0 <= q.correct_index < len(q.options)
            assert q.explanation, "Should have explanation"

    async def test_quiz_zero_questions_returns_empty(
        self, curator, scenario,
    ) -> None:
        """Zero count returns quiz with no questions."""
        quiz = await curator.generate_quiz(scenario, question_count=0)
        assert len(quiz.questions) == 0

    async def test_quiz_question_count_capped(
        self, curator, scenario,
    ) -> None:
        """Requesting more than available questions is capped."""
        quiz = await curator.generate_quiz(scenario, question_count=50)
        # Should produce some reasonable number, not 50
        assert 1 <= len(quiz.questions) <= 20


# ── LMS sync stub ────────────────────────────────────────────────────


class TestCuratorLMS:
    """Tests for LMS synchronisation stub."""

    async def test_sync_returns_confirmation(
        self, curator, scenario, sample_evaluations,
    ) -> None:
        """LMS sync returns success dict with expected keys."""
        plan = await curator.generate_learning_plan(
            user_id=uuid4(),
            evaluations=sample_evaluations,
            scenario=scenario,
        )
        result = await curator.sync_to_lms(plan)

        assert result["status"] == "synced"
        assert "lms_course_id" in result
        assert "lms_url" in result
        assert result["user_id"] == str(plan.user_id)

    async def test_sync_raises_on_empty_plan(
        self, curator,
    ) -> None:
        """Syncing a plan without steps raises CuratorError."""
        from core.entities import LearningPlan

        empty_plan = LearningPlan(user_id=uuid4(), steps=[])
        with pytest.raises(CuratorError):
            await curator.sync_to_lms(empty_plan)
