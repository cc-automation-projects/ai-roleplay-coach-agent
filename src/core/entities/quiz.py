"""MicroQuiz entity — short knowledge checks for operators."""

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from core.utils import SanitizedStr, utcnow


class QuizQuestion(BaseModel):
    """A single question in a micro-quiz."""

    question: SanitizedStr = Field(min_length=1)
    options: list[SanitizedStr] = Field(min_length=2)
    correct_index: int = Field(ge=0)
    explanation: SanitizedStr = ""


class MicroQuiz(BaseModel):
    """A short quiz tied to a scenario for skill reinforcement."""

    id: UUID = Field(default_factory=uuid4)
    scenario_id: UUID | None = None
    title: SanitizedStr = Field(min_length=1)
    questions: list[QuizQuestion] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utcnow)
