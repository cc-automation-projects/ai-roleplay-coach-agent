"""LLMCoachAdapter — CoachAgent-совместимая обёртка для LLMCoachAgent.

Позволяет подменять rule-based CoachAgent на LLM-оценку
через зависимость get_coach, без изменения кода API и SessionService.

Адаптер пробует LLM-оценку через CircuitBreaker. Если CircuitBreaker
открыт или LLM выбросил исключение — используется rule-based fallback.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from core.exceptions import CircuitBreakerOpenError

if TYPE_CHECKING:
    from agents.coach.agent import CoachAgent
    from agents.coach.llm_agent import LLMCoachAgent
    from core.entities import Evaluation, Scenario, Session
    from core.services.circuit_breaker import CircuitBreakerRegistry

logger = logging.getLogger(__name__)

_CIRCUIT_NAME = "llm-coach"
_CIRCUIT_THRESHOLD = 3
_CIRCUIT_TIMEOUT = 30.0


class LLMCoachAdapter:
    """Adapter: выбирает LLM-оценку или rule-based fallback.

    Usage:
        adapter = LLMCoachAdapter(llm_agent, rule_agent, cb_registry)
        evaluation = await adapter.evaluate_session(session, scenario)
    """

    def __init__(
        self,
        llm_agent: LLMCoachAgent,
        rule_agent: CoachAgent,
        cb_registry: CircuitBreakerRegistry,
    ) -> None:
        self._llm_agent = llm_agent
        self._rule_agent = rule_agent
        self._cb = cb_registry.get(
            _CIRCUIT_NAME,
            threshold=_CIRCUIT_THRESHOLD,
            recovery_timeout=_CIRCUIT_TIMEOUT,
        )

    async def evaluate_session(
        self, session: Session, scenario: Scenario,
    ) -> Evaluation:
        """Evaluate session: try LLM via CircuitBreaker, fallback on failure."""
        try:
            result = await self._cb.call(
                self._llm_agent.evaluate_session,
                session,
                scenario,
            )
        except CircuitBreakerOpenError:
            logger.warning(
                "Coach CircuitBreaker OPEN (session=%s), using rule-based",
                session.id,
            )
            return await self._rule_agent.evaluate_session(session, scenario)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Coach LLM fallback (reason=%s: %s, session=%s)",
                type(exc).__name__, exc, session.id,
            )
            return await self._rule_agent.evaluate_session(session, scenario)

        logger.info(
            "Coach LLM evaluation success (session=%s, state=%s)",
            session.id, self._cb.state.value,
        )
        return result
