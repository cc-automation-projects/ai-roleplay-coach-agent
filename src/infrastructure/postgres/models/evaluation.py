"""SQLAlchemy model for the Evaluation aggregate."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Float, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from core.utils import utcnow

from .base import Base


class EvaluationModel(Base):
    __tablename__ = "evaluations"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    session_id: Mapped[UUID]
    user_id: Mapped[UUID]
    overall_score: Mapped[float] = mapped_column(Float)
    script_adherence: Mapped[float] = mapped_column(Float)
    tone_score: Mapped[float] = mapped_column(Float)
    empathy_score: Mapped[float] = mapped_column(Float)
    objection_handling: Mapped[float] = mapped_column(Float)
    completeness_score: Mapped[float] = mapped_column(Float)
    tenant_id: Mapped[UUID | None] = mapped_column(nullable=True)
    praise_text: Mapped[str] = mapped_column(String, default="")
    growth_text: Mapped[str] = mapped_column(String, default="")
    closing_text: Mapped[str] = mapped_column(String, default="")
    script_citations: Mapped[list[str] | None] = mapped_column(ARRAY(String), default_factory=list)
    gaming_detected: Mapped[bool] = mapped_column(Boolean, default=False)
    gaming_notes: Mapped[str] = mapped_column(String, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default_factory=utcnow)
