"""SQLAlchemy model for the User aggregate."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from core.utils import utcnow

from .base import Base


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(256), nullable=False, server_default="")
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(256))
    tenant_id: Mapped[UUID | None] = mapped_column(nullable=True)
    role: Mapped[str] = mapped_column(String(32), default="operator")
    xp_total: Mapped[int] = mapped_column(Integer, default=0)
    level: Mapped[int] = mapped_column(Integer, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default_factory=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default_factory=utcnow)
