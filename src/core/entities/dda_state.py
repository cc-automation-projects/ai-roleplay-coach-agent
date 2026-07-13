"""DDAState — persisted dynamic difficulty adjustment state per session.

Replaces the in-memory ``SimulatorSessionState`` dataclass in the
SimulatorAgent so that DDA levels survive service restarts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from core.utils import utcnow


@dataclass
class DDAState:
    """Persistent DDA tracking for a single simulation session.

    Core fields
    -----------
    session_id
        FK to ``sessions`` table.
    dda_level
        Current difficulty escalation level (0 = normal).
    operator_success_streak
        Consecutive "good" operator responses — used by the
        Anti-Gaming heuristic.
    last_operator_messages
        Rolling window of recent operator utterances (Anti-Gaming).
    repetition_count
        How many times the operator repeated themselves.
    dialogue_stage
        Current stage of the conversation (greeting,
        objection, …).
    created_at / updated_at
        Timestamps for auditing and stale-state GC.
    """

    session_id: UUID
    dda_level: int = 0
    operator_success_streak: int = 0
    last_operator_messages: list[str] = field(default_factory=list)
    repetition_count: int = 0
    dialogue_stage: str = "greeting"
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)

    # ── Behaviour helpers ───────────────────────────────────────────────

    def push_message(self, message: str, max_window: int = 5) -> None:
        """Append an operator message, keeping a rolling window."""
        self.last_operator_messages.append(message)
        if len(self.last_operator_messages) > max_window:
            self.last_operator_messages.pop(0)
        self.updated_at = utcnow()

    def is_repeating(self, message: str) -> bool:
        """Heuristic: is the operator repeating themselves?"""
        return message.strip().lower() in (
            m.strip().lower() for m in self.last_operator_messages
        )

    def escalate(self, by: int = 1, max_level: int = 10) -> None:
        """Increase DDA level."""
        self.dda_level = min(self.dda_level + by, max_level)
        self.updated_at = utcnow()

    def deescalate(self, by: int = 1) -> None:
        """Decrease DDA level (floor 0)."""
        self.dda_level = max(self.dda_level - by, 0)
        self.updated_at = utcnow()


@dataclass
class DDAStateCreate:
    """DTO for creating a new DDAState record."""

    session_id: UUID
    dialogue_stage: str = "greeting"
