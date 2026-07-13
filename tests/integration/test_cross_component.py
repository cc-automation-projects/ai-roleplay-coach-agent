"""Cross-component integration — Auth → Session → Coach → Gamification → Analyst pipeline.

Tests that multiple Phase 3b components work together in-process
(without HTTP) to simulate a full user workflow:
1. Register user (AuthService)
2. Start session (SessionService)
3. Simulate turns (SessionService)
4. Evaluate (CoachAgent)
5. Award XP (GamificationEngine)
6. Check stats (AnalystService)
"""

from __future__ import annotations

from uuid import UUID

import pytest

from agents.analyst.service import AnalystService
from agents.coach.agent import CoachAgent
from agents.gamification.engine import GamificationEngine
from core.entities import (
    DifficultyLevel,
    EvaluationCreate,
    Psychotype,
    Scenario,
    SessionCreate,
    SessionStatus,
)
from core.services.auth_service import AuthService
from infrastructure.memory.repositories import (
    InMemoryBadgeRepository,
    InMemoryEvaluationRepository,
    InMemoryScenarioRepository,
    InMemorySessionRepository,
    InMemoryUserRepository,
    InMemoryXPTransactionRepository,
)

# ── Fixtures ─────────────────────────────────────────────────────────────


@pytest.fixture
def user_repo() -> InMemoryUserRepository:
    return InMemoryUserRepository()


@pytest.fixture
def session_repo() -> InMemorySessionRepository:
    return InMemorySessionRepository()


@pytest.fixture
def eval_repo() -> InMemoryEvaluationRepository:
    return InMemoryEvaluationRepository()


@pytest.fixture
def xp_repo() -> InMemoryXPTransactionRepository:
    return InMemoryXPTransactionRepository()


@pytest.fixture
def badge_repo() -> InMemoryBadgeRepository:
    return InMemoryBadgeRepository()


@pytest.fixture
def scenario_repo() -> InMemoryScenarioRepository:
    return InMemoryScenarioRepository()


@pytest.fixture
def auth_service(user_repo) -> AuthService:
    return AuthService(user_repo=user_repo)


@pytest.fixture
def gamification_engine(user_repo, xp_repo, badge_repo) -> GamificationEngine:
    return GamificationEngine(user_repo=user_repo, xp_repo=xp_repo, badge_repo=badge_repo)


@pytest.fixture
def analyst_service(eval_repo, session_repo, user_repo) -> AnalystService:
    return AnalystService(eval_repo=eval_repo, session_repo=session_repo, user_repo=user_repo)


@pytest.fixture
def scenario() -> Scenario:
    return Scenario(
        name="Billing",
        description="Billing issue scenario",
        script_ref="s-001",
        script_text="Greet. Identify. Empathize. Solve.",
        psychotype=Psychotype.NEUTRAL,
        difficulty=DifficultyLevel.BEGINNER,
    )


TEST_PWD = "TstPwd123"
TEST_PWD2 = "Pwd123Sec"


class TestCrossComponentPipeline:
    """Auth → Session → Coach → Gamification → Analyst pipeline."""

    async def test_full_pipeline(
        self,
        auth_service: AuthService,
        session_repo: InMemorySessionRepository,
        eval_repo: InMemoryEvaluationRepository,
        scenario_repo: InMemoryScenarioRepository,
        gamification_engine: GamificationEngine,
        analyst_service: AnalystService,
        scenario: Scenario,
    ) -> None:
        """End-to-end pipeline: register → session → evaluate → XP → stats."""
        # 1. Register user
        reg = await auth_service.register(
            username="pipeline_user",
            password=TEST_PWD,
        )
        user_id = UUID(reg["user_id"])
        assert reg["role"] == "operator"

        # 2. Seed scenario, create session directly
        scenario_repo.seed(scenario)
        session = await session_repo.create(
            SessionCreate(user_id=user_id, scenario_id=scenario.id)
        )
        assert session is not None

        # 3. Simulate turns
        session.append_transcript_entry("operator", "Hello, how can I help you?")
        session.append_transcript_entry("client", "I have a billing issue")
        session.append_transcript_entry("operator", "Let me look into that for you")
        session.append_transcript_entry("client", "Thank you")
        session.append_transcript_entry("operator", "Is there anything else?")
        session.append_transcript_entry("client", "No, that is all")

        session.status = SessionStatus.COMPLETED
        await session_repo.update(session)

        # 4. Evaluate with rule-based Coach
        coach = CoachAgent()
        evaluation = await coach.evaluate_session(session, scenario)
        assert evaluation is not None
        assert evaluation.overall_score > 0

        await analyst_service.eval_repo.create(
            EvaluationCreate(
                user_id=user_id,
                session_id=session.id,
                overall_score=evaluation.overall_score,
                script_adherence=evaluation.script_adherence,
                tone_score=evaluation.tone_score,
                empathy_score=evaluation.empathy_score,
                objection_handling=evaluation.objection_handling,
                completeness_score=evaluation.completeness_score,
                praise_text=evaluation.praise_text,
                growth_text=evaluation.growth_text,
                closing_text=evaluation.closing_text,
                gaming_detected=evaluation.gaming_detected,
            )
        )

        # 5. Award XP
        award = await gamification_engine.award_session_completed(evaluation)
        assert award.xp_awarded > 0
        assert award.new_total_xp > 0

        # 6. Check analyst stats
        stats = await analyst_service.get_session_stats(user_id)
        assert stats.total_sessions >= 1
        assert stats.completed_sessions >= 1
        assert stats.avg_overall_score > 0

        # 7. Verify gamification stats
        gs = await gamification_engine.get_user_stats(user_id)
        assert gs["xp_total"] > 0
        assert gs["level"] >= 1

    async def test_multiple_sessions_pipeline(
        self,
        auth_service: AuthService,
        session_repo: InMemorySessionRepository,
        scenario_repo: InMemoryScenarioRepository,
        eval_repo: InMemoryEvaluationRepository,
        gamification_engine: GamificationEngine,
        analyst_service: AnalystService,
        scenario: Scenario,
    ) -> None:
        """Multiple sessions accumulate XP and update stats correctly."""
        reg = await auth_service.register(
            username="multi_session_user",
            password=TEST_PWD2,
        )
        user_id = UUID(reg["user_id"])
        scenario_repo.seed(scenario)

        for _ in range(3):
            session = await session_repo.create(
                SessionCreate(user_id=user_id, scenario_id=scenario.id),
            )
            session.append_transcript_entry("operator", "Hello")
            session.append_transcript_entry("client", "Hi")
            session.status = SessionStatus.COMPLETED
            await session_repo.update(session)

            coach = CoachAgent()
            evaluation = await coach.evaluate_session(session, scenario)

            await analyst_service.eval_repo.create(
                EvaluationCreate(
                    user_id=user_id,
                    session_id=session.id,
                    overall_score=evaluation.overall_score,
                    script_adherence=evaluation.script_adherence,
                    tone_score=evaluation.tone_score,
                    empathy_score=evaluation.empathy_score,
                    objection_handling=evaluation.objection_handling,
                    completeness_score=evaluation.completeness_score,
                    praise_text=evaluation.praise_text,
                    growth_text=evaluation.growth_text,
                    closing_text=evaluation.closing_text,
                    gaming_detected=evaluation.gaming_detected,
                )
            )

            await gamification_engine.award_session_completed(evaluation)

        stats = await analyst_service.get_session_stats(user_id)
        assert stats.total_sessions == 3
        assert stats.completed_sessions == 3

        gs = await gamification_engine.get_user_stats(user_id)
        assert gs["xp_total"] >= 300  # 3 * 100 base XP
