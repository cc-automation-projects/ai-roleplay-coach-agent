"""Unit tests for AnalystService."""

from __future__ import annotations

from uuid import uuid4

import pytest

from agents.analyst.service import AnalystService
from core.entities import (
    Evaluation,
    EvaluationCreate,
    Session,
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


@pytest.fixture
def analyst_service() -> AnalystService:
    """Create a fresh AnalystService with empty in-memory repos."""
    return AnalystService(
        eval_repo=InMemoryEvaluationRepository(),
        session_repo=InMemorySessionRepository(),
        user_repo=InMemoryUserRepository(),
    )


@pytest.fixture
async def seed_user(analyst_service: AnalystService) -> User:
    """Return a seeded user."""
    dto = UserCreate(
        username="testuser",
        hashed_password="",
        email="test@example.com",
        name="Test User",
        role=UserRole.OPERATOR,
    )
    return await analyst_service.user_repo.create(dto)


@pytest.fixture
async def seed_sessions(
    analyst_service: AnalystService, seed_user: User
) -> list[Session]:
    """Seed 3 sessions (2 completed, 1 interrupted)."""
    repo: InMemorySessionRepository = analyst_service.session_repo
    uid = seed_user.id
    sid = uuid4()
    s1 = await repo.create(
        SessionCreate(
            user_id=uid,
            scenario_id=sid,
            status=SessionStatus.COMPLETED,
        )
    )
    s2 = await repo.create(
        SessionCreate(
            user_id=uid,
            scenario_id=sid,
            status=SessionStatus.COMPLETED,
        )
    )
    s3 = await repo.create(
        SessionCreate(
            user_id=uid,
            scenario_id=sid,
            status=SessionStatus.INTERRUPTED,
        )
    )
    return [s1, s2, s3]


@pytest.fixture
async def seed_evaluations(
    analyst_service: AnalystService, seed_user: User, seed_sessions: list[Session]
) -> list[Evaluation]:
    """Seed 3 evaluations matching the 3 sessions."""
    repo: InMemoryEvaluationRepository = analyst_service.eval_repo
    uid = seed_user.id
    evals = []
    scores = [
        (85, 80, 70, 90, 75, 88),
        (92, 95, 85, 90, 88, 91),
        (60, 55, 65, 50, 70, 60),
    ]
    for i, session in enumerate(seed_sessions):
        ov, sa, ts, es, oh, cs = scores[i]
        ev = await repo.create(
            EvaluationCreate(
                session_id=session.id,
                user_id=uid,
                overall_score=ov,
                script_adherence=sa,
                tone_score=ts,
                empathy_score=es,
                objection_handling=oh,
                completeness_score=cs,
            )
        )
        evals.append(ev)
    return evals


@pytest.mark.asyncio
async def test_get_session_stats_with_data(
    analyst_service: AnalystService,
    seed_user: User,
    seed_sessions: list[Session],
    seed_evaluations: list[Evaluation],
) -> None:
    """get_session_stats should return correct stats for a user with data."""
    stats = await analyst_service.get_session_stats(seed_user.id)
    assert stats.total_sessions == 3
    assert stats.completed_sessions == 2
    assert stats.abandoned_sessions == 1
    assert stats.avg_overall_score == pytest.approx(79.0, abs=0.1)
    assert stats.max_overall_score == 92.0
    assert stats.min_overall_score == 60.0
    # Avg per dimension
    assert stats.avg_script_adherence == pytest.approx(76.67, abs=0.1)
    assert stats.avg_empathy_score == pytest.approx(76.67, abs=0.1)


@pytest.mark.asyncio
async def test_get_session_stats_empty_user(
    analyst_service: AnalystService,
) -> None:
    """get_session_stats should return zeros for a user with no data."""
    uid = uuid4()
    stats = await analyst_service.get_session_stats(uid)
    assert stats.total_sessions == 0
    assert stats.completed_sessions == 0
    assert stats.abandoned_sessions == 0
    assert stats.avg_overall_score == 0.0
    assert stats.max_overall_score == 0.0
    assert stats.min_overall_score == 0.0


@pytest.mark.asyncio
async def test_get_session_stats_global(
    analyst_service: AnalystService,
    seed_user: User,
    seed_sessions: list[Session],
    seed_evaluations: list[Evaluation],
) -> None:
    """get_session_stats with None should aggregate across all users."""
    stats = await analyst_service.get_session_stats()
    assert stats.total_sessions >= 3
    assert stats.completed_sessions >= 2
    assert stats.avg_overall_score == pytest.approx(79.0, abs=0.1)


@pytest.mark.asyncio
async def test_get_score_distribution(
    analyst_service: AnalystService,
    seed_user: User,
    seed_sessions: list[Session],
    seed_evaluations: list[Evaluation],
) -> None:
    """Distribution should have 6 dimensions with correct bins."""
    dist = await analyst_service.get_score_distribution(seed_user.id)
    assert len(dist) == 6
    dimension_names = {d.dimension for d in dist}
    assert dimension_names == {
        "overall_score",
        "script_adherence",
        "tone_score",
        "empathy_score",
        "objection_handling",
        "completeness_score",
    }
    # Check overall_score bins (scores: 85, 92, 60)
    overall = next(d for d in dist if d.dimension == "overall_score")
    assert overall.bins["81-90"] == 1
    assert overall.bins["91-100"] == 1
    assert overall.bins["61-80"] == 0
    assert overall.bins["41-60"] == 1


@pytest.mark.asyncio
async def test_get_progress_over_time(
    analyst_service: AnalystService,
    seed_user: User,
    seed_sessions: list[Session],
    seed_evaluations: list[Evaluation],
) -> None:
    """Progress should return sorted time-series points."""
    points = await analyst_service.get_progress_over_time(seed_user.id)
    assert len(points) == 3
    # Should be sorted by date ascending
    for i in range(len(points) - 1):
        assert points[i].date <= points[i + 1].date
    # All scores should match
    assert {p.overall_score for p in points} == {85, 92, 60}


@pytest.mark.asyncio
async def test_get_progress_over_time_empty(
    analyst_service: AnalystService,
) -> None:
    """Progress for user with no evaluations should return empty list."""
    uid = uuid4()
    points = await analyst_service.get_progress_over_time(uid)
    assert points == []


@pytest.mark.asyncio
async def test_get_global_stats(
    analyst_service: AnalystService,
    seed_user: User,
    seed_sessions: list[Session],
    seed_evaluations: list[Evaluation],
) -> None:
    """Global stats should include total users, sessions, avg score."""
    stats = await analyst_service.get_global_stats()
    assert stats.total_users >= 1
    assert stats.total_sessions >= 3
    assert stats.avg_score == pytest.approx(79.0, abs=0.1)
    # top_scenario should be set (we used same scenario_id)
    assert stats.top_scenario is not None


@pytest.mark.asyncio
async def test_get_global_stats_empty(
    analyst_service: AnalystService,
) -> None:
    """Global stats with no data should return zeros."""
    stats = await analyst_service.get_global_stats()
    assert stats.total_users == 0
    assert stats.total_sessions == 0
    assert stats.avg_score == 0.0
    assert stats.top_scenario is None
