"""SQLAlchemy model for the Session aggregate."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from core.utils import utcnow

from .base import Base


class SessionModel(Base):
    __tablename__ = "sessions"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    user_id: Mapped[UUID]
    scenario_id: Mapped[UUID]
    tenant_id: Mapped[UUID | None] = mapped_column(nullable=True, default=None)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    transcript: Mapped[list[dict] | None] = mapped_column(JSONB, default_factory=list)
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    difficulty_at_start: Mapped[str | None] = mapped_column(String(32), nullable=True, default=None)
    psychotype_at_start: Mapped[str | None] = mapped_column(String(32), nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default_factory=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default_factory=utcnow)
