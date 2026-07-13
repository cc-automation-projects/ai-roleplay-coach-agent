"""JWT-based authentication service — register, login, refresh, token validation."""

from __future__ import annotations

import logging
import re
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING
from uuid import UUID

import bcrypt as _bcrypt
from jose import JWTError, jwt
from pydantic import BaseModel

from core.config import settings
from core.entities.user import User, UserCreate
from core.exceptions import AuthorizationError

if TYPE_CHECKING:
    from core.interfaces.repositories import UserRepository
    from core.interfaces.token_store import TokenStore

logger = logging.getLogger(__name__)


# ── Models ─────────────────────────────────────────────────────────────


class TokenPair(BaseModel):
    """Access + refresh token pair returned on login/register."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"  # noqa: S105


class TokenPayload(BaseModel):
    """Decoded access token payload."""

    sub: str  # user_id
    username: str
    role: str


# ── Helpers ─────────────────────────────────────────────────────────────


def _hash_password(password: str) -> str:
    """Hash a plaintext password with bcrypt."""
    return _bcrypt.hashpw(password.encode("utf-8"), _bcrypt.gensalt()).decode("utf-8")


def _verify_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    return _bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def _create_access_token(user: User) -> str:
    """Create a short-lived JWT access token."""
    expire = timedelta(minutes=settings.JWT_ACCESS_EXPIRE_MINUTES)
    payload = {
        "sub": str(user.id),
        "username": user.username,
        "role": user.role.value,
        "exp": datetime.now(UTC) + expire,
    }
    return jwt.encode(payload, settings.JWT_SIGNING_KEY, algorithm=settings.JWT_ALGORITHM)


def _create_refresh_token(user: User, expires_at: datetime) -> str:
    """Create a longer-lived JWT refresh token."""
    payload = {
        "sub": str(user.id),
        "username": user.username,
        "exp": expires_at,
    }
    return jwt.encode(payload, settings.JWT_SIGNING_KEY, algorithm=settings.JWT_ALGORITHM)


def _decode_token(token: str) -> dict:
    """Decode and validate a JWT token. Raises AuthorizationError on failure."""
    try:
        return jwt.decode(token, settings.JWT_SIGNING_KEY, algorithms=[settings.JWT_ALGORITHM])
    except JWTError as exc:
        msg = f"Invalid or expired token: {exc}"
        raise AuthorizationError(msg) from exc


def _validate_username(username: str) -> None:
    """Validate username format."""
    if not re.match(r"^[a-zA-Z0-9_]{3,32}$", username):
        msg = "Username must be 3-32 characters, only letters, digits and underscores"
        raise ValueError(
            msg
        )


_COMMON_PASSWORDS: frozenset[str] = frozenset({
    "password", "12345678", "123456789", "1234567890", "qwerty123",
    "password1", "abcdefgh", "11111111", "iloveyou", "trustno1",
    "monkey", "dragon", "master", "shadow", "sunshine",
    "princess", "football", "baseball", "welcome", "admin123",
    "letmein", "passw0rd", "login", "starwars", "pass1234",
})


def _validate_password(password: str) -> None:
    """Validate password strength."""
    if len(password) < 8:
        msg = "Password must be at least 8 characters long"
        raise ValueError(msg)
    if password.lower() in _COMMON_PASSWORDS:
        msg = "Password is too common — choose a more unique password"
        raise ValueError(msg)
    if not re.search(r"[A-Z]", password):
        msg = "Password must contain at least one uppercase letter"
        raise ValueError(msg)
    if not re.search(r"[a-z]", password):
        msg = "Password must contain at least one lowercase letter"
        raise ValueError(msg)
    if not re.search(r"[0-9]", password):
        msg = "Password must contain at least one digit"
        raise ValueError(msg)


# ── AuthService ────────────────────────────────────────────────────────


class AuthService:
    """Authentication service: register, login, token refresh, user resolution."""

    def __init__(self, user_repo: UserRepository, token_store: TokenStore | None = None) -> None:
        self._user_repo = user_repo
        self._token_store = token_store

    # ── Public API ────────────────────────────────────────────────────

    async def register(self, username: str, password: str) -> dict:
        """Register a new user. Returns TokenPair + user info."""
        _validate_username(username)
        _validate_password(password)

        hashed = _hash_password(password)
        data = UserCreate(
            username=username,
            hashed_password=hashed,
            email=f"{username}@example.com",  # placeholder; full registration requires email
            name=username,
        )
        user = await self._user_repo.create(data)
        result = await self._build_and_store_tokens(user)
        return {
            "user_id": str(user.id),
            "username": user.username,
            "role": user.role.value,
            **result.model_dump(),
        }

    async def login(self, username: str, password: str) -> TokenPair:
        """Authenticate a user and return token pair."""
        user = await self._user_repo.get_by_username(username)
        if user is None:
            msg = "Invalid username or password"
            raise AuthorizationError(msg)

        if not _verify_password(password, user.hashed_password):
            msg = "Invalid username or password"
            raise AuthorizationError(msg)

        if not user.is_active:
            msg = "Account is inactive"
            raise AuthorizationError(msg)

        return await self._build_and_store_tokens(user)

    async def refresh_token(self, refresh_token: str) -> TokenPair:
        """Exchange a valid refresh token for a new token pair (rotation)."""
        store = self._require_store()
        user_id = await store.validate(refresh_token)
        if user_id is None:
            msg = "Invalid or revoked refresh token"
            raise AuthorizationError(msg)

        # Revoke old token first (rotation — prevent replay)
        await store.revoke(refresh_token)

        # Verify JWT itself is still valid
        _decode_token(refresh_token)
        user = await self._user_repo.get_by_id(user_id)
        if user is None:
            msg = "User not found"
            raise AuthorizationError(msg)

        return await self._build_and_store_tokens(user)

    async def logout(self, refresh_token: str) -> None:
        """Revoke a refresh token."""
        store = self._require_store()
        await store.revoke(refresh_token)

    async def revoke_all_for_user(self, user_id: UUID) -> None:
        """Revoke every refresh token belonging to a user."""
        store = self._require_store()
        await store.revoke_all_for_user(user_id)

    async def get_current_user(self, token: str) -> User:
        """Decode an access token and return the corresponding user."""
        payload = _decode_token(token)
        user_id = payload.get("sub")
        if user_id is None:
            msg = "Invalid token payload"
            raise AuthorizationError(msg)
        user = await self._user_repo.get_by_id(UUID(user_id))
        if user is None:
            msg = "User not found"
            raise AuthorizationError(msg)
        if not user.is_active:
            msg = "Account is inactive"
            raise AuthorizationError(msg)
        return user

    # ── Internals ─────────────────────────────────────────────────────

    def _require_store(self) -> TokenStore:
        if self._token_store is None:
            msg = "TokenStore not configured"
            raise RuntimeError(msg)
        return self._token_store

    async def _build_and_store_tokens(self, user: User) -> TokenPair:
        """Create access + refresh token pair and persist the refresh token."""
        expires_at = datetime.now(UTC) + timedelta(days=settings.JWT_REFRESH_EXPIRE_DAYS)
        pair = TokenPair(
            access_token=_create_access_token(user),
            refresh_token=_create_refresh_token(user, expires_at),
        )
        if self._token_store is not None:
            await self._token_store.store(user.id, pair.refresh_token, expires_at)
        return pair
