"""LmsSyncResult — model for LMS synchronisation operation results."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum, auto
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from core.utils import utcnow


class LmsSyncStatus(StrEnum):
    """Status of an LMS sync operation."""

    PENDING = auto()
    IN_PROGRESS = auto()
    SUCCESS = auto()
    PARTIAL = auto()
    FAILED = auto()


class LmsSyncResult(BaseModel):
    """Result of an LMS synchronisation operation.

    Tracks the outcome of syncing a learning plan (or other entity)
    to an external LMS (e.g. iSpring Learn). Stores the remote
    course identifier, HTTP status, error details, and timing.
    """

    id: UUID = Field(default_factory=uuid4)
    learning_plan_id: UUID
    user_id: UUID
    tenant_id: UUID | None = None

    status: LmsSyncStatus = LmsSyncStatus.PENDING

    # Remote LMS identifiers
    lms_course_id: str = ""
    lms_url: str = ""

    # HTTP-level details
    http_status_code: int | None = None
    error_message: str = ""

    # Content snapshot
    focus_areas: list[str] = Field(default_factory=list)
    step_count: int = 0

    # Timing
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)

    # ── Helpers ─────────────────────────────────────────────────────────

    @property
    def is_success(self) -> bool:
        """Return True if the sync completed successfully."""
        return self.status == LmsSyncStatus.SUCCESS

    @property
    def duration_seconds(self) -> float | None:
        """Return the sync duration in seconds, or None if not finished."""
        if self.started_at is None or self.completed_at is None:
            return None
        return (self.completed_at - self.started_at).total_seconds()

    def mark_started(self) -> None:
        """Mark the sync as in progress."""
        self.status = LmsSyncStatus.IN_PROGRESS
        self.started_at = utcnow()

    def mark_completed(
        self,
        *,
        success: bool = True,
        lms_course_id: str = "",
        lms_url: str = "",
        http_status_code: int | None = None,
        error_message: str = "",
    ) -> None:
        """Finalise the sync result with outcome details."""
        self.status = (
            LmsSyncStatus.SUCCESS if success else LmsSyncStatus.FAILED
        )
        self.lms_course_id = lms_course_id
        self.lms_url = lms_url
        self.http_status_code = http_status_code
        self.error_message = error_message
        self.completed_at = utcnow()


class LmsSyncResultCreate(BaseModel):
    """DTO for initiating an LMS sync."""

    learning_plan_id: UUID
    user_id: UUID
    tenant_id: UUID | None = None
    focus_areas: list[str] = Field(default_factory=list)
    step_count: int = 0
