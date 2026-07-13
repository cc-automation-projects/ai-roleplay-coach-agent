"""Unit tests for fairness entities."""

from uuid import UUID

import pytest
from pydantic import ValidationError

from core.entities import (
    AlertingConfig,
    FairnessConfig,
    FairnessMetric,
    FairnessMetricType,
    FairnessReport,
    ProtectedAttribute,
    ReportSummary,
)


class TestProtectedAttribute:
    def test_create(self) -> None:
        attr = ProtectedAttribute(
            name="gender", values=["male", "female"],
        )
        assert attr.name == "gender"
        assert attr.values == ["male", "female"]

    def test_default_description(self) -> None:
        attr = ProtectedAttribute(name="age", values=["18-25"])
        assert attr.description == ""


class TestFairnessMetric:
    def test_create(self) -> None:
        m = FairnessMetric(
            metric_name=FairnessMetricType.DEMOGRAPHIC_PARITY,
            value=0.95, group="female", attribute="gender",
            threshold=0.8, passed=True,
        )
        assert m.value == 0.95
        assert m.passed is True

    def test_value_out_of_range(self) -> None:
        with pytest.raises(ValidationError):
            FairnessMetric(
                metric_name=FairnessMetricType.CALIBRATION,
                value=1.5, group="all", attribute="age",
                threshold=0.8, passed=True,
            )


class TestFairnessReport:
    def test_create_with_uuid(self) -> None:
        r = FairnessReport()
        assert isinstance(r.report_id, UUID)
        assert r.summary == ReportSummary.PASS

    def test_summarize_all_pass(self) -> None:
        r = FairnessReport(metrics=[
            FairnessMetric(
                metric_name=FairnessMetricType.DEMOGRAPHIC_PARITY,
                value=0.9, group="x", attribute="g",
                threshold=0.8, passed=True,
            ),
            FairnessMetric(
                metric_name=FairnessMetricType.EQUALIZED_ODDS,
                value=0.85, group="x", attribute="g",
                threshold=0.8, passed=True,
            ),
        ])
        assert r.summarize() == ReportSummary.PASS

    def test_summarize_all_fail(self) -> None:
        r = FairnessReport(metrics=[
            FairnessMetric(
                metric_name=FairnessMetricType.CALIBRATION,
                value=0.5, group="x", attribute="g",
                threshold=0.8, passed=False,
            ),
        ])
        assert r.summarize() == ReportSummary.FAIL

    def test_summarize_partial(self) -> None:
        r = FairnessReport(metrics=[
            FairnessMetric(
                metric_name=FairnessMetricType.DEMOGRAPHIC_PARITY,
                value=0.9, group="x", attribute="g",
                threshold=0.8, passed=True,
            ),
            FairnessMetric(
                metric_name=FairnessMetricType.CALIBRATION,
                value=0.5, group="x", attribute="g",
                threshold=0.8, passed=False,
            ),
        ])
        assert r.summarize() == ReportSummary.PARTIAL

    def test_summarize_empty_fails(self) -> None:
        r = FairnessReport(metrics=[])
        assert r.summarize() == ReportSummary.FAIL


class TestAlertingConfig:
    def test_defaults(self) -> None:
        cfg = AlertingConfig()
        assert cfg.enabled is True
        assert cfg.threshold_breach_action == "log"
        assert cfg.notification_recipients == []

    def test_custom(self) -> None:
        cfg = AlertingConfig(
            enabled=False,
            threshold_breach_action="warn",
            notification_recipients=["admin@test.com"],
        )
        assert cfg.enabled is False


class TestFairnessConfig:
    def test_defaults(self) -> None:
        cfg = FairnessConfig()
        assert cfg.protected_attributes == []
        assert cfg.alerting.enabled is True

    def test_from_dict(self) -> None:
        data = {
            "protected_attributes": [
                {"name": "gender", "values": ["m", "f"], "description": ""},
            ],
            "alerting": {
                "enabled": True,
                "threshold_breach_action": "log",
                "notification_recipients": [],
            },
        }
        cfg = FairnessConfig.from_dict(data)
        assert len(cfg.protected_attributes) == 1
        assert cfg.alerting.enabled is True

    def test_from_dict_empty(self) -> None:
        cfg = FairnessConfig.from_dict({})
        assert cfg.protected_attributes == []

    def test_get_threshold_default(self) -> None:
        cfg = FairnessConfig()
        assert cfg.get_threshold("gender", FairnessMetricType.DEMOGRAPHIC_PARITY) == 0.8
