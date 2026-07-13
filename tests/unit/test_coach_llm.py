"""Tests for LLMCoachAgent — LLM-powered evaluation with fallback."""

from __future__ import annotations

from uuid import uuid4

import pytest

from agents.coach.agent import CoachAgent
from agents.coach.llm_agent import (
    _MAX_TRANSCRIPT_TOKENS,
    LLMCoachAgent,
    _build_user_prompt,
    _clamp,
    _parse_json_response,
)
from core.entities import DifficultyLevel, Evaluation, Psychotype, Scenario, Session, SessionStatus

# ── Helpers ────────────────────────────────────────────────────────────


class _MockLLM:
    """Helper: LLMProvider stub that returns a canned response or raises."""

    def __init__(self, response: str = "", *, raises: type[Exception] | None = None) -> None:
        self._response = response
        self._raises = raises

    async def generate(self, messages, temperature=0.7, max_tokens=1024, stop=None) -> str:
        if self._raises:
            msg = "LLM error"
            raise self._raises(msg)
        return self._response


_VALID_JSON = """{
  "script_adherence": 75.0,
  "tone_score": 82.0,
  "empathy_score": 68.0,
  "objection_handling": 90.0,
  "completeness_score": 85.0,
  "overall_score": 80.0,
  "praise_text": "Good use of the script",
  "growth_text": "Work on empathy",
  "closing_text": "Keep practising",
  "gaming_detected": false
}"""


def _make_session() -> Session:
    session = Session(
        id=uuid4(),
        user_id=uuid4(),
        scenario_id=uuid4(),
        status=SessionStatus.COMPLETED,
    )
    session.append_transcript_entry("operator", "Hello, how can I help you?")
    session.append_transcript_entry("client", "I have a billing problem")
    session.append_transcript_entry("operator", "I understand, let me check")
    return session


@pytest.fixture
def scenario() -> Scenario:
    return Scenario(
        name="Billing issue",
        description="Customer with billing dispute",
        script_ref="s-002",
        script_text="Greet the customer. Identify the issue. Empathize. Offer a solution.",
        psychotype=Psychotype.AGGRESSIVE,
        difficulty=DifficultyLevel.INTERMEDIATE,
    )


# ── _parse_json_response ───────────────────────────────────────────────


class TestParseJsonResponse:
    def test_valid_json(self) -> None:
        result = _parse_json_response('{"score": 80}')
        assert result == {"score": 80}

    def test_markdown_code_block(self) -> None:
        raw = '```json\n{"score": 90}\n```'
        result = _parse_json_response(raw)
        assert result == {"score": 90}

    def test_markdown_no_lang(self) -> None:
        raw = '```\n{"score": 70}\n```'
        result = _parse_json_response(raw)
        assert result == {"score": 70}

    def test_invalid_json(self) -> None:
        result = _parse_json_response("not json at all")
        assert result is None

    def test_non_dict_json(self) -> None:
        result = _parse_json_response("[1, 2, 3]")
        assert result is None

    def test_empty_string(self) -> None:
        result = _parse_json_response("")
        assert result is None


# ── _clamp ─────────────────────────────────────────────────────────────


class TestClamp:
    def test_within_range(self) -> None:
        assert _clamp(50.0) == 50.0

    def test_below_min(self) -> None:
        assert _clamp(-10.0) == 0.0

    def test_above_max(self) -> None:
        assert _clamp(150.0) == 100.0

    def test_edge_min(self) -> None:
        assert _clamp(0.0) == 0.0

    def test_edge_max(self) -> None:
        assert _clamp(100.0) == 100.0


# ── Module-level fixtures ──────────────────────────────────────────────


@pytest.fixture
def session() -> Session:
    return _make_session()


# ── LLMCoachAgent ──────────────────────────────────────────────────────


