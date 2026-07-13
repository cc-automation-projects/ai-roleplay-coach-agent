"""Integration tests for Coach LLM — CoachAdapter + MockLLMProvider + CircuitBreaker.

Tests component interactions without HTTP:
- LLMCoachAgent parses LLM output correctly
- CoachAdapter falls back to rule-based on LLM failure
- CircuitBreaker opens after N failures and still returns Evaluation
- CircuitBreaker transitions to HALF_OPEN after recovery_timeout
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from agents.coach.adapter import _CIRCUIT_NAME, LLMCoachAdapter
from agents.coach.agent import CoachAgent
from agents.coach.llm_agent import LLMCoachAgent
from core.entities import DifficultyLevel, Evaluation, Psychotype, Scenario, Session, SessionStatus
from core.services.circuit_breaker import CircuitBreakerRegistry

# ── Helpers ──────────────────────────────────────────────────────────────

class _MockLLM:
    """LLMProvider stub that returns JSON or raises."""

    def __init__(self, response: str = "", *, raises: type[Exception] | None = None) -> None:
        self._response = response
        self._raises = raises

    async def generate(self, messages, temperature=0.7, max_tokens=1024, stop=None) -> str:
        if self._raises:
            msg = "LLM error"
            raise self._raises(msg)
        return self._response


_VALID_JSON = """{
  "overall_score": 85, "script_adherence": 80, "tone_score": 90,
  "empathy_score": 75, "objection_handling": 85, "completeness_score": 80,
  "praise_text": "Great work", "growth_text": "Keep improving",
  "closing_text": "Well done", "gaming_detected": false
}"""

_MALFORMED_JSON = """{"overall_score": "not_a_number"}"""


# ── Fixtures ─────────────────────────────────────────────────────────────

@pytest.fixture
def scenario() -> Scenario:
    return Scenario(
        name="Billing",
        description="Billing issue",
        script_ref="s-001",
        script_text="Greet. Identify. Empathize. Solve.",
        psychotype=Psychotype.NEUTRAL,
        difficulty=DifficultyLevel.BEGINNER,
    )


@pytest.fixture
def session() -> Session:
    s = Session(id=uuid4(), user_id=uuid4(), scenario_id=uuid4(), status=SessionStatus.COMPLETED)
    s.append_transcript_entry("operator", "Hello")
    s.append_transcript_entry("client", "Hi, I need help")
    s.append_transcript_entry("operator", "Of course")
    return s


@pytest.fixture
def cb_registry() -> CircuitBreakerRegistry:
    return CircuitBreakerRegistry()


# ── Tests ────────────────────────────────────────────────────────────────


class TestCoachLLMIntegration:
    """CoachAdapter + LLMCoachAgent + CircuitBreaker integration."""

    async def test_llm_valid_json_returns_evaluation(
        self, scenario: Scenario, session: Session, cb_registry: CircuitBreakerRegistry,
    ) -> None:
        """CoachAdapter with valid LLM output returns correctly parsed Evaluation."""
        llm = _MockLLM(_VALID_JSON)
        llm_agent = LLMCoachAgent(llm=llm, rule_based=CoachAgent())
        adapter = LLMCoachAdapter(llm_agent, CoachAgent(), cb_registry)

        result = await adapter.evaluate_session(session, scenario)

        assert isinstance(result, Evaluation)
        assert result.overall_score == 85.0
        assert result.script_adherence == 80.0
        assert result.tone_score == 90.0
        assert result.empathy_score == 75.0
        assert result.objection_handling == 85.0
        assert result.completeness_score == 80.0
        assert result.praise_text == "Great work"
        assert result.gaming_detected is False

    async def test_llm_malformed_json_triggers_fallback(
        self, scenario: Scenario, session: Session, cb_registry: CircuitBreakerRegistry,
    ) -> None:
        """Malformed LLM JSON → LLMCoachAgent falls back to rule-based internally."""
        llm = _MockLLM(_MALFORMED_JSON)
        llm_agent = LLMCoachAgent(llm=llm, rule_based=CoachAgent())
        adapter = LLMCoachAdapter(llm_agent, CoachAgent(), cb_registry)

        result = await adapter.evaluate_session(session, scenario)

        assert isinstance(result, Evaluation)
        # Rule-based fallback: should return non-zero score
        assert result.overall_score > 0

    async def test_llm_exception_fallback_to_rule_based(
        self, scenario: Scenario, session: Session, cb_registry: CircuitBreakerRegistry,
    ) -> None:
        """LLM raises exception → adapter falls back to rule-based."""
        llm = _MockLLM(raises=RuntimeError)
        llm_agent = LLMCoachAgent(llm=llm, rule_based=CoachAgent())
        adapter = LLMCoachAdapter(llm_agent, CoachAgent(), cb_registry)

        result = await adapter.evaluate_session(session, scenario)

        assert isinstance(result, Evaluation)
        assert result.overall_score >= 0

    async def test_circuit_breaker_opens_after_three_failures(
        self, scenario: Scenario, session: Session,
    ) -> None:
        """After 3 consecutive LLM failures, CircuitBreaker transitions to OPEN."""
        cb_registry = CircuitBreakerRegistry()
        failing_llm = _MockLLM(raises=RuntimeError)
        llm_agent = LLMCoachAgent(llm=failing_llm, rule_based=CoachAgent())
        adapter = LLMCoachAdapter(llm_agent, CoachAgent(), cb_registry)

        for _ in range(3):
            result = await adapter.evaluate_session(session, scenario)
            assert isinstance(result, Evaluation)

        cb = cb_registry.get(_CIRCUIT_NAME, threshold=3, recovery_timeout=30.0)
        assert cb.state.value == "open"

    async def test_circuit_breaker_open_still_produces_evaluation_via_fallback(
        self, scenario: Scenario, session: Session,
    ) -> None:
        """Even when CircuitBreaker is OPEN, adapter returns Evaluation via fallback."""
        cb_registry = CircuitBreakerRegistry()
        failing_llm = _MockLLM(raises=RuntimeError)
        llm_agent = LLMCoachAgent(llm=failing_llm, rule_based=CoachAgent())
        adapter = LLMCoachAdapter(llm_agent, CoachAgent(), cb_registry)

        for _ in range(3):
            await adapter.evaluate_session(session, scenario)

        cb = cb_registry.get(_CIRCUIT_NAME, threshold=3, recovery_timeout=30.0)
        assert cb.state.value == "open"

        result = await adapter.evaluate_session(session, scenario)
        assert isinstance(result, Evaluation)
        assert result.overall_score >= 0

    async def test_circuit_breaker_half_open_recovery(
        self, scenario: Scenario, session: Session,
    ) -> None:
        """After recovery_timeout, CB allows a probe and recovers to CLOSED."""
        import asyncio

        cb_registry = CircuitBreakerRegistry()
        # Pre-create circuit with short timeout so the adapter cannot override it
        cb_registry.get(_CIRCUIT_NAME, threshold=3, recovery_timeout=0.05)

        failing_llm = _MockLLM(raises=RuntimeError)
        llm_agent = LLMCoachAgent(llm=failing_llm, rule_based=CoachAgent())
        adapter = LLMCoachAdapter(llm_agent, CoachAgent(), cb_registry)

        # Trip the breaker
        for _ in range(3):
            await adapter.evaluate_session(session, scenario)

        cb = cb_registry.get(_CIRCUIT_NAME)
        assert cb.state.value == "open"

        # Wait for recovery_timeout to expire
        await asyncio.sleep(0.06)

        # The next call triggers _evaluate_state() → HALF_OPEN,
        # probe succeeds → CLOSED (evaluate_state is lazy, only inside call())
        llm = _MockLLM(_VALID_JSON)
        llm_agent2 = LLMCoachAgent(llm=llm, rule_based=CoachAgent())
        adapter2 = LLMCoachAdapter(llm_agent2, CoachAgent(), cb_registry)
        result = await adapter2.evaluate_session(session, scenario)
        assert isinstance(result, Evaluation)
        assert result.overall_score == 85.0  # from LLM, not fallback
        assert cb.state.value == "closed"

    async def test_always_returns_evaluation_no_matter_what(
        self, scenario: Scenario, session: Session, cb_registry: CircuitBreakerRegistry,
    ) -> None:
        """Adapter never throws — always returns an Evaluation regardless of LLM state."""
        llm = _MockLLM(raises=RuntimeError)
        llm_agent = LLMCoachAgent(llm=llm, rule_based=CoachAgent())
        adapter = LLMCoachAdapter(llm_agent, CoachAgent(), cb_registry)

        for _ in range(10):
            result = await adapter.evaluate_session(session, scenario)
            assert isinstance(result, Evaluation)
