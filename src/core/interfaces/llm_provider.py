"""LLM provider protocol — абстракция для любых LLM (port/adapter)."""

from typing import Literal, Protocol

from pydantic import BaseModel


class LLMMessage(BaseModel):
    """Сообщение в диалоге с LLM."""

    role: Literal["system", "user", "assistant"]
    content: str


class LLMProvider(Protocol):
    """Протокол для любого LLM-провайдера.

    Достаточно простой, чтобы любая реализация
    (Ollama, OpenAI, Mock, vLLM) вписалась без изменений.
    """

    async def generate(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 1024,
        stop: list[str] | None = None,
    ) -> str:
        """Отправить сообщения в LLM и получить ответ.

        Args:
            messages: История диалога (system, user, assistant).
            temperature: Температура генерации (0.0 — детерминировано).
            max_tokens: Максимум токенов в ответе.
            stop: Строки-стоперы для досрочной остановки.

        Returns:
            Сгенерированный текст ответа.

        Raises:
            AITimeoutError: Если LLM не ответил за timeout.
            InfrastructureError: Если транспортная ошибка.
        """
        ...
