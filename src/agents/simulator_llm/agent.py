

"""LLMSimulatorAgent — LLM-powered client simulator.

Первая версия поверх абстрактного LLMProvider.
Пока rule-based не заменяет — работает как параллельная реализация.

Состояния:
    - System prompt формируется из ScriptNode (сценарий, роль клиента)
    - User turn: сообщение оператора
    - LLM.generate → ответ клиента
    - История ведётся в Session.transcript
"""

from __future__ import annotations

import contextlib
import logging
from typing import TYPE_CHECKING

from core.interfaces.llm_provider import (
    LLMMessage,
    LLMProvider,
)

if TYPE_CHECKING:
    from core.entities import ScriptNode, Session

logger = logging.getLogger(__name__)


class LLMSimulatorAgent:
    """Симулятор клиента на LLM.

    Принимает сообщение оператора, формирует system prompt из ScriptNode,
    вызывает LLM и возвращает ответ клиента.
    """

    def __init__(
        self,
        llm: LLMProvider,
        script: ScriptNode | None = None,
    ) -> None:
        """Инициализация.

        Args:
            llm: LLM-провайдер для генерации ответов.
            script: Опциональный ScriptNode (сценарий, роль клиента).
        """
        self._llm = llm
        self._script = script

    async def process_turn(
        self,
        session: Session,
        operator_message: str,
    ) -> str:
        """Обработать один turn: сообщение оператора → ответ клиента.

        Добавляет сообщение оператора в транскрипт, генерирует
        ответ клиента через LLM и добавляет его в транскрипт.

        Args:
            session: Текущая сессия (transcript будет обновлён in-place).
            operator_message: Текст сообщения оператора.

        Returns:
            Сгенерированный ответ клиента.
        """
        # Собираем историю из транскрипта
        messages = self._build_messages(session, operator_message)

        # Генерируем ответ
        client_reply = await self._llm.generate(
            messages=messages,
            temperature=0.7,
            max_tokens=512,
        )

        # Добавляем в транскрипт через штатный метод Session
        # (автоматический trim до 100 записей + обновление updated_at)
        with contextlib.suppress(AttributeError):
            session.append_transcript_entry(
                speaker="client",
                text=client_reply,
            )

        return client_reply

    async def generate_response(
        self,
        session: Session,
    ) -> str:
        """Сгенерировать ответ клиента на основе существующей истории."""
        messages = self._build_messages(session)

        return await self._llm.generate(
            messages=messages,
            temperature=0.7,
            max_tokens=512,
        )

    # ── Internal helpers ───────────────────────────────────────────────

    def _build_messages(
        self,
        session: Session,
        new_operator_message: str | None = None,
    ) -> list[LLMMessage]:
        """Собрать список сообщений для LLM из транскрипта сессии.

        Args:
            session: Сессия с транскриптом.
            new_operator_message: Новое сообщение оператора (если ещё
                                  не добавлено в транскрипт).

        Returns:
            Список LLMMessage: system prompt → история диалога.
        """
        messages: list[LLMMessage] = []

        # System prompt
        system_prompt = self._build_system_prompt(session)
        messages.append(LLMMessage(role="system", content=system_prompt))

        # История из транскрипта
        if session.transcript:
            for entry in session.transcript:
                role = "user" if entry.speaker == "operator" else "assistant"
                messages.append(LLMMessage(role=role, content=entry.text))

        # Новое сообщение оператора (если есть)
        if new_operator_message:
            messages.append(
                LLMMessage(role="user", content=new_operator_message)
            )

        return messages

    def _build_system_prompt(self, session: Session) -> str:
        """Сформировать system prompt на основе ScriptNode и данных сессии."""
        lines: list[str] = [
            "Ты — клиент колл-центра. Отвечай как реальный человек в диалоге с оператором.",
            "",
        ]

        # Информация о клиенте
        if session.psychotype_at_start:
            lines.append(
                f"Твой психотип: {session.psychotype_at_start.value}. "
                f"Веди себя соответственно."
            )

        if session.difficulty_at_start:
            lines.append(
                f"Уровень сложности: {session.difficulty_at_start.value}. "
                f"Чем выше уровень, тем требовательнее и капризнее клиент."
            )

        # Информация из ScriptNode
        if self._script:
            lines.extend([
                "",
                "Сценарий разговора:",
                f"  Роль: {self._script.text}",
            ])

            if self._script.keywords:
                lines.append(
                    f"  Ключевые темы: {', '.join(self._script.keywords)}"
                )

        # Скрипт сценария (текст, который оператор должен отработать)
        if session.script_text_at_start:
            lines.extend([
                "",
                "Скрипт, который отрабатывает оператор:",
                f"  {session.script_text_at_start}",
                "",
                "Твоя задача — реагировать на действия оператора естественно, "
                "как реальный клиент. Оператор следует этому скрипту. "
                "Отвечай соответственно ситуации.",
            ])

        lines.extend([
            "",
            "Правила:",
            "- Не пиши 'как ИИ' или 'как ассистент'. Ты — живой человек.",
            "- Отвечай естественно, возможно с эмоциями.",
            "- Если оператор ошибается — укажи на это.",
            "- Если оператор грубит — вырази недовольство.",
            "- Если вопрос решён — поблагодари и заверши диалог.",
            "- Отвечай коротко, как в реальном разговоре (1-3 предложения).",
            "- Пиши ТОЛЬКО ответ клиента, без пояснений и ремарок.",
        ])

        return "\n".join(lines)
