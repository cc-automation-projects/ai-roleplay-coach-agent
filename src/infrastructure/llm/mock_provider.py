"""MockLLMProvider — предсказуемые ответы для unit-тестов.

Режимы:
    simple  — всегда возвращает одну фразу ("Mock response").
    template — возвращает ответ из словаря responses по ключу
               (последнее сообщение пользователя или system prompt).
    echo    — возвращает последнее сообщение пользователя как есть.
"""

from core.interfaces.llm_provider import LLMMessage


class MockLLMProvider:
    """Mock LLM provider с предсказуемыми ответами для тестов."""

    def __init__(
        self,
        mode: str = "simple",
        responses: dict[str, str] | None = None,
    ) -> None:
        """Инициализация.

        Args:
            mode: "simple" | "template" | "echo"
            responses: Словарь prompt → ответ для режима "template"
        """
        if mode not in ("simple", "template", "echo"):
            msg = f"Unknown MockLLMProvider mode: {mode!r} (expected simple/template/echo)"
            raise ValueError(msg)
        self._mode = mode
        self._responses = responses or {}

    async def generate(  # noqa: PLR0911
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 1024,
        stop: list[str] | None = None,
    ) -> str:
        """Сгенерировать ответ согласно выбранному режиму."""
        _ = temperature, max_tokens, stop  # ignored in mock

        if self._mode == "simple":
            return "Mock response"

        if self._mode == "echo":
            if not messages:
                return ""
            return messages[-1].content

        # template mode
        if not messages:
            return ""

        # Пробуем найти точное совпадение по последнему сообщению
        last = messages[-1].content
        if last in self._responses:
            return self._responses[last]

        # Пробуем найти совпадение по system prompt
        for msg in messages:
            if msg.role == "system" and msg.content in self._responses:
                return self._responses[msg.content]

        return "Mock template response"
