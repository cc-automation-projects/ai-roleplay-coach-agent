"""LearningPlan entity — study plan with progressive difficulty."""

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from core.utils import SanitizedStr, utcnow


class PlanStep(BaseModel):
    """A single actionable step in a learning plan."""

    order: int = Field(ge=1)
    title: SanitizedStr = Field(min_length=1)
    description: SanitizedStr = Field(min_length=1)
    estimated_minutes: int = Field(ge=1, default=10)


class LearningPlan(BaseModel):
    """Personalised learning plan based on evaluation weaknesses."""

    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    scenario_id: UUID | None = None

    focus_areas: list[SanitizedStr] = Field(default_factory=list)
    steps: list[PlanStep] = Field(default_factory=list)

    difficulty_label: SanitizedStr = "beginner"
    created_at: datetime = Field(default_factory=utcnow)
