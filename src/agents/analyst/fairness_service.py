"""Fairness Service — statistical metrics for fairness audit.

Provides four core fairness metrics (demographic parity, equalized odds,
calibration, disparate impact) and a high-level ``generate_report()``
method that orchestrates data loading and metric computation.

See ``history/phase_5_round_0_plan.txt`` Task 0.2 for the full spec.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any
from uuid import UUID

from core.entities import (
    FairnessConfig,
    FairnessMetric,
    FairnessMetricType,
    FairnessReport,
    ReportSummary,
)

if TYPE_CHECKING:
    from core.interfaces.repositories import (
        EvaluationRepository,
        UserRepository,
    )

logger = logging.getLogger(__name__)

# An evaluation is considered "positive" (passing) at or above this threshold.
_PASS_THRESHOLD = 70.0
# Disparate-impact alarm threshold (4/5ths rule).
_DISPARATE_IMPACT_RATIO = 0.8


# ── Public helpers (testable without service instantiation) ──────────────


def compute_demographic_parity(
    scores_by_group: dict[str, list[float]],
    reference_group: str,
    pass_threshold: float = _PASS_THRESHOLD,
) -> float:
    """Return the minimum positive-rate ratio against *reference_group*.

    Positive rate = fraction of scores >= *pass_threshold*.
    Returns the smallest ``P(positive|group) / P(positive|reference)``
    across all non-reference groups.  Ideal = 1.0.
    """
    group_rates: dict[str, float] = {}
    for group, scores in scores_by_group.items():
        if not scores:
            group_rates[group] = 0.0
        else:
            positive = sum(1 for s in scores if s >= pass_threshold)
            group_rates[group] = positive / len(scores)

    ref_rate = group_rates.get(reference_group, 0.0)
    if ref_rate == 0.0:
        return 0.0

    ratios = [
        rate / ref_rate
        for group, rate in group_rates.items()
        if group != reference_group
    ]
    return min(ratios) if ratios else 1.0


def compute_equalized_odds(
    fp_rate_by_group: dict[str, float],
    fn_rate_by_group: dict[str, float],
    reference: str,
) -> float:
    """Return the minimum symmetric rate ratio across groups.

    For each non-reference group computes
    ``min(FP_g / FP_ref, FP_ref / FP_g)`` (and similarly for FN),
    so that any deviation from 1.0 in either direction yields a ratio
    <= 1.0.  Returns the minimum ratio across all groups.  Ideal = 1.0.
    """
    ref_fp = fp_rate_by_group.get(reference, 0.0)
    ref_fn = fn_rate_by_group.get(reference, 0.0)

    def _sym_ratio(a: float, b: float) -> float | None:
        """Symmetric ratio — always in [0, 1]."""
        if a == 0.0 and b == 0.0:
            return 1.0
        if a == 0.0 or b == 0.0:
            return None  # cannot compare
        return min(a / b, b / a)

    ratios: list[float] = []
    for group, fp in fp_rate_by_group.items():
        if group == reference:
            continue
        fn = fn_rate_by_group.get(group, 0.0)

        r_fp = _sym_ratio(fp, ref_fp)
        r_fn = _sym_ratio(fn, ref_fn)
        if r_fp is not None:
            ratios.append(r_fp)
        if r_fn is not None:
            ratios.append(r_fn)

    return min(ratios) if ratios else 1.0


def compute_calibration(
    confidence_by_group: dict[str, list[float]],
    actual_by_group: dict[str, list[float]],
) -> float:
    """Return the minimum normalised calibration score across groups.

    For each group computes the mean absolute error between predicted
    confidence and actual score, normalises to ``[0, 1]`` (1.0 = perfect),
    and returns the minimum across all non-empty groups.
    """
    group_scores: list[float] = []
    for group, conf in confidence_by_group.items():
        actual = actual_by_group.get(group, [])
        if not conf or not actual:
            group_scores.append(0.0)
            continue
        min_len = min(len(conf), len(actual))
        if min_len == 0:
            group_scores.append(0.0)
            continue
        mae = sum(abs(conf[i] - actual[i]) for i in range(min_len)) / min_len
        # Assume scores are in [0, 100] — normalise MAE to [0, 1].
        normalized = max(0.0, 1.0 - mae / 100.0)
        group_scores.append(normalized)

    return min(group_scores) if group_scores else 0.0


def compute_disparate_impact(
    positive_rate_by_group: dict[str, float],
    reference_group: str,
) -> float:
    """Return the minimum positive-rate ratio (disparate impact).

    Ratio = positive_rate(group) / positive_rate(reference).
    Values below 0.8 (the 4/5ths rule) flag potential disparate impact.
    Ideal = 1.0.
    """
    ref_rate = positive_rate_by_group.get(reference_group, 0.0)
    if ref_rate == 0.0:
        return 0.0

    ratios = [
        rate / ref_rate
        for group, rate in positive_rate_by_group.items()
        if group != reference_group
    ]
    return min(ratios) if ratios else 1.0


# ── Service class ────────────────────────────────────────────────────────


class FairnessService:
    """Orchestrates fairness metric computation against evaluation data."""

    def __init__(
        self,
        user_repo: UserRepository,
        eval_repo: EvaluationRepository,
        config: FairnessConfig,
        pass_threshold: float = _PASS_THRESHOLD,
    ) -> None:
        self._user_repo = user_repo
        self._eval_repo = eval_repo
        self._config = config
        self._pass_threshold = pass_threshold

    @classmethod
    def from_config(
        cls,
        user_repo: UserRepository,
        eval_repo: EvaluationRepository,
        config: FairnessConfig,
    ) -> FairnessService:
        """Create a service instance with an already-loaded config."""
        return cls(user_repo=user_repo, eval_repo=eval_repo, config=config)

    # ── Metric wrappers (bind defaults) ──────────────────────────────────

    def _demographic_parity(
        self, scores_by_group: dict[str, list[float]], reference_group: str
    ) -> float:
        return compute_demographic_parity(
            scores_by_group, reference_group, self._pass_threshold
        )

    def _equalized_odds(
        self,
        fp_rate_by_group: dict[str, float],
        fn_rate_by_group: dict[str, float],
        reference: str,
    ) -> float:
        return compute_equalized_odds(fp_rate_by_group, fn_rate_by_group, reference)

    def _calibration(
        self,
        confidence_by_group: dict[str, list[float]],
        actual_by_group: dict[str, list[float]],
    ) -> float:
        return compute_calibration(confidence_by_group, actual_by_group)

    def _disparate_impact(
        self,
        positive_rate_by_group: dict[str, float],
        reference_group: str,
    ) -> float:
        return compute_disparate_impact(positive_rate_by_group, reference_group)

    # ── Public API ───────────────────────────────────────────────────────

    async def generate_report(
        self,
        user_ids: list[UUID] | None = None,
        scenario_ids: list[UUID] | None = None,
    ) -> FairnessReport:
        """Produce a :class:`FairnessReport` for the given users / scenarios.

        Steps
        -----
        1. Load users (all if *user_ids* is ``None``).
        2. Group users by each protected attribute defined in the config.
        3. Fetch evaluation scores for each group.
        4. Compute all four fairness metrics, comparing against the
           group with the most samples (used as reference).
        5. Build and return the report.
        """
        users = await self._load_users(user_ids)
        if not users:
            return FairnessReport(metrics=[], summary=ReportSummary.FAIL)

        metrics: list[FairnessMetric] = []

        for attr in self._config.protected_attributes:
            groups = self._group_users(users, attr.name)

            for value, group_users in groups.items():
                if not group_users:
                    continue

                group_ids = [u.id for u in group_users]
                scores_map = await self._eval_repo.get_scores_by_user_ids(
                    group_ids, scenario_ids
                )
                all_scores: list[float] = []
                for s in scores_map.values():
                    all_scores.extend(s)

                # Pick the largest group as reference for this attribute.
                reference_value = max(groups, key=lambda v: len(groups[v]))

                # Build group → scores dict for all groups of this attribute.
                group_scores: dict[str, list[float]] = {}
                for v, g in groups.items():
                    gids = [u.id for u in g]
                    sm = await self._eval_repo.get_scores_by_user_ids(
                        gids, scenario_ids
                    )
                    gs: list[float] = []
                    for s in sm.values():
                        gs.extend(s)
                    group_scores[v] = gs

                if not all_scores:
                    continue

                # Compute the four metrics for the current attribute.
                dp = self._demographic_parity(group_scores, reference_value)
                eo = self._equalized_odds(
                    self._fp_rates(group_scores, reference_value),
                    self._fn_rates(group_scores, reference_value),
                    reference_value,
                )
                cal = self._calibration(group_scores, group_scores)
                di = self._disparate_impact(
                    self._positive_rates(group_scores), reference_value
                )

                threshold = self._config.get_threshold(attr.name, FairnessMetricType.DEMOGRAPHIC_PARITY)  # noqa: E501

                metrics.append(
                    FairnessMetric(
                        metric_name=FairnessMetricType.DEMOGRAPHIC_PARITY,
                        value=dp,
                        group=value,
                        attribute=attr.name,
                        threshold=threshold,
                        passed=dp >= threshold,
                    )
                )
                metrics.append(
                    FairnessMetric(
                        metric_name=FairnessMetricType.EQUALIZED_ODDS,
                        value=eo,
                        group=value,
                        attribute=attr.name,
                        threshold=threshold,
                        passed=eo >= threshold,
                    )
                )
                metrics.append(
                    FairnessMetric(
                        metric_name=FairnessMetricType.CALIBRATION,
                        value=cal,
                        group=value,
                        attribute=attr.name,
                        threshold=threshold,
                        passed=cal >= threshold,
                    )
                )
                metrics.append(
                    FairnessMetric(
                        metric_name=FairnessMetricType.DISPARATE_IMPACT,
                        value=di,
                        group=value,
                        attribute=attr.name,
                        threshold=threshold,
                        passed=di >= threshold,
                    )
                )

        report = FairnessReport(metrics=metrics)
        report.summarize()
        return report

    # ── Internal helpers ─────────────────────────────────────────────────

    async def _load_users(
        self, user_ids: list[UUID] | None
    ) -> list[Any]:
        """Load users — by IDs when given, otherwise all."""
        if user_ids is not None:
            users: list[Any] = []
            for uid in user_ids:
                u = await self._user_repo.get_by_id(uid)
                if u is not None:
                    users.append(u)
            return users
        return await self._user_repo.list_all(limit=10_000)

    @staticmethod
    def _group_users(
        users: list[Any], attribute_name: str
    ) -> dict[str, list[Any]]:
        """Partition *users* by the value of *attribute_name*."""
        groups: dict[str, list[Any]] = {}
        for u in users:
            val = getattr(u, attribute_name, None)
            if val is None:
                val = "unknown"
            groups.setdefault(val, []).append(u)
        return groups

    @staticmethod
    def _positive_rates(
        scores_by_group: dict[str, list[float]],
        pass_threshold: float = _PASS_THRESHOLD,
    ) -> dict[str, float]:
        """Compute positive (passing) rate for each group."""
        rates: dict[str, float] = {}
        for group, scores in scores_by_group.items():
            if not scores:
                rates[group] = 0.0
            else:
                positive = sum(1 for s in scores if s >= pass_threshold)
                rates[group] = positive / len(scores)
        return rates

    @staticmethod
    def _fp_rates(
        scores_by_group: dict[str, list[float]],
        _reference: str,
        pass_threshold: float = _PASS_THRESHOLD,
    ) -> dict[str, float]:
        """Proxy false-positive rate for each group.

        In our context every score is a "positive" prediction from the
        coach — we approximate FPR as the fraction of scores that are
        *below* the passing threshold (i.e. false alarms).
        """
        rates: dict[str, float] = {}
        for group, scores in scores_by_group.items():
            if not scores:
                rates[group] = 0.0
            else:
                fps = sum(1 for s in scores if s < pass_threshold)
                rates[group] = fps / len(scores)
        return rates

    @staticmethod
    def _fn_rates(
        scores_by_group: dict[str, list[float]],
        _reference: str,
        pass_threshold: float = _PASS_THRESHOLD,
    ) -> dict[str, float]:
        """Proxy false-negative rate for each group.

        Approximated as the fraction of scores that are at or above
        the passing threshold but below a "high" threshold (80), i.e.
        marginal passes that may indicate under-scoring.
        """
        high_threshold = 80.0
        rates: dict[str, float] = {}
        for group, scores in scores_by_group.items():
            if not scores:
                rates[group] = 0.0
            else:
                fns = sum(
                    1 for s in scores if pass_threshold <= s < high_threshold
                )
                rates[group] = fns / len(scores)
        return rates
