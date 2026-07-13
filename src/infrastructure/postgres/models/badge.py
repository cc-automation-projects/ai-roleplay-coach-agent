"""SQLAlchemy models for Badge and UserBadge aggregates."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from core.utils import utcnow

from .base import Base


class BadgeModel(Base):
    __tablename__ = "badges"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(256))
    description: Mapped[str] = mapped_column(String(500))
    criteria: Mapped[str] = mapped_column(String(1000))
    tenant_id: Mapped[UUID | None] = mapped_column(nullable=True)
    icon_url: Mapped[str] = mapped_column(String(500), default="")
    xp_reward: Mapped[int] = mapped_column(Integer, default=0)
    is_hidden: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default_factory=utcnow)


class UserBadgeModel(Base):
    __tablename__ = "user_badges"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    user_id: Mapped[UUID]
    badge_id: Mapped[UUID]
    awarded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default_factory=utcnow)
