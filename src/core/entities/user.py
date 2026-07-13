"""User entity — contact center operator."""

from datetime import datetime
from enum import StrEnum, auto
from uuid import UUID, uuid4

from pydantic import BaseModel, EmailStr, Field

from core.utils import SanitizedStr, utcnow


class UserRole(StrEnum):
    """Role in the coaching system."""

    OPERATOR = auto()
    TRAINER = auto()
    ADMIN = auto()


_AGE_GROUPS = {"18-25", "26-35", "36-45", "46-55", "55+"}


class User(BaseModel):
    """Contact center operator participating in simulations."""

    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID | None = None
    username: str = Field(
        min_length=3, max_length=32,
        pattern=r"^[a-zA-Z0-9_]+$",
        description="Unique login name",
    )
    hashed_password: str = Field(
        min_length=0,
        description="Bcrypt hash of the password — never store plaintext",
    )
    email: EmailStr = Field(description="PII-sensitive: operator email address")
    name: SanitizedStr = Field(min_length=1)
    role: UserRole = UserRole.OPERATOR
    xp_total: int = Field(default=0, ge=0)
    level: int = Field(default=1, ge=1)
    is_active: bool = True
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    # ── Fairness / protected attributes (all optional) ──────────────────
    gender: str | None = Field(default=None, description="male, female, other")
    age_group: str | None = Field(
        default=None,
        pattern=f"^({'|'.join(_AGE_GROUPS)})$",
        description=f"One of {sorted(_AGE_GROUPS)}",
    )
    accent: str | None = Field(default=None, description="native, region1, region2, ...")
    native_language: str | None = Field(default=None, description="ru, en, ...")

    _XP_PER_LEVEL = 1000

    def add_xp(self, amount: int) -> None:
        """Add XP and recalculate level."""
        if amount < 0:
            msg = "XP amount must be non-negative"
            raise ValueError(msg)
        self.xp_total += amount
        self.level = (self.xp_total // self._XP_PER_LEVEL) + 1
        self.updated_at = utcnow()


class UserCreate(BaseModel):
    """DTO for creating a new user."""

    username: str = Field(
        min_length=3, max_length=32,
        pattern=r"^[a-zA-Z0-9_]+$",
    )
    hashed_password: str = Field(min_length=0)
    email: EmailStr
    name: SanitizedStr = Field(min_length=1)
    role: UserRole = UserRole.OPERATOR
    tenant_id: UUID | None = None
    gender: str | None = None
    age_group: str | None = None
    accent: str | None = None
    native_language: str | None = None


class UserUpdate(BaseModel):
    """DTO for updating user fields. All fields optional."""

    name: SanitizedStr | None = None
    role: UserRole | None = None
    is_active: bool | None = None
    tenant_id: UUID | None = None
    gender: str | None = None
    age_group: str | None = None
    accent: str | None = None
    native_language: str | None = None
