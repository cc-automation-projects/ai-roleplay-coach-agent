"""Integration tests for Gamification — GamificationEngine + repositories.

Tests component interactions without HTTP:
- Evaluation → XP: after evaluation, XP is awarded
- XP → Leaderboard: XP appears in leaderboard
- XP → Badge: reaching level threshold awards badge
- Streak: consecutive passing evaluations increase streak
- User stats: get_user_stats returns correct data
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from agents.gamification.engine import GamificationEngine
from core.entities import (
    Evaluation,
    User,
    UserCreate,
    UserRole,
    XPReason,
)
from core.entities.badge import Badge
from infrastructure.memory.repositories import (
    InMemoryBadgeRepository,
    InMemoryUserRepository,
    InMemoryXPTransactionRepository,
)

# ── Fixtures ─────────────────────────────────────────────────────────────


@pytest.fixture
def user_repo() -> InMemoryUserRepository:
    return InMemoryUserRepository()


@pytest.fixture
def xp_repo() -> InMemoryXPTransactionRepository:
    return InMemoryXPTransactionRepository()


@pytest.fixture
def badge_repo() -> InMemoryBadgeRepository:
    return InMemoryBadgeRepository()


@pytest.fixture
def engine(user_repo, xp_repo, badge_repo) -> GamificationEngine:
    return GamificationEngine(
        user_repo=user_repo,
        xp_repo=xp_repo,
        badge_repo=badge_repo,
    )


@pytest.fixture
async def seed_user(user_repo: InMemoryUserRepository) -> User:
    dto = UserCreate(
        username="gamification_user",
        hashed_password="",
        email="gamification@test.com",
        name="Gamification User",
        role=UserRole.OPERATOR,
    )
    return await user_repo.create(dto)


@pytest.fixture
async def seed_badges(badge_repo: InMemoryBadgeRepository) -> dict[str, Badge]:
    """Create level-based badges for testing."""
    badges: dict[str, Badge] = {}
    for name, criteria in [
        ("Bronze Operator", "min_level:5"),
        ("Silver Operator", "min_level:10"),
        ("Gold Operator", "min_level:15"),
    ]:
        badge = await badge_repo.create(
            Badge(name=name, description=f"Awarded at level {name.split()[0]}", criteria=criteria)
        )
        badges[name] = badge
    return badges


def _make_evaluation(user_id, overall_score: float = 85.0) -> Evaluation:
    """Create an Evaluation with given score."""
    return Evaluation(
        id=uuid4(),
        user_id=user_id,
        session_id=uuid4(),
        overall_score=overall_score,
        script_adherence=80.0,
        tone_score=75.0,
        empathy_score=70.0,
        objection_handling=80.0,
        completeness_score=85.0,
        praise_text="Good job",
        growth_text="Needs improvement",
        closing_text="Keep going",
        gaming_detected=False,
        created_at=datetime.now(UTC),
    )


# ── Tests ────────────────────────────────────────────────────────────────


class TestGamificationIntegration:
    """GamificationEngine + repositories integration."""

    async def test_session_completed_awards_xp(
        self, engine: GamificationEngine, seed_user: User,
    ) -> None:
        """Completing a session evaluation awards base XP."""
        evaluation = _make_evaluation(seed_user.id)
        result = await engine.award_session_completed(evaluation)

        assert result.xp_awarded > 0
        assert result.new_total_xp > 0
        assert result.new_level >= 1

        # Check XP was persisted
        txns = await engine._xp_repo.list_by_user(seed_user.id, skip=0, limit=10)
        assert len(txns) == 1
        assert txns[0].reason == XPReason.SESSION_COMPLETED

    async def test_high_score_bonus_xp(
        self, engine: GamificationEngine, seed_user: User,
    ) -> None:
        """Score >= 90 awards bonus XP."""
        evaluation = _make_evaluation(seed_user.id, overall_score=95.0)
        result = await engine.award_session_completed(evaluation)

        # Base (100) + High score bonus (50) = 150
        assert result.xp_awarded == 150

    async def test_streak_bonus_xp(
        self, engine: GamificationEngine, seed_user: User,
    ) -> None:
        """Streak count >= 3 awards streak bonus XP."""
        evaluation = _make_evaluation(seed_user.id)
        result = await engine.award_session_completed(evaluation, streak_count=3)

        assert result.streaks_bonus is True
        # Base (100) + Streak bonus (200) = 300
        assert result.xp_awarded == 300

    async def test_xp_appears_in_leaderboard(
        self, engine: GamificationEngine, seed_user: User,
    ) -> None:
        """After awarding XP, user appears in leaderboard."""
        evaluation = _make_evaluation(seed_user.id)
        await engine.award_session_completed(evaluation)

        leaderboard = await engine.get_leaderboard(limit=10, skip=0)
        assert len(leaderboard) >= 1
        entry = next((e for e in leaderboard if e["user_id"] == str(seed_user.id)), None)
        assert entry is not None
        assert entry["xp_total"] > 0

    async def test_level_up_awards_badge(
        self, engine: GamificationEngine, seed_user: User, seed_badges,
    ) -> None:
        """Reaching level 5 awards 'Bronze Operator' badge."""
        # Give user enough XP to reach level 5 (5000 XP = 50 evaluations)
        for _ in range(50):
            evaluation = _make_evaluation(seed_user.id)
            await engine.award_session_completed(evaluation)

        user = await engine._user_repo.get_by_id(seed_user.id)
        assert user is not None
        assert user.level >= 5

        # Check badges were awarded
        user_badges = await engine._badge_repo.get_user_badges(seed_user.id)
        badge_names = [b.name for b in user_badges]
        assert "Bronze Operator" in badge_names

    async def test_streak_tracking(
        self, engine: GamificationEngine, seed_user: User,
    ) -> None:
        """Consecutive passing evaluations increase streak."""
        for _ in range(5):
            evaluation = _make_evaluation(seed_user.id)
            await engine.award_session_completed(evaluation)

        streak = await engine.get_streak(seed_user.id)
        assert streak >= 5

    async def test_get_user_stats_returns_complete_data(
        self, engine: GamificationEngine, seed_user: User,
    ) -> None:
        """get_user_stats returns XP, level, txns, badges, progress."""
        evaluation = _make_evaluation(seed_user.id)
        await engine.award_session_completed(evaluation)

        stats = await engine.get_user_stats(seed_user.id)
        assert stats["xp_total"] > 0
        assert stats["level"] >= 1
        assert len(stats["recent_txns"]) >= 1
        assert "progress_pct" in stats
