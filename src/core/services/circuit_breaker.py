"""CircuitBreaker — prevents cascading failures for external calls.

States:
    CLOSED  — normal operation, calls pass through.
    OPEN    — failure threshold exceeded, calls are rejected fast.
    HALF_OPEN — probe period: one trial call is allowed.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Awaitable, Callable
from enum import StrEnum, auto
from typing import Any, TypeVar

from core.exceptions import CircuitBreakerOpenError

logger = logging.getLogger(__name__)

T = TypeVar("T")

_CircuitFunc = Callable[..., Awaitable[T]]


class CircuitState(StrEnum):
    """Circuit breaker state."""

    CLOSED = auto()
    OPEN = auto()
    HALF_OPEN = auto()


class CircuitBreaker:
    """Async circuit breaker with configurable thresholds.

    Usage::

        cb = CircuitBreaker(name="qdrant", threshold=5, recovery_timeout=30.0)
        result = await cb.call(rag_service.index_script, script_id, text)
    """

    def __init__(
        self,
        name: str,
        *,
        threshold: int = 5,
        recovery_timeout: float = 30.0,
        half_open_max_calls: int = 1,
    ) -> None:
        """
        Args:
            name: Human-readable name for logging.
            threshold: Consecutive failures before opening the circuit.
            recovery_timeout: Seconds to wait before moving to HALF_OPEN.
            half_open_max_calls: Max probe calls in HALF_OPEN state.
        """
        self._name = name
        self._threshold = threshold
        self._recovery_timeout = recovery_timeout
        self._half_open_max_calls = half_open_max_calls

        self._state: CircuitState = CircuitState.CLOSED
        self._failure_count: int = 0
        self._last_failure_time: float = 0.0
        self._half_open_calls: int = 0
        self._lock: asyncio.Lock = asyncio.Lock()

    # ── Properties ──────────────────────────────────────────────────────

    @property
    def name(self) -> str:
        """Return the circuit breaker name."""
        return self._name

    @property
    def state(self) -> CircuitState:
        """Return current circuit state (CLOSED / OPEN / HALF_OPEN)."""
        return self._state

    @property
    def failure_count(self) -> int:
        """Return consecutive failure count."""
        return self._failure_count

    @property
    def is_open(self) -> bool:
        """Return True if calls are being rejected."""
        return self._state == CircuitState.OPEN

    # ── Public API ──────────────────────────────────────────────────────

    async def call(self, func: _CircuitFunc, *args: Any, **kwargs: Any) -> T:
        """Execute an async call through the circuit breaker.

        Raises:
            CircuitBreakerOpenError: When the circuit is OPEN and not
                yet ready for a probe.
        """
        async with self._lock:
            self._evaluate_state()

            if self._state == CircuitState.OPEN:
                raise CircuitBreakerOpenError(
                    circuit_name=self._name,
                    failure_count=self._failure_count,
                    retry_after=self._remaining_cooldown(),
                )

            if self._state == CircuitState.HALF_OPEN:
                if self._half_open_calls >= self._half_open_max_calls:
                    raise CircuitBreakerOpenError(
                        circuit_name=self._name,
                        failure_count=self._failure_count,
                        retry_after=self._remaining_cooldown(),
                        message=f"Half-open probe limit ({self._half_open_max_calls}) reached",
                    )
                self._half_open_calls += 1

        # Execute the actual call outside the lock to avoid holding it
        # during I/O — we only need the lock for state transitions.
        try:
            result = await func(*args, **kwargs)
        except Exception as exc:
            async with self._lock:
                self._on_failure()
            logger.warning(
                "CircuitBreaker[%s] call failed (%s): %s",
                self._name,
                type(exc).__name__,
                exc,
            )
            raise

        async with self._lock:
            self._on_success()
        return result

    async def reset(self) -> None:
        """Manually reset the circuit to CLOSED."""
        async with self._lock:
            self._reset_unsafe()
        logger.info("CircuitBreaker[%s] manually reset to CLOSED", self._name)

    # ── Internal helpers (caller MUST hold self._lock) ──────────────────

    def _evaluate_state(self) -> None:
        """Transition OPEN → HALF_OPEN when recovery timeout elapses."""
        if self._state != CircuitState.OPEN:
            return
        elapsed = time.monotonic() - self._last_failure_time
        if elapsed >= self._recovery_timeout:
            logger.info(
                "Circuit Breaker[%s] OPEN → HALF_OPEN "
                "(cooldown of %.1fs elapsed)",
                self._name,
                elapsed,
            )
            self._state = CircuitState.HALF_OPEN
            self._half_open_calls = 0

    def _on_success(self) -> None:
        """Handle a successful call (caller must hold lock)."""
        if self._state == CircuitState.HALF_OPEN:
            logger.info(
                "CircuitBreaker[%s] HALF_OPEN → CLOSED (probe succeeded)",
                self._name,
            )
            self._reset_unsafe()
        else:
            # CLOSED: reset failure count on success
            self._failure_count = 0

    def _on_failure(self) -> None:
        """Handle a failed call (caller must hold lock)."""
        self._failure_count += 1
        self._last_failure_time = time.monotonic()

        if self._failure_count >= self._threshold:
            logger.warning(
                "CircuitBreaker[%s] %s → OPEN "
                "(failure_count=%d threshold=%d)",
                self._name,
                self._state.value,
                self._failure_count,
                self._threshold,
            )
            self._state = CircuitState.OPEN

    def _reset_unsafe(self) -> None:
        """Reset circuit state without locking (caller must hold lock)."""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._half_open_calls = 0
        self._last_failure_time = 0.0

    def _remaining_cooldown(self) -> float:
        """Return seconds remaining before HALF_OPEN transition."""
        if self._last_failure_time == 0:
            return 0.0
        elapsed = time.monotonic() - self._last_failure_time
        remaining = self._recovery_timeout - elapsed
        return max(remaining, 0.0)


class CircuitBreakerRegistry:
    """Thread-safe registry of named circuit breakers.

    Provides a single place to access all circuit breakers used
    across the application.
    """

    def __init__(self) -> None:
        self._breakers: dict[str, CircuitBreaker] = {}

    def get(
        self,
        name: str,
        *,
        threshold: int = 5,
        recovery_timeout: float = 30.0,
    ) -> CircuitBreaker:
        """Return an existing circuit breaker or create a new one."""
        if name not in self._breakers:
            self._breakers[name] = CircuitBreaker(
                name=name,
                threshold=threshold,
                recovery_timeout=recovery_timeout,
            )
        return self._breakers[name]

    def all_states(self) -> dict[str, str]:
        """Return a snapshot of all breaker states for monitoring."""
        return {
            name: breaker.state.value
            for name, breaker in self._breakers.items()
        }

    async def reset_all(self) -> None:
        """Reset every registered circuit breaker."""
        for breaker in self._breakers.values():
            await breaker.reset()
