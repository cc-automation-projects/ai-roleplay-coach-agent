"""Fairness audit entities."""
from __future__ import annotations

from datetime import datetime
from enum import StrEnum, auto
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from core.utils import utcnow


class FairnessMetricType(StrEnum):
    DEMOGRAPHIC_PARITY = auto()
    EQUALIZED_ODDS = auto()
    CALIBRATION = auto()
    DISPARATE_IMPACT = auto()


class ReportSummary(StrEnum):
    PASS = auto()
    FAIL = auto()
    PARTIAL = auto()


class ProtectedAttribute(BaseModel):
    name: str
    values: list[str]
    description: str = ""


class FairnessMetric(BaseModel):
    metric_name: FairnessMetricType
    value: float = Field(ge=0.0, le=1.0)
    group: str
    attribute: str
    threshold: float = Field(ge=0.0, le=1.0)
    passed: bool


class FairnessReport(BaseModel):
    report_id: UUID = Field(default_factory=uuid4)
    generated_at: datetime = Field(default_factory=utcnow)
    metrics: list[FairnessMetric] = Field(default_factory=list)
    summary: ReportSummary = ReportSummary.PASS
    config_version: str = "1.0"

    def summarize(self) -> ReportSummary:
        if not self.metrics:
            self.summary = ReportSummary.FAIL
            return self.summary
        passed_count = sum(1 for m in self.metrics if m.passed)
        total = len(self.metrics)
        if passed_count == total:
            self.summary = ReportSummary.PASS
        elif passed_count == 0:
            self.summary = ReportSummary.FAIL
        else:
            self.summary = ReportSummary.PARTIAL
        return self.summary


class AlertingConfig(BaseModel):
    enabled: bool = True
    threshold_breach_action: str = "log"
    notification_recipients: list[str] = Field(default_factory=list)


class FairnessConfig(BaseModel):
    protected_attributes: list[ProtectedAttribute] = Field(default_factory=list)
    alerting: AlertingConfig = Field(default_factory=AlertingConfig)

    @classmethod
    def from_dict(cls, data: dict) -> FairnessConfig:
        attr_list = data.get("protected_attributes", [])
        attrs = [ProtectedAttribute(**a) for a in attr_list]
        alert_raw = data.get("alerting", {}) or {}
        alert = AlertingConfig(**alert_raw)
        return cls(protected_attributes=attrs, alerting=alert)

    def get_threshold(self, _attribute_name: str, _metric: FairnessMetricType) -> float:
        return 0.8
