"""SQLAlchemy model for the Scenario aggregate."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from core.utils import utcnow

from .base import Base


class ScenarioModel(Base):
    __tablename__ = "scenarios"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(256))
    description: Mapped[str]
    script_ref: Mapped[str] = mapped_column(String(512))
    script_text: Mapped[str]
    tenant_id: Mapped[UUID | None] = mapped_column(nullable=True)
    tags: Mapped[list[str] | None] = mapped_column(ARRAY(String), default_factory=list)
    difficulty: Mapped[str] = mapped_column(String(32), default="beginner")
    psychotype: Mapped[str] = mapped_column(String(32), default="neutral")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default_factory=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default_factory=utcnow)
