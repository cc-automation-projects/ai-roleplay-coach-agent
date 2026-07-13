"""LLMSimulatorAdapter — SimulatorAgent-совместимая обёртка для LLMSimulatorAgent.

Позволяет подменять rule-based SimulatorAgent на LLM-симулятор
через зависимость get_simulator, без изменения кода API.
"""

from __future__ import annotations

import logging
import random
from typing import TYPE_CHECKING

from core.entities import Psychotype

if TYPE_CHECKING:
    from agents.simulator_llm.agent import LLMSimulatorAgent
    from core.entities import Scenario, Session

logger = logging.getLogger(__name__)

_MAX_TURNS = 8
_GREETINGS: dict[Psychotype, list[str]] = {
    Psychotype.NEUTRAL: [
        "Здравствуйте! Слушаю вас.",
        "Добрый день! Чем я могу помочь?",
        "Здравствуйте, я внимательно слушаю.",
    ],
    Psychotype.AGGRESSIVE: [
        "Это снова вы? Уже сколько можно звонить?",
        "Да? Чего вам?",
        "Слушаю... хотя не уверен что это поможет.",
    ],
    Psychotype.CONFUSED: [
        "Здравствуйте... кажется я не совсем понимаю что происходит.",
        "Добрый день. Вы не могли бы объяснить попроще?",
        "Ой, здравствуйте. Я, кажется, запутался в документах.",
    ],
    Psychotype.TECHNICALLY_INEPT: [
        "Здравствуйте! Рассказывайте, я во всё вникну.",
        "Добрый день! А давайте по порядку, с самого начала.",
        "О, хорошо что вы позвонили. Расскажите подробно.",
    ],
    Psychotype.FRAUDSTER: [
        "Ну и что вы хотите мне предложить?",
        "Здравствуйте. Только давайте без стандартных скриптов.",
        "Сомневаюсь что вы сможете мне помочь, но попробуйте.",
    ],
}


class LLMSimulatorAdapter:
    """Адаптер, приводящий LLMSimulatorAgent к интерфейсу SimulatorAgent.

    Delegates generate_response to LLMSimulatorAgent.process_turn,
    keeps start_dialogue and should_end rule-based (эти методы
    не требуют LLM).
    """

    def __init__(self, llm_agent: LLMSimulatorAgent) -> None:
        self._llm_agent = llm_agent

    async def start_dialogue(
        self, scenario: Scenario
    ) -> tuple[str, Psychotype]:
        """Start a dialogue: return greeting and scenario psychotype."""
        psychotype = scenario.psychotype
        greetings = _GREETINGS.get(psychotype, _GREETINGS[Psychotype.NEUTRAL])
        greeting = random.choice(greetings)  # noqa: S311
        logger.info(
            "LLMSimulator started dialogue psychotype=%s",
            psychotype.value,
        )
        return greeting, psychotype

    async def generate_response(self, session: Session) -> str:
        """Generate client response via LLM.

        Finds the last operator message and delegates to
        LLMSimulatorAgent.process_turn.
        """
        if not session.transcript:
            return "..."

        # Find last operator message
        last_op = ""
        for entry in reversed(session.transcript):
            if entry.speaker == "operator":
                last_op = entry.text
                break

        if not last_op:
            return "..."

        return await self._llm_agent.process_turn(session, last_op)

    async def should_end(self, session: Session) -> bool:
        """Check if the dialogue should end (rule-based)."""
        if not session.transcript:
            return False
        turns = len(session.transcript) // 2  # operator+client = 1 turn
        return turns >= _MAX_TURNS

    def reset_session(self, session_id: object) -> None:
        """No-op: LLMSimulatorAgent is stateless."""
