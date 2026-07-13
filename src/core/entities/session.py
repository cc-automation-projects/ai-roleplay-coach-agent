"""Session entity — a single simulation session."""

from datetime import datetime
from enum import StrEnum, auto
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, model_validator

from core.entities.scenario import DifficultyLevel, Psychotype
from core.utils import SanitizedStr, utcnow

_MAX_TRANSCRIPT_LENGTH = 100


class SessionStatus(StrEnum):
    """Status of a simulation session."""

    PENDING = auto()
    IN_PROGRESS = auto()
    COMPLETED = auto()
    INTERRUPTED = auto()
    FAILED = auto()


class TranscriptEntry(BaseModel):
    """A single turn in the session transcript."""

    speaker: Literal["operator", "client"]
    text: SanitizedStr = Field(
        description="PII-sensitive: transcript text may contain personal data"
    )
    timestamp: datetime = Field(default_factory=utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Session(BaseModel):
    """A single simulation session between operator and AI client."""

    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID | None = None
    user_id: UUID
    scenario_id: UUID
    status: SessionStatus = SessionStatus.PENDING
    transcript: list[TranscriptEntry] = Field(default_factory=list)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    difficulty_at_start: DifficultyLevel | None = None
    psychotype_at_start: Psychotype | None = None
    script_text_at_start: str | None = Field(
        default=None,
        description="Script text at session start — used to provide context to LLM simulator"
    )
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    @model_validator(mode="after")
    def _trim_transcript(self) -> "Session":
        """Limit transcript to max 100 entries (oldest dropped)."""
        if len(self.transcript) > _MAX_TRANSCRIPT_LENGTH:
            self.transcript = self.transcript[-_MAX_TRANSCRIPT_LENGTH:]
        return self

    def append_transcript_entry(
        self,
        speaker: Literal["operator", "client"],
        text: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Thread-safe transcript append (avoids race conditions with parallel LiveKit writes)."""
        entry = TranscriptEntry(speaker=speaker, text=text, metadata=metadata or {})
        self.transcript.append(entry)
        if len(self.transcript) > _MAX_TRANSCRIPT_LENGTH:
            self.transcript = self.transcript[-_MAX_TRANSCRIPT_LENGTH:]
        self.updated_at = utcnow()


class SessionCreate(BaseModel):
    """DTO for starting a new session."""

    user_id: UUID
    scenario_id: UUID
    tenant_id: UUID | None = None
    status: SessionStatus = SessionStatus.PENDING
    transcript: list[TranscriptEntry] = Field(default_factory=list)
    difficulty_at_start: DifficultyLevel | None = None
    psychotype_at_start: Psychotype | None = None
    script_text_at_start: str | None = None


class SessionUpdate(BaseModel):
    """DTO for updating session fields. All fields optional."""

    status: SessionStatus | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    difficulty_at_start: DifficultyLevel | None = None
    psychotype_at_start: Psychotype | None = None
    script_text_at_start: str | None = None
    transcript: list[TranscriptEntry] | None = None
