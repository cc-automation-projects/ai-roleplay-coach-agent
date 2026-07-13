"""Full-cycle integration tests with MockLLMProvider and LLMSimulatorAdapter."""

from __future__ import annotations

from uuid import uuid4

from core.entities import DifficultyLevel, Psychotype, Scenario, Session, TranscriptEntry
from infrastructure.llm import MockLLMProvider
from src.agents.simulator_llm import LLMSimulatorAgent
from src.agents.simulator_llm.adapter import _GREETINGS, LLMSimulatorAdapter


class TestIntegrationWithMockProvider:
    """Full cycle: agent -> MockLLMProvider -> response."""

    async def test_full_cycle(
        self, mock_llm: MockLLMProvider, session: Session, script: object
    ) -> None:
        """process_turn -> client replied, transcript updated."""
        agent = LLMSimulatorAgent(llm=mock_llm, script=script)

        reply = await agent.process_turn(session, "Чем могу помочь?")

        assert reply == "Mock response"
        assert len(session.transcript) == 1
        assert session.transcript[0].speaker == "client"

    async def test_generate_response_uses_history(
        self, session: Session, script: object
    ) -> None:
        """generate_response uses transcript history."""
        llm = MockLLMProvider(mode="simple")
        agent = LLMSimulatorAgent(llm=llm, script=script)

        await agent.process_turn(session, "Как дела?")
        await agent.process_turn(session, "Что случилось?")

        reply = await agent.generate_response(session)
        assert reply == "Mock response"


class MockLLMAgent:
    """Minimal mock for LLMSimulatorAgent used by LLMSimulatorAdapter."""

    def __init__(self) -> None:
        self.turns: list[tuple[str, str]] = []

    async def process_turn(self, session: object, operator_msg: str) -> str:
        self.turns.append(("process_turn", operator_msg))
        return f"LLM reply to: {operator_msg[:20]}"


class TestLLMSimulatorAdapter:
    """LLMSimulatorAdapter — rule-based start/should_end, LLM-based generate."""

    # ── start_dialogue ──────────────────────────────────────────────

    async def test_start_dialogue_returns_greeting_and_psychotype(
        self,
    ) -> None:
        """start_dialogue returns non-empty greeting and scenario psychotype."""
        scenario = Scenario(
            name="Test",
            description="A test",
            psychotype=Psychotype.CONFUSED,
            difficulty=DifficultyLevel.BEGINNER,
            script_ref="T-001",
            script_text="Hello.",
        )

        adapter = LLMSimulatorAdapter(llm_agent=MockLLMAgent())
        greeting, psychotype = await adapter.start_dialogue(scenario)

        assert len(greeting) > 0
        assert psychotype == Psychotype.CONFUSED

    async def test_start_dialogue_all_psychotypes_have_greeting(self) -> None:
        """Every Psychotype value has at least one greeting in _GREETINGS."""
        for pt in Psychotype:
            assert pt in _GREETINGS, f"Missing greeting for {pt}"
            assert len(_GREETINGS[pt]) > 0, f"Empty greeting list for {pt}"

    # ── generate_response ───────────────────────────────────────────

    async def test_generate_empty_transcript_returns_ellipsis(self) -> None:
        """Empty transcript → '...' without calling LLM."""
        session = Session(user_id=uuid4(), scenario_id=uuid4())
        adapter = LLMSimulatorAdapter(llm_agent=MockLLMAgent())

        reply = await adapter.generate_response(session)

        assert reply == "..."

    async def test_generate_no_operator_message_returns_ellipsis(self) -> None:
        """Transcript without operator → '...' without calling LLM."""
        session = Session(user_id=uuid4(), scenario_id=uuid4())
        session.transcript = [
            TranscriptEntry(speaker="client", text="Hello?"),
        ]
        adapter = LLMSimulatorAdapter(llm_agent=MockLLMAgent())

        reply = await adapter.generate_response(session)

        assert reply == "..."

    async def test_generate_delegates_to_llm(self) -> None:
        """Last operator message → delegated to llm_agent.process_turn."""
        session = Session(user_id=uuid4(), scenario_id=uuid4())
        session.transcript = [
            TranscriptEntry(speaker="operator", text="How can I help?"),
        ]
        adapter = LLMSimulatorAdapter(llm_agent=MockLLMAgent())

        reply = await adapter.generate_response(session)

        assert "How can I help?" in reply
        assert "LLM reply" in reply

    async def test_generate_picks_last_operator_message(self) -> None:
        """Multiple entries — picks the LAST operator message."""
        session = Session(user_id=uuid4(), scenario_id=uuid4())
        session.transcript = [
            TranscriptEntry(speaker="operator", text="First message"),
            TranscriptEntry(speaker="client", text="Reply"),
            TranscriptEntry(speaker="operator", text="Second message"),
        ]
        adapter = LLMSimulatorAdapter(llm_agent=MockLLMAgent())

        reply = await adapter.generate_response(session)

        assert "Second message" in reply

    # ── should_end ──────────────────────────────────────────────────

    async def test_should_end_empty_transcript_false(self) -> None:
        """Empty transcript → False."""
        session = Session(user_id=uuid4(), scenario_id=uuid4())
        adapter = LLMSimulatorAdapter(llm_agent=MockLLMAgent())

        result = await adapter.should_end(session)

        assert result is False

    async def test_should_end_under_max_turns_false(self) -> None:
        """7 turns (14 entries) → False."""
        session = Session(user_id=uuid4(), scenario_id=uuid4())
        session.transcript = [
            TranscriptEntry(speaker="operator" if i % 2 == 0 else "client", text=f"msg{i}")
            for i in range(14)  # 7 operator + 7 client
        ]
        adapter = LLMSimulatorAdapter(llm_agent=MockLLMAgent())

        result = await adapter.should_end(session)

        assert result is False

    async def test_should_end_at_max_turns_true(self) -> None:
        """8 turns (16 entries) → True."""
        session = Session(user_id=uuid4(), scenario_id=uuid4())
        session.transcript = [
            TranscriptEntry(speaker="operator" if i % 2 == 0 else "client", text=f"msg{i}")
            for i in range(16)  # 8 operator + 8 client
        ]
        adapter = LLMSimulatorAdapter(llm_agent=MockLLMAgent())

        result = await adapter.should_end(session)

        assert result is True

    async def test_should_end_exceeds_max_turns_true(self) -> None:
        """10 turns (20 entries) → True."""
        session = Session(user_id=uuid4(), scenario_id=uuid4())
        session.transcript = [
            TranscriptEntry(speaker="operator" if i % 2 == 0 else "client", text=f"msg{i}")
            for i in range(20)
        ]
        adapter = LLMSimulatorAdapter(llm_agent=MockLLMAgent())

        result = await adapter.should_end(session)

        assert result is True

    # ── reset_session ───────────────────────────────────────────────

    async def test_reset_session_noop(self) -> None:
        """reset_session is a no-op, doesn't raise."""
        adapter = LLMSimulatorAdapter(llm_agent=MockLLMAgent())
        adapter.reset_session("some-id")  # should not raise
