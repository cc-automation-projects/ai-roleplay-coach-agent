"""EvaluationService — persistence and analytics for evaluations.

Handles saving evaluations (with optional XP awards), computing
averages, trends, and grade summaries for users.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from core.entities import Evaluation, XPReason, XPTransaction

if TYPE_CHECKING:
    from uuid import UUID

    from core.interfaces.repositories import (
        EvaluationRepository,
        UserRepository,
        XPTransactionRepository,
    )

logger = logging.getLogger(__name__)


class EvaluationService:
    """Business logic for evaluation persistence and analytics."""

    def __init__(
        self,
        eval_repo: EvaluationRepository,
        user_repo: UserRepository,
        xp_repo: XPTransactionRepository,
        gamification_engine: Any | None = None,
        xp_for_passing: int = 100,
    ) -> None:
        self._eval_repo = eval_repo
        self._user_repo = user_repo
        self._xp_repo = xp_repo
        self._xp_for_passing = xp_for_passing
        self._gamification = gamification_engine

    async def save_evaluation(self, evaluation: Evaluation) -> Evaluation:
        """Persist an evaluation and award XP if passing.

        Uses the GamificationEngine when wired (for streak bonuses,
        badges, etc.), otherwise falls back to direct XP award.
        Returns the saved evaluation.
        """
        saved = await self._eval_repo.create(evaluation)

        if saved.is_passing:
            if self._gamification is not None:
                await self._gamification.award_session_completed(
                    evaluation=saved,
                )
            else:
                await self._award_xp(
                    user_id=saved.user_id,
                    session_id=saved.session_id,
                    amount=self._xp_for_passing,
                )

        return saved

    async def get_user_average(self, user_id: UUID) -> float:
        """Return the average overall score for a user."""
        return await self._eval_repo.get_average_score(user_id)

    async def get_user_trend(
        self,
        user_id: UUID,
        last_n: int = 10,
    ) -> list[dict]:
        """Return the last N evaluations as trend data points.

        Each entry contains score, grade, and session_id for charting.
        """
        evals = await self._eval_repo.list_by_user(
            user_id, skip=0, limit=last_n
        )
        return [
            {
                "session_id": str(e.session_id),
                "score": e.overall_score,
                "grade": e.grade,
                "created_at": e.created_at.isoformat(),
            }
            for e in evals
        ]

    async def get_user_grade_summary(self, user_id: UUID) -> dict:
        """Return grade distribution and average for a user."""
        evals = await self._eval_repo.list_by_user(
            user_id, skip=0, limit=1000
        )
        summary: dict[str, int] = {}
        total = 0.0
        for e in evals:
            summary[e.grade] = summary.get(e.grade, 0) + 1
            total += e.overall_score

        result: dict = {
            **summary,
            "total": len(evals),
            "average": round(total / len(evals), 1) if evals else 0.0,
        }
        return result

    async def _award_xp(
        self,
        user_id: UUID,
        session_id: UUID,
        amount: int,
    ) -> None:
        """Award XP for a passing session.

        Uses the GamificationEngine when wired, else falls back to
        direct repository calls.
        """
        if self._gamification is not None:
            await self._gamification.award_session_completed(
                user_id=user_id,
                session_id=session_id,
            )
            return

        # Fallback: direct XP write
        txn = XPTransaction(
            user_id=user_id,
            amount=amount,
            reason=XPReason.SESSION_COMPLETED,
            reference_id=session_id,
        )
        await self._xp_repo.create(txn)
        user = await self._user_repo.get_by_id(user_id)
        if user is not None:
            user.add_xp(amount)
            await self._user_repo.update(user)
