"""Badge entity — gamification achievements."""

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from core.utils import SanitizedStr, utcnow


class Badge(BaseModel):
    """A gamification badge that operators can earn."""

    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID | None = None
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    icon_url: str = ""
    criteria: str = Field(min_length=1)  # JSON or rule string describing how to earn this badge
    xp_reward: int = Field(default=0, ge=0)
    is_hidden: bool = False
    created_at: datetime = Field(default_factory=utcnow)


class BadgeCreate(BaseModel):
    """DTO for creating a new badge."""

    name: SanitizedStr = Field(min_length=1)
    description: SanitizedStr = Field(min_length=1)
    icon_url: SanitizedStr = ""
    criteria: SanitizedStr = Field(min_length=1)
    xp_reward: int = Field(default=0, ge=0)
    is_hidden: bool = False
    tenant_id: UUID | None = None


class UserBadge(BaseModel):
    """Awarded badge linking a user to a badge."""

    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    badge_id: UUID
    awarded_at: datetime = Field(default_factory=utcnow)
