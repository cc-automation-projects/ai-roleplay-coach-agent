"""Integration tests for Analyst — AnalystService + repositories.

Tests component interactions without HTTP:
- Session stats after N completed sessions
- Score distribution bins
- Progress over time
- Global stats aggregation
- User isolation (stats don't leak between users)
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from agents.analyst.service import AnalystService
from core.entities import (
    EvaluationCreate,
    SessionCreate,
    SessionStatus,
    User,
    UserCreate,
    UserRole,
)
from infrastructure.memory.repositories import (
    InMemoryEvaluationRepository,
    InMemorySessionRepository,
    InMemoryUserRepository,
)

# ── Fixtures ─────────────────────────────────────────────────────────────


@pytest.fixture
def eval_repo() -> InMemoryEvaluationRepository:
    return InMemoryEvaluationRepository()


@pytest.fixture
def session_repo() -> InMemorySessionRepository:
    return InMemorySessionRepository()


@pytest.fixture
def user_repo() -> InMemoryUserRepository:
    return InMemoryUserRepository()


@pytest.fixture
def analyst(
    eval_repo: InMemoryEvaluationRepository,
    session_repo: InMemorySessionRepository,
    user_repo: InMemoryUserRepository,
) -> AnalystService:
    return AnalystService(
        eval_repo=eval_repo,
        session_repo=session_repo,
        user_repo=user_repo,
    )


@pytest.fixture
async def seed_user(user_repo: InMemoryUserRepository) -> User:
    dto = UserCreate(
        username="analyst_user",
        hashed_password="",
        email="analyst@test.com",
        name="Analyst User",
        role=UserRole.OPERATOR,
    )
    return await user_repo.create(dto)


async def _seed_session_and_eval(
    session_repo: InMemorySessionRepository,
    eval_repo: InMemoryEvaluationRepository,
    user_id,
    *,
    status: SessionStatus = SessionStatus.COMPLETED,
    score: float = 75.0,
) -> None:
    """Helper: create a session + evaluation in one call."""
    session = await session_repo.create(
        SessionCreate(user_id=user_id, scenario_id=uuid4(), status=status)
    )
    await eval_repo.create(
        EvaluationCreate(
            user_id=user_id,
            session_id=session.id,
            overall_score=score,
            script_adherence=70.0,
            tone_score=65.0,
            empathy_score=60.0,
            objection_handling=75.0,
            completeness_score=80.0,
            praise_text="Good",
            growth_text="Needs work",
            closing_text="Keep going",
            gaming_detected=False,
        )
    )


# ── Tests ────────────────────────────────────────────────────────────────


class TestAnalystIntegration:
    """AnalystService + repositories integration."""

    async def test_session_stats_after_multiple_sessions(
        self, analyst: AnalystService, seed_user: User,
    ) -> None:
        """After 3 completed sessions, stats reflect correct counts and averages."""
        uid = seed_user.id
        for i in range(3):
            await _seed_session_and_eval(
                analyst.session_repo, analyst.eval_repo, uid,
                score=70.0 + i * 10.0,  # 70, 80, 90
            )

        stats = await analyst.get_session_stats(uid)

        assert stats.total_sessions == 3
        assert stats.completed_sessions == 3
        assert stats.abandoned_sessions == 0
        assert stats.avg_overall_score == 80.0  # (70+80+90)/3

    async def test_abandoned_sessions_tracked(
        self, analyst: AnalystService, seed_user: User,
    ) -> None:
        """Interrupted and failed sessions count as abandoned."""
        uid = seed_user.id
        await _seed_session_and_eval(analyst.session_repo, analyst.eval_repo, uid)

        # Interrupted session
        session = await analyst.session_repo.create(
            SessionCreate(user_id=uid, scenario_id=uuid4(), status=SessionStatus.INTERRUPTED)
        )
        await analyst.eval_repo.create(
            EvaluationCreate(
                user_id=uid,
                session_id=session.id,
                overall_score=50.0,
                script_adherence=50.0,
                tone_score=50.0,
                empathy_score=50.0,
                objection_handling=50.0,
                completeness_score=50.0,
                praise_text="",
                growth_text="",
                closing_text="",
                gaming_detected=False,
            )
        )

        stats = await analyst.get_session_stats(uid)
        assert stats.total_sessions == 2
        assert stats.completed_sessions == 1
        assert stats.abandoned_sessions >= 1

    async def test_score_distribution_returns_bins(
        self, analyst: AnalystService, seed_user: User,
    ) -> None:
        """Score distribution returns correct histogram bins."""
        uid = seed_user.id
        for score in [10, 30, 50, 70, 85, 95]:
            await _seed_session_and_eval(analyst.session_repo, analyst.eval_repo, uid, score=float(score))

        dist = await analyst.get_score_distribution(uid)

        assert len(dist) == 6  # 6 dimensions
        overall = next(d for d in dist if d.dimension == "overall_score")
        assert overall.bins["0-20"] == 1  # score 10
        assert overall.bins["21-40"] == 1  # score 30
        assert overall.bins["41-60"] == 1  # score 50
        assert overall.bins["61-80"] == 1  # score 70
        assert overall.bins["81-90"] == 1  # score 85
        assert overall.bins["91-100"] == 1  # score 95

    async def test_progress_over_time_returns_sorted(
        self, analyst: AnalystService, seed_user: User,
    ) -> None:
        """Progress over time returns evaluations sorted by date."""
        uid = seed_user.id
        for score in [60, 70, 80]:
            await _seed_session_and_eval(analyst.session_repo, analyst.eval_repo, uid, score=float(score))

        progress = await analyst.get_progress_over_time(uid, limit=10)
        assert len(progress) == 3
        # Should be sorted by date ascending
        scores = [p.overall_score for p in progress]
        assert scores == sorted(scores)

    async def test_user_isolation(
        self, analyst: AnalystService, seed_user: User, user_repo: InMemoryUserRepository,
    ) -> None:
        """Stats for user A don't include user B's data."""
        uid_a = seed_user.id

        # Create user B
        user_b = await user_repo.create(
            UserCreate(
                username="user_b",
                hashed_password="",
                email="user_b@test.com",
                name="User B",
                role=UserRole.OPERATOR,
            )
        )

        # Seed data for user B
        await _seed_session_and_eval(analyst.session_repo, analyst.eval_repo, user_b.id, score=95.0)

        # User A has no sessions
        stats_a = await analyst.get_session_stats(uid_a)
        assert stats_a.total_sessions == 0

        # Global stats should see user B's session
        global_stats = await analyst.get_global_stats()
        assert global_stats.total_sessions >= 1

    async def test_global_stats_aggregation(
        self, analyst: AnalystService, seed_user: User, user_repo: InMemoryUserRepository,
    ) -> None:
        """Global stats aggregate across all users."""
        uid1 = seed_user.id

        # Create more users with sessions
        for name in ["user_c", "user_d"]:
            u = await user_repo.create(
                UserCreate(
                    username=name, hashed_password="",
                    email=f"{name}@test.com", name=name,
                    role=UserRole.OPERATOR,
                )
            )
            await _seed_session_and_eval(analyst.session_repo, analyst.eval_repo, u.id, score=80.0)

        # Also seed user1
        await _seed_session_and_eval(analyst.session_repo, analyst.eval_repo, uid1, score=90.0)

        global_stats = await analyst.get_global_stats()
        assert global_stats.total_users >= 3
        assert global_stats.total_sessions >= 3
        assert global_stats.avg_score > 0
