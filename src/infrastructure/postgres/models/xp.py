"""SQLAlchemy models for XPTransaction and Metric aggregates."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from core.utils import utcnow

from .base import Base


class XPTransactionModel(Base):
    __tablename__ = "xp_transactions"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    user_id: Mapped[UUID]
    amount: Mapped[int] = mapped_column(Integer)
    reason: Mapped[str] = mapped_column(String(64))
    reference_id: Mapped[UUID | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default_factory=utcnow)


class MetricModel(Base):
    __tablename__ = "metrics"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    user_id: Mapped[UUID]
    metric_type: Mapped[str] = mapped_column(String(64))
    value: Mapped[float] = mapped_column(Float)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default_factory=utcnow)
