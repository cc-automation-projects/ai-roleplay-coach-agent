"""DDAStateService — manage persisted DDA state for simulation sessions.

Replaces the in-memory ``SimulatorSessionState`` management inside
the SimulatorAgent with a persistent repository-backed approach.
"""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import TYPE_CHECKING

from core.entities.dda_state import DDAState, DDAStateCreate
from core.utils import utcnow

if TYPE_CHECKING:
    from uuid import UUID

    from core.interfaces.repositories import DDAStateRepository

logger = logging.getLogger(__name__)

_STALE_TTL_HOURS = 24  # auto-clean sessions older than this


class DDAStateService:
    """High-level service for DDA state lifecycle.

    Provides the same operations that ``SimulatorSessionState``
    previously handled in-memory, but backed by ``DDAStateRepository``
    so state survives restarts.
    """

    def __init__(self, repo: DDAStateRepository) -> None:
        self._repo = repo

    # ── Lifecycle ───────────────────────────────────────────────────────

    async def get_or_create(self, session_id: UUID, **defaults: str) -> DDAState:
        """Return existing DDA state for *session_id* or create one."""
        existing = await self._repo.get_by_session(session_id)
        if existing is not None:
            return existing

        state_create = DDAStateCreate(
            session_id=session_id,
            dialogue_stage=defaults.get("dialogue_stage", "greeting"),
        )
        new_state = await self._repo.create(state_create)
        logger.debug("Created DDA state session=%s", session_id)
        return new_state

    async def save(self, state: DDAState) -> None:
        """Persist updated DDA state."""
        await self._repo.update(state)

    async def delete(self, session_id: UUID) -> None:
        """Remove DDA state for a completed/failed session."""
        await self._repo.delete(session_id)

    # ── DDA operations (delegated to entity methods + persist) ──────────

    async def push_message(
        self, state: DDAState, message: str, max_window: int = 5
    ) -> None:
        """Record an operator message and persist."""
        state.push_message(message, max_window)
        await self._repo.update(state)

    async def escalate(self, state: DDAState, by: int = 1, max_level: int = 10) -> None:
        """Increase DDA level and persist."""
        state.escalate(by, max_level)
        await self._repo.update(state)

    async def deescalate(self, state: DDAState, by: int = 1) -> None:
        """Decrease DDA level and persist."""
        state.deescalate(by)
        await self._repo.update(state)

    # ── GC ──────────────────────────────────────────────────────────────

    async def clean_stale(self, ttl_hours: int = _STALE_TTL_HOURS) -> int:
        """Delete DDA states older than *ttl_hours*.

        Returns number of deleted records.
        """
        cutoff = utcnow() - timedelta(hours=ttl_hours)
        deleted = await self._repo.delete_stale(cutoff)
        if deleted:
            logger.info("Cleaned %d stale DDA states (TTL=%dh)", deleted, ttl_hours)
        return deleted
