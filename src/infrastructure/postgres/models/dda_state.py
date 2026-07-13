"""SQLAlchemy model for DDA state persistence."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.utils import utcnow
from infrastructure.postgres.models.base import Base


class DDAStateModel(Base):
    """ORM model for per-session DDA state."""

    __tablename__ = "dda_states"

    session_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        comment="FK to sessions table",
    )
    dda_level: Mapped[int] = mapped_column(Integer, default=0)
    operator_success_streak: Mapped[int] = mapped_column(Integer, default=0)
    last_operator_messages: Mapped[list[str]] = mapped_column(
        ARRAY(Text),
        default_factory=list,
    )
    repetition_count: Mapped[int] = mapped_column(Integer, default=0)
    dialogue_stage: Mapped[str] = mapped_column(
        String(64), default="greeting"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default_factory=utcnow,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default_factory=utcnow,
    )

    def __repr__(self) -> str:
        return (
            f"<DDAStateModel session={self.session_id!s:.8} "
            f"level={self.dda_level}>"
        )
