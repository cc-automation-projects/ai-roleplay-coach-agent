"""Token store protocol for refresh token persistence."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol
from uuid import UUID


class TokenStore(Protocol):
    """Persistent store for refresh tokens.

    Implementations must support ``store``, ``validate``, ``revoke``,
    and ``revoke_all_for_user``.
    """

    async def store(self, user_id: UUID, token: str, expires_at: datetime) -> None:
        """Persist a refresh token with an expiry timestamp."""
        ...

    async def validate(self, token: str) -> UUID | None:
        """Return the user_id associated with *token*, or ``None``."""
        ...

    async def revoke(self, token: str) -> None:
        """Revoke a single refresh token."""
        ...

    async def revoke_all_for_user(self, user_id: UUID) -> None:
        """Revoke every refresh token belonging to *user_id*."""
        ...
