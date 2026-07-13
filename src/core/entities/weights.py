"""Evaluation weights — configurable dimension scoring weights.

Allows per-tenant or per-scenario weighting of the five CoachAgent
scoring dimensions. When no custom weights are defined, default
equal-weight (uniform) scoring is used.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator

from core.utils import utcnow

_DEFAULT_WEIGHT = 1.0
_SUM_TARGET = 5.0  # sum of all weights when normalised


class EvaluationWeights(BaseModel):
    """Per-dimension weights for coach evaluation scoring.

    All weights default to 1.0 (equal weight). Custom weights are
    normalised so that they sum to ``_SUM_TARGET`` (5.0) before being
    applied in the weighted average computation.

    Attributes:
        tenant_id:  Optional tenant scope (None = global default).
        scenario_id: Optional scenario scope (None = tenant default).
        script_adherence: Weight for the script-adherence dimension.
        tone_score: Weight for the tone dimension.
        empathy_score: Weight for the empathy dimension.
        objection_handling: Weight for the objection-handling dimension.
        completeness_score: Weight for the completeness dimension.
    """

    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID | None = None
    scenario_id: UUID | None = None

    script_adherence: float = _DEFAULT_WEIGHT
    tone_score: float = _DEFAULT_WEIGHT
    empathy_score: float = _DEFAULT_WEIGHT
    objection_handling: float = _DEFAULT_WEIGHT
    completeness_score: float = _DEFAULT_WEIGHT

    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    @field_validator(
        "script_adherence",
        "tone_score",
        "empathy_score",
        "objection_handling",
        "completeness_score",
        mode="before",
    )
    @classmethod
    def _validate_non_negative(cls, v: float) -> float:
        if v < 0:
            msg = f"Weight must be non-negative, got {v}"
            raise ValueError(msg)
        return v

    # ── Public helpers ──────────────────────────────────────────────────

    def normalised(self) -> EvaluationWeights:
        """Return a new instance with weights normalised to sum 5.0.

        Normalisation preserves relative ratios while making the sum
        predictable, so that substituting custom weights for defaults
        does not inflate or deflate overall scores.
        """
        raw = [
            self.script_adherence,
            self.tone_score,
            self.empathy_score,
            self.objection_handling,
            self.completeness_score,
        ]
        total = sum(raw)
        if total == 0:
            # All zeros → fall back to uniform
            return EvaluationWeights(
                tenant_id=self.tenant_id,
                scenario_id=self.scenario_id,
            )
        factor = _SUM_TARGET / total
        return EvaluationWeights(
            tenant_id=self.tenant_id,
            scenario_id=self.scenario_id,
            script_adherence=round(self.script_adherence * factor, 4),
            tone_score=round(self.tone_score * factor, 4),
            empathy_score=round(self.empathy_score * factor, 4),
            objection_handling=round(self.objection_handling * factor, 4),
            completeness_score=round(self.completeness_score * factor, 4),
        )

    @staticmethod
    def default() -> EvaluationWeights:
        """Return default equal-weight configuration."""
        return EvaluationWeights()

    def as_dict(self) -> dict[str, float]:
        """Return dimension → weight mapping for the weighted average."""
        return {
            "script_adherence": self.script_adherence,
            "tone_score": self.tone_score,
            "empathy_score": self.empathy_score,
            "objection_handling": self.objection_handling,
            "completeness_score": self.completeness_score,
        }


class EvaluationWeightsCreate(BaseModel):
    """DTO for creating custom evaluation weights."""

    tenant_id: UUID | None = None
    scenario_id: UUID | None = None
    script_adherence: float = _DEFAULT_WEIGHT
    tone_score: float = _DEFAULT_WEIGHT
    empathy_score: float = _DEFAULT_WEIGHT
    objection_handling: float = _DEFAULT_WEIGHT
    completeness_score: float = _DEFAULT_WEIGHT
