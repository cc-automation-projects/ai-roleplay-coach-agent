"""Shared fixtures for LLMSimulatorAgent tests."""

from __future__ import annotations

from uuid import uuid4

import pytest

from core.entities import DifficultyLevel, Psychotype, Scenario, Session
from core.entities.script_node import ScriptNode
from infrastructure.llm import MockLLMProvider
from src.agents.simulator_llm import LLMSimulatorAgent


@pytest.fixture
def mock_llm() -> MockLLMProvider:
    return MockLLMProvider(mode="simple")


@pytest.fixture
def scenario() -> Scenario:
    return Scenario(
        name="Angry customer",
        description="Aggressive client with billing issue",
        script_ref="s-001",
        script_text="Operator should greet the customer.",
        difficulty=DifficultyLevel.INTERMEDIATE,
        psychotype=Psychotype.AGGRESSIVE,
    )


@pytest.fixture
def session(scenario: Scenario) -> Session:
    return Session(
        user_id=uuid4(),
        scenario_id=scenario.id,
        difficulty_at_start=DifficultyLevel.INTERMEDIATE,
        psychotype_at_start=Psychotype.AGGRESSIVE,
    )


@pytest.fixture
def script(scenario: Scenario) -> ScriptNode:
    return ScriptNode(
        scenario_id=scenario.id,
        text="Клиент — раздражённый мужчина, звонит из-за переплаты за связь",
        keywords=["переплата", "связь", "тариф"],
    )


@pytest.fixture
def agent(mock_llm: MockLLMProvider) -> LLMSimulatorAgent:
    return LLMSimulatorAgent(llm=mock_llm)


@pytest.fixture
def agent_with_script(mock_llm: MockLLMProvider, script: ScriptNode) -> LLMSimulatorAgent:
    return LLMSimulatorAgent(llm=mock_llm, script=script)
