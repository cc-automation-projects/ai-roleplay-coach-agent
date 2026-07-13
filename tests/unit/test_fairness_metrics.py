"""Unit tests for fairness metric functions and FairnessService."""

from __future__ import annotations

from uuid import uuid4

import pytest

from agents.analyst.fairness_service import (
    FairnessService,
    compute_calibration,
    compute_demographic_parity,
    compute_disparate_impact,
    compute_equalized_odds,
)
from core.entities import (
    FairnessConfig,
    ProtectedAttribute,
    ReportSummary,
)
from infrastructure.memory.repositories import (
    InMemoryEvaluationRepository,
    InMemoryUserRepository,
)

# ── Demographic parity ────────────────────────────────────────────────────


class TestDemographicParity:
    def test_equal_rates(self) -> None:
        """Equal positive rates across groups → 1.0."""
        scores = {
            "male": [80.0, 85.0, 90.0],
            "female": [75.0, 88.0, 92.0],
        }
        result = compute_demographic_parity(scores, reference_group="male")
        assert result == pytest.approx(1.0, abs=0.01)

    def test_unequal_rates(self) -> None:
        """Unequal positive rates → < 1.0 but > 0.0."""
        scores = {
            "male": [80.0, 85.0, 90.0],
            "female": [75.0, 40.0, 50.0],  # 1/3 passing → rate ~0.33
        }
        result = compute_demographic_parity(scores, reference_group="male")
        # male rate = 1.0, female rate ≈ 0.33, ratio ≈ 0.33
        assert result < 1.0
        assert result > 0.0

    def test_empty_group(self) -> None:
        """Empty group does not crash and returns 0.0."""
        scores = {
            "male": [],
            "female": [80.0, 85.0],
        }
        result = compute_demographic_parity(scores, reference_group="male")
        assert result == 0.0


# ── Equalized odds ────────────────────────────────────────────────────────


class TestEqualizedOdds:
    def test_equal_rates(self) -> None:
        """Equal TPR / FPR across groups → 1.0."""
        fp = {"male": 0.1, "female": 0.1}
        fn = {"male": 0.2, "female": 0.2}
        result = compute_equalized_odds(fp, fn, reference="male")
        assert result == pytest.approx(1.0, abs=0.01)

    def test_different_rates(self) -> None:
        """Different TPR / FPR → < 1.0."""
        fp = {"male": 0.1, "female": 0.4}
        fn = {"male": 0.2, "female": 0.5}
        result = compute_equalized_odds(fp, fn, reference="male")
        # fp ratio = min(0.4/0.1, 0.1/0.4) = 0.25
        # fn ratio = min(0.5/0.2, 0.2/0.5) = 0.40
        # min of [0.25, 0.40] ≈ 0.25
        assert result < 1.0
        assert result == pytest.approx(0.25, abs=0.01)


# ── Calibration ───────────────────────────────────────────────────────────


class TestCalibration:
    def test_perfect(self) -> None:
        """Identical confidence and actual scores → 1.0."""
        conf = {"group_a": [80.0, 85.0, 90.0]}
        actual = {"group_a": [80.0, 85.0, 90.0]}
        result = compute_calibration(conf, actual)
        assert result == pytest.approx(1.0, abs=0.01)

    def test_with_error(self) -> None:
        """Non-zero MAE → < 1.0."""
        conf = {"group_a": [80.0, 85.0, 90.0]}
        actual = {"group_a": [50.0, 55.0, 60.0]}
        result = compute_calibration(conf, actual)
        assert result < 1.0
        assert result > 0.0


# ── Disparate impact ──────────────────────────────────────────────────────


class TestDisparateImpact:
    def test_acceptable(self) -> None:
        """Ratio >= 0.8 → acceptable."""
        rates = {"male": 0.6, "female": 0.55}
        result = compute_disparate_impact(rates, reference_group="male")
        # female rate = 0.55 / 0.6 ≈ 0.917 > 0.8
        assert result >= 0.8

    def test_flagged(self) -> None:
        """Ratio < 0.8 → flagged (disparate impact)."""
        rates = {"male": 0.6, "female": 0.3}
        result = compute_disparate_impact(rates, reference_group="male")
        # female rate = 0.3 / 0.6 = 0.5 < 0.8
        assert result < 0.8


# ── FairnessService.generate_report ──────────────────────────────────────


class TestGenerateReport:
    """Integration-style tests for the full report pipeline."""

    @pytest.fixture
    def empty_user_repo(self) -> InMemoryUserRepository:
        return InMemoryUserRepository()

    @pytest.fixture
    def empty_eval_repo(self) -> InMemoryEvaluationRepository:
        return InMemoryEvaluationRepository()

    @pytest.fixture
    def config(self) -> FairnessConfig:
        return FairnessConfig(
            protected_attributes=[
                ProtectedAttribute(
                    name="gender",
                    values=["male", "female"],
                    description="Gender",
                ),
            ],
        )

    async def test_empty_data_returns_fail(
        self,
        empty_user_repo: InMemoryUserRepository,
        empty_eval_repo: InMemoryEvaluationRepository,
        config: FairnessConfig,
    ) -> None:
        """Empty data → metrics mostly 0.0, summary FAIL, no crash."""
        service = FairnessService(
            user_repo=empty_user_repo,
            eval_repo=empty_eval_repo,
            config=config,
        )
        report = await service.generate_report()
        assert report.summary == ReportSummary.FAIL
        assert len(report.metrics) == 0

    async def test_generate_report_smoke(
        self,
        empty_user_repo: InMemoryUserRepository,
        empty_eval_repo: InMemoryEvaluationRepository,
        config: FairnessConfig,
    ) -> None:
        """Smoke test: generate_report doesn't crash with unknown IDs."""
        service = FairnessService(
            user_repo=empty_user_repo,
            eval_repo=empty_eval_repo,
            config=config,
        )
        report = await service.generate_report(
            user_ids=[uuid4()],
            scenario_ids=[uuid4()],
        )
        assert report.summary in (ReportSummary.FAIL, ReportSummary.PASS)
