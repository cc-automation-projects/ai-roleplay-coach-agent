"""Tests for LLMCoachAdapter вЂ” CircuitBreaker-protected LLM evaluation."""

from __future__ import annotations

import logging
from uuid import uuid4

import pytest

from agents.coach.adapter import _CIRCUIT_NAME, LLMCoachAdapter
from agents.coach.agent import CoachAgent
from agents.coach.llm_agent import LLMCoachAgent
from core.entities import DifficultyLevel, Evaluation, Psychotype, Scenario, Session, SessionStatus
from core.services.circuit_breaker import CircuitBreakerRegistry


class _MockLLM:
    """Helper: LLMProvider stub that returns valid JSON or raises."""

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


@pytest.fixture
def scenario() -> Scenario:
    return Scenario(
        name="Billing",
        description="Billing issue scenario",
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
    s.append_transcript_entry("operator", "Of course, tell me more")
    return s


@pytest.fixture
def cb_registry() -> CircuitBreakerRegistry:
    return CircuitBreakerRegistry()


class TestLLMCoachAdapter:
    """LLMCoachAdapter: CircuitBreaker protection + fallback."""

    async def test_llm_success(
        self, scenario: Scenario, session: Session, cb_registry: CircuitBreakerRegistry,
    ) -> None:
        """LLM returns valid result в†’ adapter returns LLM Evaluation."""
        llm = _MockLLM(_VALID_JSON)
        llm_agent = LLMCoachAgent(llm=llm, rule_based=CoachAgent())
        adapter = LLMCoachAdapter(llm_agent, CoachAgent(), cb_registry)

        result = await adapter.evaluate_session(session, scenario)

        assert isinstance(result, Evaluation)
        assert result.overall_score == 85.0  # from LLM JSON
        assert result.tone_score == 90.0

    async def test_llm_exception_fallback(
        self, scenario: Scenario, session: Session, cb_registry: CircuitBreakerRegistry,
    ) -> None:
        """LLM throws в†’ fallback to rule-based (always returns Evaluation)."""
        llm = _MockLLM(raises=RuntimeError)
        llm_agent = LLMCoachAgent(llm=llm, rule_based=CoachAgent())
        adapter = LLMCoachAdapter(llm_agent, CoachAgent(), cb_registry)

        result = await adapter.evaluate_session(session, scenario)

        assert isinstance(result, Evaluation)
        assert result.overall_score >= 0

    async def test_circuit_breaker_opens_after_errors(
        self, scenario: Scenario, session: Session,
    ) -> None:
        """After consecutive failures, CircuitBreaker opens."""
        cb_registry = CircuitBreakerRegistry()
        failing_llm = _MockLLM(raises=RuntimeError)
        llm_agent = LLMCoachAgent(llm=failing_llm, rule_based=CoachAgent())
        adapter = LLMCoachAdapter(llm_agent, CoachAgent(), cb_registry)

        # 3 failures should open the circuit
        for _ in range(3):
            result = await adapter.evaluate_session(session, scenario)
            assert isinstance(result, Evaluation)

        # CircuitBreaker should now be OPEN
        cb = cb_registry.get(_CIRCUIT_NAME, threshold=3, recovery_timeout=30.0)
        assert cb.state.value == "open"

    async def test_circuit_breaker_open_still_returns_evaluation(
        self, scenario: Scenario, session: Session,
    ) -> None:
        """Even when CircuitBreaker is OPEN в†’ adapter returns Evaluation (fallback)."""
        cb_registry = CircuitBreakerRegistry()
        failing_llm = _MockLLM(raises=RuntimeError)
        llm_agent = LLMCoachAgent(llm=failing_llm, rule_based=CoachAgent())
        adapter = LLMCoachAdapter(llm_agent, CoachAgent(), cb_registry)

        # Open the circuit
        for _ in range(3):
            await adapter.evaluate_session(session, scenario)

        # Now circuit is OPEN вЂ” should still get Evaluation via fallback
        result = await adapter.evaluate_session(session, scenario)

        assert isinstance(result, Evaluation)
        assert result.overall_score >= 0

    async def test_always_returns_evaluation(
        self, scenario: Scenario, session: Session, cb_registry: CircuitBreakerRegistry,
    ) -> None:
        """Adapter never throws вЂ” always returns Evaluation."""
        llm = _MockLLM(raises=RuntimeError)
        llm_agent = LLMCoachAgent(llm=llm, rule_based=CoachAgent())
        adapter = LLMCoachAdapter(llm_agent, CoachAgent(), cb_registry)

        for _ in range(10):
            result = await adapter.evaluate_session(session, scenario)
            assert isinstance(result, Evaluation)

    async def test_fallback_logging(
        self, scenario: Scenario, session: Session, caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Fallback to rule-based logs a warning."""
        llm = _MockLLM(raises=RuntimeError)
        llm_agent = LLMCoachAgent(llm=llm, rule_based=CoachAgent())
        adapter = LLMCoachAdapter(llm_agent, CoachAgent(), CircuitBreakerRegistry())

        with caplog.at_level(logging.WARNING):
            result = await adapter.evaluate_session(session, scenario)

        assert isinstance(result, Evaluation)
        assert any("fallback" in msg.lower() for msg in caplog.messages)


class TestCoachProvider:

    async def test_mock_provider_returns_coach_agent(self) -> None:
        from api.dependencies import get_coach
        coach = get_coach()
        from agents.coach.agent import CoachAgent as CA
        assert isinstance(coach, CA)

