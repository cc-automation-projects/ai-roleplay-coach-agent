"""GamificationEngine — unified XP, levels, streaks, and badges.

Wraps the existing XP infrastructure (XPReason, XPTransaction,
Metric entities) into a single interface for use by agents and
API routes.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from core.entities import (
    Evaluation,
    Metric,
    MetricType,
    User,
    XPReason,
    XPTransaction,
)
from core.entities.badge import Badge, UserBadge

if TYPE_CHECKING:
    from uuid import UUID

    from core.interfaces.repositories import (
        BadgeRepository,
        UserRepository,
        XPTransactionRepository,
    )

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────

_XP_SESSION_PASS = 100
_XP_SESSION_HIGH_SCORE = 50  # bonus for score >= 90
_XP_STREAK_BONUS = 200
_XP_BADGE_EARNED = 50

_STREAK_THRESHOLD = 3  # consecutive passes to count as streak
_HIGH_SCORE_THRESHOLD = 90
_PERFECT_SCORE_THRESHOLD = 95
_XP_PER_LEVEL = 1000

# ── Data structures ────────────────────────────────────────────────────


@dataclass
class AwardResult:
    """Result of awarding XP, including side effects."""

    xp_awarded: int = 0
    level_up: bool = False
    new_level: int = 1
    new_total_xp: int = 0
    streaks_bonus: bool = False
    badges_earned: list[str] = field(default_factory=list)


# ── GamificationEngine ─────────────────────────────────────────────────


class GamificationEngine:
    """Central gamification engine for XP, levels, and badges.

    Works with the existing ``User``, ``XPTransaction``, and
    ``Badge`` entities.  Does **not** replace them — provides
    a convenient high-level API for awarding XP and checking
    achievements.
    """

    def __init__(
        self,
        user_repo: UserRepository,
        xp_repo: XPTransactionRepository,
        badge_repo: BadgeRepository,
        xp_per_level: int = _XP_PER_LEVEL,
    ) -> None:
        self._user_repo = user_repo
        self._xp_repo = xp_repo
        self._badge_repo = badge_repo
        self._xp_per_level = xp_per_level

    # ── Public API ──────────────────────────────────────────────────────

    async def award_session_completed(
        self,
        evaluation: Evaluation,
        *,
        streak_count: int = 0,
    ) -> AwardResult:
        """Award XP for completing a session evaluation.

        Args:
            evaluation: The completed evaluation.
            streak_count: Number of consecutive passed evaluations
                before this one (for streak bonus).

        Returns:
            AwardResult with XP changes, level-ups, and badges.
        """
        result = AwardResult()

        # Base XP
        xp = _XP_SESSION_PASS

        # High-score bonus
        if evaluation.overall_score >= _HIGH_SCORE_THRESHOLD:
            xp += _XP_SESSION_HIGH_SCORE

        # Streak bonus
        if streak_count >= _STREAK_THRESHOLD:
            xp += _XP_STREAK_BONUS
            result.streaks_bonus = True

        # Persist XP transaction
        txn = XPTransaction(
            user_id=evaluation.user_id,
            amount=xp,
            reason=XPReason.SESSION_COMPLETED,
            reference_id=evaluation.session_id,
        )
        await self._xp_repo.create(txn)

        # Update user
        user = await self._user_repo.get_by_id(evaluation.user_id)
        if user is None:
            logger.warning("User %s not found for XP award", evaluation.user_id)
            return result

        old_level = user.level
        user.add_xp(xp)
        await self._user_repo.update(user)

        result.xp_awarded = xp
        result.new_total_xp = user.xp_total
        result.new_level = user.level
        result.level_up = self._check_level_up(old_level, user.level)

        badge_names = await self._check_badges(user, evaluation)
        result.badges_earned = badge_names

        return result

    async def award_badge_earned(
        self,
        user_id: UUID,
        badge_name: str,
    ) -> AwardResult:
        """Award XP for earning a badge."""
        result = AwardResult()
        txn = XPTransaction(
            user_id=user_id,
            amount=_XP_BADGE_EARNED,
            reason=XPReason.BADGE_EARNED,
        )
        await self._xp_repo.create(txn)

        user = await self._user_repo.get_by_id(user_id)
        if user is None:
            return result

        old_level = user.level
        user.add_xp(_XP_BADGE_EARNED)
        await self._user_repo.update(user)

        result.xp_awarded = _XP_BADGE_EARNED
        result.new_total_xp = user.xp_total
        result.new_level = user.level
        result.level_up = self._check_level_up(old_level, user.level)
        result.badges_earned = [badge_name]

        return result

    async def get_user_stats(self, user_id: UUID) -> dict:
        """Return gamification stats for a user dashboard.

        Returns XP total, level, progress to next level,
        recent transactions, and earned badges.
        """
        user = await self._user_repo.get_by_id(user_id)
        if user is None:
            return {}

        txns = await self._xp_repo.list_by_user(user_id, skip=0, limit=20)
        badges = await self._badge_repo.get_user_badges(user_id)

        xp_in_level = user.xp_total % self._xp_per_level
        progress_pct = round(xp_in_level / self._xp_per_level * 100, 1)

        return {
            "xp_total": user.xp_total,
            "level": user.level,
            "xp_in_level": xp_in_level,
            "xp_for_next_level": self._xp_per_level,
            "progress_pct": progress_pct,
            "recent_txns": [
                {
                    "amount": t.amount,
                    "reason": t.reason.value,
                    "created_at": t.created_at.isoformat(),
                }
                for t in txns
            ],
            "badges": [b.name for b in badges],
        }

    async def record_metric(
        self,
        user_id: UUID,
        metric_type: MetricType,
        value: float,
    ) -> Metric:
        """Record a time-series metric (for analytics)."""
        metric = Metric(
            user_id=user_id,
            metric_type=metric_type,
            value=value,
        )
        # Persist via repository (caller to provide)
        logger.info(
            "Metric recorded user=%s type=%s value=%.2f",
            user_id, metric_type.value, value,
        )
        return metric

    async def get_leaderboard(
        self, limit: int = 10, skip: int = 0,
    ) -> list[dict]:
        """Return top users by XP with rank."""
        users = await self._user_repo.get_leaderboard(limit=limit, skip=skip)
        return [
            {
                "rank": idx + 1,
                "user_id": str(u.id),
                "name": u.name,
                "xp_total": u.xp_total,
                "level": u.level,
            }
            for idx, u in enumerate(users)
        ]

    async def get_leaderboard_count(self) -> int:
        """Return total number of users eligible for the leaderboard."""
        return await self._user_repo.count()

    async def get_streak(self, user_id: UUID) -> int:
        """Return current streak (consecutive passing evaluations).

        Reads recent XP transactions and counts consecutive
        SESSION_COMPLETED entries.  Partial — returns pass/fail
        streak from the last 10 transactions.
        """
        txns = await self._xp_repo.list_by_user(user_id, skip=0, limit=10)
        streak = 0
        for txn in reversed(txns):
            if txn.reason == XPReason.SESSION_COMPLETED and txn.amount > 0:
                streak += 1
            else:
                break
        return streak

    # ── Internal helpers ────────────────────────────────────────────────

    async def _check_badges(
        self,
        user: User,
        evaluation: Evaluation,
    ) -> list[str]:
        """Check and award milestone badges.

        Returns names of newly earned badges.
        """
        new_badges: list[str] = []

        # Level-based badges
        level_badges: dict[int, str] = {
            5: "Bronze Operator",
            10: "Silver Operator",
            15: "Gold Operator",
            20: "Platinum Operator",
        }

        # Get user's existing badges + all available badges
        user_badges = await self._badge_repo.get_user_badges(user.id)
        user_badge_ids = {b.id for b in user_badges}

        all_badges = await self._badge_repo.list_all()
        all_badges_by_name: dict[str, Badge] = {b.name: b for b in all_badges}

        for level, badge_name in level_badges.items():
            if user.level < level:
                continue
            badge = all_badges_by_name.get(badge_name)
            if badge is None:
                logger.warning(
                    "Level badge '%s' not found in badge catalog",
                    badge_name,
                )
                continue
            if badge.id in user_badge_ids:
                logger.debug(
                    "Badge '%s' already awarded to user %s",
                    badge_name, user.id,
                )
                continue
            # Award the badge
            await self._badge_repo.award_to_user(
                UserBadge(user_id=user.id, badge_id=badge.id)
            )
            new_badges.append(badge_name)
            logger.info(
                "Awarded badge '%s' to user %s",
                badge_name, user.id,
            )

        # Score-based badges
        if evaluation.overall_score >= _PERFECT_SCORE_THRESHOLD:
            new_badges.append("Perfect Score")

        return new_badges

    @staticmethod
    def _check_level_up(old_level: int, new_level: int) -> bool:
        """Return True if the user reached a new level."""
        return new_level > old_level
