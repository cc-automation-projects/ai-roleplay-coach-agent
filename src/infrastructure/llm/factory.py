"""Provider Factory — создаёт нужный LLMProvider по переменной окружения.

Использование:
    provider = create_llm_provider()
    answer = await provider.generate([LLMMessage(role="user", content="Hi")])
"""

import os

from core.exceptions import ConfigurationError
from core.interfaces.llm_provider import LLMProvider
from src.infrastructure.llm.mock_provider import MockLLMProvider
from src.infrastructure.llm.ollama_provider import OllamaProvider

# Типы провайдеров, которые фабрика умеет создавать
PROVIDER_MOCK = "mock"
PROVIDER_OLLAMA = "ollama"
PROVIDER_OPENAI_COMPAT = "openai_compat"
VALID_PROVIDERS = frozenset({PROVIDER_MOCK, PROVIDER_OLLAMA, PROVIDER_OPENAI_COMPAT})

# Значения по умолчанию
_DEFAULT_BASE_URL = "http://localhost:11434/v1"
_DEFAULT_MODEL = "qwen2.5:7b"
_DEFAULT_TIMEOUT = 60


def create_llm_provider() -> LLMProvider:
    """Создать LLM-провайдер на основе переменной окружения LLM_PROVIDER.

    Returns:
        Экземпляр LLMProvider (MockLLMProvider или OllamaProvider).

    Raises:
        ConfigurationError: Если LLM_PROVIDER невалиден.
    """
    provider_name = os.getenv("LLM_PROVIDER", PROVIDER_MOCK).lower().strip()

    if provider_name not in VALID_PROVIDERS:
        msg = (
            f"Unknown LLM_PROVIDER={provider_name!r}. "
            f"Expected one of: {', '.join(sorted(VALID_PROVIDERS))}"
        )
        raise ConfigurationError(
            msg
        )

    if provider_name == PROVIDER_MOCK:
        mode = os.getenv("LLM_MOCK_MODE", "simple")
        return MockLLMProvider(mode=mode)

    # Ollama / OpenAI-совместимый — оба через /v1/chat/completions
    base_url = os.getenv("LLM_BASE_URL", _DEFAULT_BASE_URL)
    model = os.getenv("LLM_MODEL", _DEFAULT_MODEL)
    timeout = int(os.getenv("LLM_TIMEOUT", str(_DEFAULT_TIMEOUT)))
    api_key = os.getenv("LLM_API_KEY") or None

    return OllamaProvider(
        base_url=base_url,
        model=model,
        timeout=timeout,
        api_key=api_key,
    )