class TestLLMCoachAgent:
    """LLMCoachAgent: evaluate_session — LLM path and rule-based fallback."""

    async def test_llm_valid_json(self, scenario: Scenario, session: Session) -> None:
        """LLM returns valid JSON → Evaluation with correct scores."""
        llm = _MockLLM(_VALID_JSON)
        rule = CoachAgent()
        agent = LLMCoachAgent(llm=llm, rule_based=rule)

        eval_result = await agent.evaluate_session(session, scenario)

        assert isinstance(eval_result, Evaluation)
        assert eval_result.overall_score == 80.0
        assert eval_result.script_adherence == 75.0
        assert eval_result.tone_score == 82.0
        assert eval_result.empathy_score == 68.0
        assert eval_result.objection_handling == 90.0
        assert eval_result.completeness_score == 85.0
        assert eval_result.praise_text == "Good use of the script"
        assert eval_result.gaming_detected is False

    async def test_llm_invalid_json_fallback(self, scenario: Scenario, session: Session) -> None:
        """LLM returns invalid JSON → falls back to rule-based CoachAgent."""
        llm = _MockLLM("not valid json")
        rule = CoachAgent()
        agent = LLMCoachAgent(llm=llm, rule_based=rule)

        eval_result = await agent.evaluate_session(session, scenario)

        assert isinstance(eval_result, Evaluation)
        # Rule-based produces some scores; check it's a real Evaluation
        assert eval_result.overall_score >= 0
        assert eval_result.overall_score <= 100

    async def test_llm_exception_propagates(self, scenario: Scenario, session: Session) -> None:
        """LLM throws exception → propagates (adapter handles fallback)."""
        llm = _MockLLM(raises=RuntimeError)
        rule = CoachAgent()
        agent = LLMCoachAgent(llm=llm, rule_based=rule)

        with pytest.raises(RuntimeError, match="LLM error"):
            await agent.evaluate_session(session, scenario)

    async def test_markdown_wrapped_json(self, scenario: Scenario, session: Session) -> None:
        """LLM returns markdown-wrapped JSON → parses correctly."""
        wrapped = "```json\n" + _VALID_JSON + "\n```"
        llm = _MockLLM(wrapped)
        rule = CoachAgent()
        agent = LLMCoachAgent(llm=llm, rule_based=rule)

        eval_result = await agent.evaluate_session(session, scenario)

        assert eval_result.overall_score == 80.0
        assert eval_result.script_adherence == 75.0

    async def test_missing_fields_default(self, scenario: Scenario, session: Session) -> None:
        """JSON with missing fields → defaults applied."""
        partial = """{"overall_score": 70, "tone_score": 60}"""
        llm = _MockLLM(partial)
        rule = CoachAgent()
        agent = LLMCoachAgent(llm=llm, rule_based=rule)

        eval_result = await agent.evaluate_session(session, scenario)

        assert eval_result.overall_score == 70.0
        assert eval_result.tone_score == 60.0
        # Missing fields get defaults
        assert eval_result.empathy_score >= 0
        assert eval_result.gaming_detected is False

    async def test_score_clamping(self, scenario: Scenario, session: Session) -> None:
        """Scores outside 0-100 are clamped."""
        out_of_range = """{
            "script_adherence": -10,
            "tone_score": 150,
            "empathy_score": 50,
            "objection_handling": 50,
            "completeness_score": 50,
            "overall_score": 200
        }"""
        llm = _MockLLM(out_of_range)
        rule = CoachAgent()
        agent = LLMCoachAgent(llm=llm, rule_based=rule)

        eval_result = await agent.evaluate_session(session, scenario)

        assert eval_result.script_adherence == 0.0
        assert eval_result.tone_score == 100.0
        assert eval_result.overall_score == 100.0

    async def test_gaming_detected_flag(self, scenario: Scenario, session: Session) -> None:
        """gaming_detected=true in JSON → Evaluation.gaming_detected=True."""
        gaming = """{
            "script_adherence": 50, "tone_score": 50, "empathy_score": 50,
            "objection_handling": 50, "completeness_score": 50,
            "overall_score": 50, "praise_text": "", "growth_text": "",
            "closing_text": "", "gaming_detected": true
        }"""
        llm = _MockLLM(gaming)
        rule = CoachAgent()
        agent = LLMCoachAgent(llm=llm, rule_based=rule)

        eval_result = await agent.evaluate_session(session, scenario)

        assert eval_result.gaming_detected is True

    async def test_empty_session_fallback(self, scenario: Scenario) -> None:
        """Empty transcript → LLM returns something, but no crash."""
        session = Session(
            id=uuid4(), user_id=uuid4(), scenario_id=scenario.id,
            status=SessionStatus.COMPLETED,
        )
        llm = _MockLLM(_VALID_JSON)
        rule = CoachAgent()
        agent = LLMCoachAgent(llm=llm, rule_based=rule)

        eval_result = await agent.evaluate_session(session, scenario)

        assert isinstance(eval_result, Evaluation)

    async def test_fallback_inherits_user_id(self, scenario: Scenario, session: Session) -> None:
        """Fallback path preserves session.user_id in Evaluation."""
        llm = _MockLLM("bad json")
        rule = CoachAgent()
        agent = LLMCoachAgent(llm=llm, rule_based=rule)

        eval_result = await agent.evaluate_session(session, scenario)

        assert eval_result.user_id == session.user_id
        assert eval_result.session_id == session.id


# ── _build_user_prompt tests ──────────────────────────────────────────


class TestBuildUserPrompt:
    """Tests for _build_user_prompt truncation logic."""

    def test_short_transcript_no_truncation(self, scenario: Scenario, session: Session) -> None:
        """Transcript under limit is not truncated."""
        result = _build_user_prompt(scenario, session)
        assert "Script text:" in result
        assert "operator:" in result
        assert "... (truncated) ..." not in result

    def test_long_transcript_truncates(self, scenario: Scenario, session: Session) -> None:
        """Transcript exceeding limit is truncated."""
        # Build a session with a very long transcript
        long_text = "A" * (_MAX_TRANSCRIPT_TOKENS * 4 + 1000)
        from core.entities.session import TranscriptEntry

        long_session = Session(
            id=session.id,
            user_id=session.user_id,
            scenario_id=session.scenario_id,
            status=session.status,
            transcript=[
                TranscriptEntry(speaker="operator", text=long_text),
            ],
        )
        result = _build_user_prompt(scenario, long_session)
        assert "... (truncated) ..." in result
        # Should not exceed ~12000 chars
        assert len(result) <= _MAX_TRANSCRIPT_TOKENS * 4 + 200  # small overhead for prefix

    def test_truncation_keeps_scenario_header(self, scenario: Scenario, session: Session) -> None:
        """After truncation, scenario header (first line) is preserved."""
        long_text = "B" * (_MAX_TRANSCRIPT_TOKENS * 4 + 1000)
        from core.entities.session import TranscriptEntry

        long_session = Session(
            id=session.id,
            user_id=session.user_id,
            scenario_id=session.scenario_id,
            status=session.status,
            transcript=[
                TranscriptEntry(speaker="operator", text=long_text),
            ],
        )
        result = _build_user_prompt(scenario, long_session)
        # First line should still be the scenario name
        assert result.startswith(f"Scenario: {scenario.name}")
