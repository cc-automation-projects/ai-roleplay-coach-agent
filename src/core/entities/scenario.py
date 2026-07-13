"""Scenario entity — a simulation scenario with client psychotype."""

from datetime import datetime
from enum import StrEnum, auto
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from core.utils import SanitizedStr, utcnow


class DifficultyLevel(StrEnum):
    """Difficulty level for the scenario."""

    BEGINNER = auto()
    INTERMEDIATE = auto()
    ADVANCED = auto()
    EXPERT = auto()


class Psychotype(StrEnum):
    """Client psychotype for the simulation."""

    AGGRESSIVE = auto()
    CONFUSED = auto()
    TECHNICALLY_INEPT = auto()
    FRAUDSTER = auto()
    NEUTRAL = auto()


class Scenario(BaseModel):
    """A simulation scenario with script references and configuration."""

    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID | None = None
    name: SanitizedStr = Field(min_length=1)
    description: SanitizedStr = Field(min_length=1)
    difficulty: DifficultyLevel = DifficultyLevel.BEGINNER
    psychotype: Psychotype = Psychotype.NEUTRAL
    script_ref: SanitizedStr = Field(min_length=1)
    script_text: SanitizedStr = Field(min_length=1)
    tags: list[str] = Field(default_factory=list)
    is_active: bool = True
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class ScenarioCreate(BaseModel):
    """DTO for creating a new scenario."""

    name: SanitizedStr = Field(min_length=1)
    description: SanitizedStr = Field(min_length=1)
    difficulty: DifficultyLevel = DifficultyLevel.BEGINNER
    psychotype: Psychotype = Psychotype.NEUTRAL
    script_ref: SanitizedStr = Field(min_length=1)
    script_text: SanitizedStr = Field(min_length=1)
    tags: list[str] = []
    tenant_id: UUID | None = None


class ScenarioUpdate(BaseModel):
    """DTO for updating scenario fields. All fields optional."""

    name: SanitizedStr | None = None
    description: SanitizedStr | None = None
    difficulty: DifficultyLevel | None = None
    psychotype: Psychotype | None = None
    script_ref: SanitizedStr | None = None
    script_text: SanitizedStr | None = None
    tags: list[str] | None = None
    is_active: bool | None = None
    tenant_id: UUID | None = None
