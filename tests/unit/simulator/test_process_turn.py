"""Tests for LLMSimulatorAgent.process_turn and generate_response."""

from __future__ import annotations

from typing import TYPE_CHECKING

from infrastructure.llm import MockLLMProvider
from src.agents.simulator_llm import LLMSimulatorAgent

if TYPE_CHECKING:
    from core.entities import Session


class TestProcessTurn:
    """process_turn: operator message -> LLM -> client reply in transcript."""

    async def test_basic_flow(self, agent: LLMSimulatorAgent, session: Session) -> None:
        """Operator says something -> client replies."""
        reply = await agent.process_turn(session, "Здравствуйте, чем могу помочь?")

        assert isinstance(reply, str)
        assert len(reply) > 0

    async def test_transcript_updated_after_turn(
        self, agent: LLMSimulatorAgent, session: Session
    ) -> None:
        """After process_turn a client entry appears in transcript."""
        assert len(session.transcript) == 0

        await agent.process_turn(session, "Добрый день!")

        assert len(session.transcript) == 1
        entry = session.transcript[0]
        assert entry.speaker == "client"
        assert entry.text is not None
        assert entry.timestamp is not None

    async def test_multiple_turns_accumulate(
        self, agent: LLMSimulatorAgent, session: Session
    ) -> None:
        """Consecutive process_turn calls accumulate transcript entries."""
        for msg in ("Здравствуйте", "Что вас беспокоит?", "Расскажите подробнее"):
            await agent.process_turn(session, msg)

        assert len(session.transcript) == 3
        assert all(e.speaker == "client" for e in session.transcript)

    async def test_passes_operator_message_in_messages(
        self, session: Session
    ) -> None:
        """Echo mode returns operator message -> it lands in transcript."""
        llm = MockLLMProvider(mode="echo")
        agent = LLMSimulatorAgent(llm=llm)

        await agent.process_turn(session, "Какой ваш тариф?")

        assert len(session.transcript) == 1
        assert "Какой ваш тариф?" in session.transcript[0].text


class TestGenerateResponse:
    """generate_response: generate based on existing history."""

    async def test_returns_string(self, agent: LLMSimulatorAgent, session: Session) -> None:
        """Simply returns a string."""
        await agent.process_turn(session, "Здравствуйте")

        reply = await agent.generate_response(session)
        assert isinstance(reply, str)
        assert len(reply) > 0
