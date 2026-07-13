"""Evaluation entity — feedback and scoring for a session."""

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from core.utils import SanitizedStr, utcnow

_MIN_SCORE = 0.0
_MAX_SCORE = 100.0
_PASS_THRESHOLD = 70.0
_GRADE_A = 90
_GRADE_B = 80
_GRADE_C = 70
_GRADE_D = 60


class Evaluation(BaseModel):
    """Post-session evaluation with feedback and score."""

    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID | None = None
    session_id: UUID
    user_id: UUID

    # Scores (0.0 - 100.0)
    overall_score: float = Field(ge=_MIN_SCORE, le=_MAX_SCORE)
    script_adherence: float = Field(ge=_MIN_SCORE, le=_MAX_SCORE)
    tone_score: float = Field(ge=_MIN_SCORE, le=_MAX_SCORE)
    empathy_score: float = Field(ge=_MIN_SCORE, le=_MAX_SCORE)
    objection_handling: float = Field(ge=_MIN_SCORE, le=_MAX_SCORE)
    completeness_score: float = Field(ge=_MIN_SCORE, le=_MAX_SCORE)

    # Feedback text
    praise_text: SanitizedStr = ""
    growth_text: SanitizedStr = ""
    closing_text: SanitizedStr = ""

    # Citations from scripts (RAG-backed)
    script_citations: list[SanitizedStr] = Field(default_factory=list)

    # Anti-gaming flags
    gaming_detected: bool = False
    gaming_notes: SanitizedStr = ""

    created_at: datetime = Field(default_factory=utcnow)

    @property
    def is_passing(self) -> bool:
        """Check if the session passed."""
        return self.overall_score >= _PASS_THRESHOLD

    @property
    def grade(self) -> str:
        """Return letter grade from score."""
        if self.overall_score >= _GRADE_A:
            return "A"
        if self.overall_score >= _GRADE_B:
            return "B"
        if self.overall_score >= _GRADE_C:
            return "C"
        if self.overall_score >= _GRADE_D:
            return "D"
        return "F"


class EvaluationCreate(BaseModel):
    """DTO for creating an evaluation (scores without feedback)."""

    session_id: UUID
    user_id: UUID
    tenant_id: UUID | None = None
    overall_score: float = Field(ge=_MIN_SCORE, le=_MAX_SCORE)
    script_adherence: float = Field(ge=_MIN_SCORE, le=_MAX_SCORE)
    tone_score: float = Field(ge=_MIN_SCORE, le=_MAX_SCORE)
    empathy_score: float = Field(ge=_MIN_SCORE, le=_MAX_SCORE)
    objection_handling: float = Field(ge=_MIN_SCORE, le=_MAX_SCORE)
    completeness_score: float = Field(ge=_MIN_SCORE, le=_MAX_SCORE)
