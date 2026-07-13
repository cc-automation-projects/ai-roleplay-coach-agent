"""DTO for fairness audit API responses."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class GroupSummary(BaseModel):
    """Summary of a single demographic group within a fairness report."""

    name: str
    value: str
    user_count: int
    metrics: dict[str, float]
    passed: bool


class FairnessReportResponse(BaseModel):
    """API response wrapping a :class:`FairnessReport`."""

    report_id: UUID
    generated_at: datetime
    summary: str
    config_version: str
    metrics: list[dict]
    groups_analyzed: list[GroupSummary] = []
