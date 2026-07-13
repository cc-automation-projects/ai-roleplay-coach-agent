"""Analyst service — metrics and dashboards for session evaluations.

Provides session statistics, score distribution histograms, progress
over time, and global aggregate stats used by the Analyst API.
"""

from __future__ import annotations

import logging
from collections import Counter
from datetime import datetime
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

from core.entities import SessionStatus

if TYPE_CHECKING:
    from uuid import UUID

    from core.interfaces.repositories import (
        EvaluationRepository,
        SessionRepository,
        UserRepository,
    )

logger = logging.getLogger(__name__)


class SessionStats(BaseModel):
    """Aggregated session performance metrics for a user or globally."""

    total_sessions: int = 0
    completed_sessions: int = 0
    abandoned_sessions: int = 0
    avg_overall_score: float = 0.0
    max_overall_score: float = 0.0
    min_overall_score: float = 0.0
    avg_script_adherence: float = 0.0
    avg_tone_score: float = 0.0
    avg_empathy_score: float = 0.0
    avg_objection_handling: float = 0.0
    avg_completeness_score: float = 0.0


class ScoreDistribution(BaseModel):
    """Histogram bins for a single evaluation dimension."""

    dimension: str
    bins: dict[str, int]


class ProgressPoint(BaseModel):
    """A single data point in a progress-over-time series."""

    date: datetime
    overall_score: float


class GlobalStats(BaseModel):
    """Aggregate platform-wide statistics."""

    total_users: int = 0
    total_sessions: int = 0
    avg_score: float = 0.0
    top_scenario: str | None = None


BINS: list[tuple[int, int]] = [
    (0, 20),
    (21, 40),
    (41, 60),
    (61, 80),
    (81, 90),
    (91, 100),
]

DIMENSIONS: list[str] = [
    "overall_score",
    "script_adherence",
    "tone_score",
    "empathy_score",
    "objection_handling",
    "completeness_score",
]


def _build_histogram(values: list[float]) -> dict[str, int]:
    """Bin scores into the standard 6-bin histogram."""
    counts: dict[str, int] = {}
    for lo, hi in BINS:
        label = f"{lo}-{hi}"
        counts[label] = sum(1 for v in values if lo <= int(v) <= hi)
    return counts


def _avg(values: list[float]) -> float:
    """Safe average returning 0.0 for empty lists."""
    if not values:
        return 0.0
    return sum(values) / len(values)


