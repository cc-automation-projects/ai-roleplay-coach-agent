

"""Slow (live Ollama) tests for LLMSimulatorAgent.

Most unit tests have moved to tests/unit/simulator/.
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from core.entities import DifficultyLevel, Session
from core.entities.script_node import ScriptNode
from core.interfaces.llm_provider import LLMMessage
from infrastructure.llm.ollama_provider import OllamaProvider
from src.agents.simulator_llm import LLMSimulatorAgent


@pytest.mark.slow
class TestLiveOllama:
    """Live end-to-end tests with real Ollama (qwen2.5:7b).

    Requires Ollama server at 127.0.0.1:11434 with qwen2.5:7b installed.
    The first test call will be SLOW (~4 min on CPU) because the model
    loads into memory. Subsequent calls are faster (~10-15s).
    Skip:  pytest -m "not slow"
    """

    async def _ollama_available(self) -> bool:
        """Quick check if Ollama is reachable."""
        import httpx
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get("http://127.0.0.1:11434/api/tags")
                return resp.status_code == 200
        except Exception:
            return False

    @pytest.fixture
    async def live_provider(self) -> OllamaProvider:
        if not await self._ollama_available():
            pytest.skip("Ollama not available at 127.0.0.1:11434")
        provider = OllamaProvider(
            base_url="http://127.0.0.1:11434/v1",
            model="qwen2.5:7b",
            timeout=600,
            max_retries=0,
        )
        yield provider
        await provider.aclose()

    async def test_generate_basic(
        self, live_provider: OllamaProvider
    ) -> None:
        """Basic generate() returns non-empty Russian response."""
        messages = [
            LLMMessage(role="system", content="Ты — клиент колл-центра. Отвечай коротко."),
            LLMMessage(role="user", content="Здравствуйте, чем могу помочь?"),
        ]

        result = await live_provider.generate(messages)

        assert isinstance(result, str)
        assert len(result) > 0
        assert not result.isspace()

    async def test_llm_simulator_cycle(
        self, live_provider: OllamaProvider
    ) -> None:
        """Full cycle: LLMSimulatorAgent + Ollama -> client reply."""
        script_text = "Оператор помогает клиенту с настройкой тарифа"
        script = ScriptNode(
            scenario_id=uuid4(),
            text="Клиент — обычный пользователь, не разбирается в тарифах",
            keywords=["тариф", "настройка", "помощь"],
        )
        session = Session(
            user_id=uuid4(),
            scenario_id=uuid4(),
            difficulty_at_start=DifficultyLevel.INTERMEDIATE,
            script_text_at_start=script_text,
        )
        agent = LLMSimulatorAgent(llm=live_provider, script=script)

        reply = await agent.process_turn(session, "Здравствуйте! Чем могу помочь?")

        assert isinstance(reply, str)
        assert len(reply) > 0
        # Should not contain meta-commentary
        assert "как ИИ" not in reply.lower()
        assert "как ассистент" not in reply.lower()
