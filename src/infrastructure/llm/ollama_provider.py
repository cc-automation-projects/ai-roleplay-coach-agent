"""OllamaProvider — HTTP-клиент к локальному Ollama через OpenAI-совместимый API.

Использует /v1/chat/completions (тот же эндпоинт что у OpenAI).
Поддерживает timeout, retry, читаемые ошибки при падении.
"""

import asyncio
import logging
from typing import Any, Self

import httpx

from core.exceptions import AITimeoutError, InfrastructureError
from core.interfaces.llm_provider import LLMMessage

logger = logging.getLogger(__name__)


class OllamaProvider:
    """Провайдер для локального Ollama через OpenAI-совместимый API.

    Пример .env:
        LLM_BASE_URL=http://localhost:11434/v1
        LLM_MODEL=qwen2.5:7b
        LLM_TIMEOUT=60
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434/v1",
        model: str = "qwen2.5:7b",
        timeout: int = 60,
        max_retries: int = 2,
        api_key: str | None = None,
    ) -> None:
        """Инициализация.

        Args:
            base_url: Адрес OpenAI-совместимого API (например, Ollama /v1).
            model: Имя модели в Ollama.
            timeout: Таймаут запроса в секундах.
            max_retries: Количество повторных попыток при ошибках.
            api_key: API-ключ для OpenAI-совместимых прокси.
                     Если передан, добавляется как Bearer-токен.
        """
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout = timeout
        self._max_retries = max_retries
        self._api_key = api_key
        headers: dict[str, str] = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=httpx.Timeout(timeout),
            headers=headers,
        )

    async def generate(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 1024,
        stop: list[str] | None = None,
    ) -> str:
        """Отправить запрос в Ollama и получить ответ."""
        payload = self._build_payload(messages, temperature, max_tokens, stop)
        last_error: Exception | None = None

        for attempt in range(1 + self._max_retries):
            try:
                response = await self._client.post(
                    "/chat/completions",
                    json=payload,
                )
                response.raise_for_status()
                data: dict[str, Any] = response.json()
                return self._extract_content(data)

            except httpx.TimeoutException as exc:
                last_error = exc
                logger.warning(
                    "Ollama timeout (attempt %d/%d): %s",
                    attempt + 1, 1 + self._max_retries, exc,
                )
                if attempt < self._max_retries:
                    await asyncio.sleep(1.0 * (attempt + 1))
                    continue
                msg = (
                    f"Ollama timeout after {self._timeout}s "
                    f"({self._max_retries + 1} attempts)"
                )
                raise AITimeoutError(
                    msg
                ) from exc

            except httpx.HTTPStatusError as exc:
                last_error = exc
                logger.exception(
                    "Ollama HTTP error (attempt %d/%d): %s — %s",
                    attempt + 1, 1 + self._max_retries,
                    exc.response.status_code, exc.response.text,
                )
                if attempt < self._max_retries and exc.response.status_code >= 500:
                    await asyncio.sleep(1.0 * (attempt + 1))
                    continue
                msg = f"Ollama HTTP {exc.response.status_code}: {exc.response.text[:200]}"
                raise InfrastructureError(
                    msg
                ) from exc

            except httpx.RequestError as exc:
                last_error = exc
                logger.warning(
                    "Ollama connection error (attempt %d/%d): %s",
                    attempt + 1, 1 + self._max_retries, str(exc),
                )
                if attempt < self._max_retries:
                    await asyncio.sleep(1.0 * (attempt + 1))
                    continue
                msg = f"Cannot connect to Ollama at {self._base_url}: {exc}"
                raise InfrastructureError(
                    msg
                ) from exc

        # Should never reach here, but satisfy type-checker
        raise InfrastructureError(
            f"Ollama request failed after {self._max_retries + 1} attempts"
            f": {last_error}" if last_error else "Unknown error"
        )

    async def aclose(self) -> None:
        """Закрыть HTTP-клиент."""
        await self._client.aclose()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.aclose()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_payload(
        self,
        messages: list[LLMMessage],
        temperature: float,
        max_tokens: int,
        stop: list[str] | None,
    ) -> dict[str, Any]:
        """Собрать тело запроса для /v1/chat/completions."""
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": [msg.model_dump() for msg in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }
        if stop:
            payload["stop"] = stop
        return payload

    @staticmethod
    def _extract_content(data: dict[str, Any]) -> str:
        """Извлечь текст ответа из JSON-ответа /v1/chat/completions."""
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            msg = (
                f"Unexpected Ollama response format: {exc}. "
                f"Response keys: {list(data.keys())}"
            )
            raise InfrastructureError(
                msg
            ) from exc