class AnalystService:
    """Collects and computes analytics from evaluation and session data."""

    def __init__(
        self,
        eval_repo: EvaluationRepository,
        session_repo: SessionRepository,
        user_repo: UserRepository,
    ) -> None:
        self._eval_repo = eval_repo
        self._session_repo = session_repo
        self._user_repo = user_repo

    # ── Public accessors (for tests / extension) ────────────────────────

    @property
    def eval_repo(self) -> EvaluationRepository:
        """Expose the evaluation repository (used in tests)."""
        return self._eval_repo

    @property
    def session_repo(self) -> SessionRepository:
        """Expose the session repository (used in tests)."""
        return self._session_repo

    @property
    def user_repo(self) -> UserRepository:
        """Expose the user repository (used in tests)."""
        return self._user_repo

    # ── Public API ──────────────────────────────────────────────────────

    async def get_session_stats(
        self, user_id: UUID | None = None
    ) -> SessionStats:
        """Return aggregated session stats for a user or globally."""
        evaluations = await self._get_evaluations(user_id)
        sessions = await self._get_sessions(user_id)

        total, completed, abandoned = self._count_sessions(sessions)
        max_score, min_score = self._find_extremes(evaluations)
        scores = [e.overall_score for e in evaluations]
        avg_scores = self._average_scores(evaluations)

        return SessionStats(
            total_sessions=total,
            completed_sessions=completed,
            abandoned_sessions=abandoned,
            avg_overall_score=_avg(scores),
            max_overall_score=max_score,
            min_overall_score=min_score,
            **avg_scores,
        )

    async def get_score_distribution(
        self, user_id: UUID | None = None
    ) -> list[ScoreDistribution]:
        """Return histogram bins for each evaluation dimension."""
        evaluations = await self._get_evaluations(user_id)

        results: list[ScoreDistribution] = []
        for dim in DIMENSIONS:
            values = [getattr(e, dim) for e in evaluations]
            results.append(
                ScoreDistribution(
                    dimension=dim, bins=_build_histogram(values)
                )
            )
        return results

    async def get_progress_over_time(
        self, user_id: UUID, limit: int = 20
    ) -> list[ProgressPoint]:
        """Return a time-series of overall scores for a user."""
        evaluations = await self._eval_repo.list_by_user(user_id, limit=10_000)
        points = [
            ProgressPoint(date=e.created_at, overall_score=e.overall_score)
            for e in evaluations
        ]
        points.sort(key=lambda p: p.date)
        return points[-limit:]

    async def get_global_stats(self) -> GlobalStats:
        """Return aggregate platform-wide statistics."""
        all_evals = await self._eval_repo.list_all(limit=10_000)
        all_sessions = await self._session_repo.list_all(limit=10_000)

        scores = [e.overall_score for e in all_evals]

        # Find top scenario (most common scenario_id among completed sessions)
        scenario_counts: Counter[str] = Counter()
        for s in all_sessions:
            if s.scenario_id and s.status == SessionStatus.COMPLETED:
                scenario_counts[str(s.scenario_id)] += 1

        top_scenario_id = (
            scenario_counts.most_common(1)[0][0] if scenario_counts else None
        )

        return GlobalStats(
            total_users=await self._user_repo.count(),
            total_sessions=len(all_sessions),
            avg_score=_avg(scores),
            top_scenario=top_scenario_id,
        )

    # ── Internal helpers ────────────────────────────────────────────────

    async def _get_evaluations(self, user_id: UUID | None) -> list[Any]:
        """Return all evaluations, optionally filtered by user."""
        if user_id is not None:
            return await self._eval_repo.list_by_user(user_id, limit=10_000)
        return await self._eval_repo.list_all()

    async def _get_sessions(self, user_id: UUID | None) -> list[Any]:
        """Return all sessions, optionally filtered by user."""
        if user_id is not None:
            return await self._session_repo.list_by_user(user_id, limit=10_000)
        return await self._session_repo.list_all()

    @staticmethod
    def _count_sessions(
        sessions: list[Any],
    ) -> tuple[int, int, int]:
        """Return (total, completed, abandoned) counts."""
        statuses = [s.status for s in sessions]
        completed = statuses.count(SessionStatus.COMPLETED)
        abandoned = statuses.count(SessionStatus.INTERRUPTED) + statuses.count(
            SessionStatus.FAILED
        )
        return len(sessions), completed, abandoned

    @staticmethod
    def _find_extremes(evaluations: list[Any]) -> tuple[float, float]:
        """Return (max_overall_score, min_overall_score)."""
        scores = [e.overall_score for e in evaluations]
        if scores:
            return max(scores), min(scores)
        return 0.0, 0.0

    @staticmethod
    def _average_scores(evaluations: list[Any]) -> dict[str, float]:
        """Return average per evaluation dimension."""
        prefix = "avg_"
        out: dict[str, float] = {}
        out[prefix + "script_adherence"] = _avg(
            [e.script_adherence for e in evaluations]
        )
        out[prefix + "tone_score"] = _avg(
            [e.tone_score for e in evaluations]
        )
        out[prefix + "empathy_score"] = _avg(
            [e.empathy_score for e in evaluations]
        )
        out[prefix + "objection_handling"] = _avg(
            [e.objection_handling for e in evaluations]
        )
        out[prefix + "completeness_score"] = _avg(
            [e.completeness_score for e in evaluations]
        )
        return out
