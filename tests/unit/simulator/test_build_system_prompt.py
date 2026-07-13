"""Tests for LLMSimulatorAgent._build_system_prompt."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

from core.entities import DifficultyLevel, Session
from src.agents.simulator_llm import LLMSimulatorAgent

if TYPE_CHECKING:
    from core.entities.script_node import ScriptNode
    from infrastructure.llm import MockLLMProvider


class TestBuildSystemPrompt:
    """_build_system_prompt — direct system prompt testing."""

    async def test_no_script_no_psychotype(self, mock_llm: MockLLMProvider) -> None:
        """Without script and psychotype - basic system prompt."""
        agent = LLMSimulatorAgent(llm=mock_llm)
        session = Session(
            user_id=uuid4(),
            scenario_id=uuid4(),
        )

        prompt = agent._build_system_prompt(session)
        assert "клиент" in prompt.lower()
        assert "оператором" in prompt.lower()

    async def test_with_all_fields(
        self, agent_with_script: LLMSimulatorAgent, session: Session
    ) -> None:
        """Script, psychotype and difficulty - all in prompt."""
        prompt = agent_with_script._build_system_prompt(session)

        assert "aggressive" in prompt.lower()
        assert "intermediate" in prompt.lower()

    async def test_difficulty_higher_adds_demanding_note(
        self, mock_llm: MockLLMProvider
    ) -> None:
        """EXPERT difficulty adds demanding note to prompt."""
        agent = LLMSimulatorAgent(llm=mock_llm)
        session = Session(
            user_id=uuid4(),
            scenario_id=uuid4(),
            difficulty_at_start=DifficultyLevel.EXPERT,
        )

        prompt = agent._build_system_prompt(session)
        assert "требовательнее" in prompt.lower() or "expert" in prompt.lower()

    async def test_script_text_from_session(
        self, mock_llm: MockLLMProvider
    ) -> None:
        """script_text_at_start appears in system prompt without ScriptNode."""
        agent = LLMSimulatorAgent(llm=mock_llm)
        session = Session(
            user_id=uuid4(),
            scenario_id=uuid4(),
            script_text_at_start="Оператор должен предложить тариф 'Максимум'",
        )

        prompt = agent._build_system_prompt(session)

        assert "Максимум" in prompt
        assert "Скрипт, который отрабатывает" in prompt

    async def test_no_script_text_no_section(
        self, mock_llm: MockLLMProvider
    ) -> None:
        """Without script_text_at_start — no script section in prompt."""
        agent = LLMSimulatorAgent(llm=mock_llm)
        session = Session(
            user_id=uuid4(),
            scenario_id=uuid4(),
        )

        prompt = agent._build_system_prompt(session)

        assert "Скрипт, который отрабатывает" not in prompt

    async def test_script_text_and_script_node_both(
        self, mock_llm: MockLLMProvider, script: ScriptNode
    ) -> None:
        """Both ScriptNode and script_text_at_start appear in prompt."""
        agent = LLMSimulatorAgent(llm=mock_llm, script=script)
        session = Session(
            user_id=uuid4(),
            scenario_id=uuid4(),
            script_text_at_start="Оператор должен предложить тариф",
        )

        prompt = agent._build_system_prompt(session)

        # From ScriptNode
        assert "переплат" in prompt
        # From session.script_text_at_start
        assert "тариф" in prompt
        assert "Скрипт, который отрабатывает" in prompt
