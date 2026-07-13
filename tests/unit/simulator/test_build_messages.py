"""Tests for LLMSimulatorAgent._build_messages."""

from __future__ import annotations

from typing import TYPE_CHECKING

from core.entities import Psychotype

if TYPE_CHECKING:
    from core.entities import Session
    from src.agents.simulator_llm import LLMSimulatorAgent


class TestBuildMessages:
    """_build_messages — assembly system + transcript for LLM."""

    async def test_system_prompt_includes_psychotype(
        self, agent: LLMSimulatorAgent, session: Session
    ) -> None:
        """System prompt contains psychotype value (lowercase StrEnum)."""
        session.psychotype_at_start = Psychotype.AGGRESSIVE
        messages = agent._build_messages(session)

        system_msgs = [m for m in messages if m.role == "system"]
        assert len(system_msgs) == 1
        assert "aggressive" in system_msgs[0].content.lower()

    async def test_system_prompt_includes_difficulty(
        self, agent: LLMSimulatorAgent, session: Session
    ) -> None:
        """System prompt contains difficulty value (lowercase StrEnum)."""
        messages = agent._build_messages(session)

        system_msgs = [m for m in messages if m.role == "system"]
        assert len(system_msgs) == 1
        assert "intermediate" in system_msgs[0].content.lower()

    async def test_system_prompt_includes_script(
        self, agent_with_script: LLMSimulatorAgent, session: Session
    ) -> None:
        """System prompt contains ScriptNode text and keywords."""
        messages = agent_with_script._build_messages(session)

        system_msgs = [m for m in messages if m.role == "system"]
        content = system_msgs[0].content
        assert "переплат" in content
        assert "связь" in content or "тариф" in content

    async def test_build_messages_with_new_operator_message(
        self, agent: LLMSimulatorAgent, session: Session
    ) -> None:
        """When new_operator_message is passed, it appears in the list."""
        messages = agent._build_messages(
            session, new_operator_message="Тестовый вопрос"
        )

        user_msgs = [m for m in messages if m.role == "user"]
        assert any("Тестовый вопрос" in m.content for m in user_msgs)

    async def test_build_messages_empty_transcript_no_operator_message(
        self, agent: LLMSimulatorAgent, session: Session
    ) -> None:
        """Empty transcript + no new message -> only system prompt."""
        messages = agent._build_messages(session)

        assert len(messages) == 1
        assert messages[0].role == "system"

    async def test_transcript_entries_mapped_correctly(
        self, agent: LLMSimulatorAgent, session: Session
    ) -> None:
        """operator -> user, client -> assistant."""
        session.append_transcript_entry("operator", "Hello")
        session.append_transcript_entry("client", "Hi there")

        messages = agent._build_messages(session)

        user_msgs = [m for m in messages if m.role == "user"]
        assistant_msgs = [m for m in messages if m.role == "assistant"]
        assert any("Hello" in m.content for m in user_msgs)
        assert any("Hi there" in m.content for m in assistant_msgs)
