"""XP and metric entities for gamification and analytics."""

from datetime import datetime
from enum import StrEnum, auto
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from core.utils import utcnow


class XPReason(StrEnum):
    """Reason for XP award."""

    SESSION_COMPLETED = auto()
    HIGH_SCORE = auto()
    BADGE_EARNED = auto()
    CHALLENGE_COMPLETED = auto()
    STREAK_BONUS = auto()
    TRAINER_BONUS = auto()


class XPTransaction(BaseModel):
    """A single XP award or deduction record."""

    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    amount: int  # positive = award, negative = penalty
    reason: XPReason
    reference_id: UUID | None = None  # e.g., session_id, badge_id
    created_at: datetime = Field(default_factory=utcnow)


class MetricType(StrEnum):
    """Types of performance metrics tracked."""

    AVG_SCORE = auto()
    SCRIPTS_COMPLETED = auto()
    TOTAL_SESSIONS = auto()
    IMPROVEMENT_RATE = auto()
    AVG_RESOLUTION_TIME = auto()


class Metric(BaseModel):
    """A time-series metric record for analytics."""

    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    metric_type: MetricType
    value: float
    recorded_at: datetime = Field(default_factory=utcnow)
