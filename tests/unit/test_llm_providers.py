"""Tests for LLM provider layer — protocol, Mock, Ollama, Factory."""

import os
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from core.exceptions import AITimeoutError, ConfigurationError, InfrastructureError
from core.interfaces.llm_provider import LLMMessage
from src.infrastructure.llm.factory import create_llm_provider
from src.infrastructure.llm.mock_provider import MockLLMProvider
from src.infrastructure.llm.ollama_provider import OllamaProvider

# ── Helpers ────────────────────────────────────────────────────────


def _msg(role: str, content: str) -> LLMMessage:
    return LLMMessage(role=role, content=content)  # type: ignore[arg-type]


# ── LLMMessage ─────────────────────────────────────────────────────


class TestLLMMessage:
    """LLMMessage — базовая модель сообщения."""

    def test_create_system(self) -> None:
        msg = _msg("system", "You are a helper")
        assert msg.role == "system"
        assert msg.content == "You are a helper"

    def test_create_user(self) -> None:
        msg = _msg("user", "Hello")
        assert msg.role == "user"

    def test_create_assistant(self) -> None:
        msg = _msg("assistant", "Hi there")
        assert msg.role == "assistant"

    def test_serialize(self) -> None:
        msg = _msg("user", "test")
        data = msg.model_dump()
        assert data == {"role": "user", "content": "test"}

    def test_invalid_role(self) -> None:
        with pytest.raises(Exception):
            LLMMessage(role="invalid", content="x")  # type: ignore[arg-type]


# ── MockLLMProvider ────────────────────────────────────────────────


class TestMockLLMProvider:
    """MockLLMProvider — все режимы."""

    @pytest.mark.asyncio
    async def test_simple_mode(self) -> None:
        provider = MockLLMProvider(mode="simple")
        result = await provider.generate([_msg("user", "Hi")])
        assert result == "Mock response"

    @pytest.mark.asyncio
    async def test_simple_mode_empty(self) -> None:
        provider = MockLLMProvider(mode="simple")
        result = await provider.generate([])
        assert result == "Mock response"

    @pytest.mark.asyncio
    async def test_echo_mode(self) -> None:
        provider = MockLLMProvider(mode="echo")
        result = await provider.generate([_msg("user", "Hello world")])
        assert result == "Hello world"

    @pytest.mark.asyncio
    async def test_echo_mode_last_message(self) -> None:
        provider = MockLLMProvider(mode="echo")
        result = await provider.generate([
            _msg("system", "System prompt"),
            _msg("user", "First"),
            _msg("assistant", "Middle"),
            _msg("user", "Last"),
        ])
        assert result == "Last"

    @pytest.mark.asyncio
    async def test_echo_empty(self) -> None:
        provider = MockLLMProvider(mode="echo")
        result = await provider.generate([])
        assert result == ""

    @pytest.mark.asyncio
    async def test_template_mode_exact_match(self) -> None:
        provider = MockLLMProvider(
            mode="template",
            responses={"Hi": "Hello!", "Bye": "Goodbye!"},
        )
        result = await provider.generate([_msg("user", "Hi")])
        assert result == "Hello!"

    @pytest.mark.asyncio
    async def test_template_mode_system_match(self) -> None:
        provider = MockLLMProvider(
            mode="template",
            responses={"You are a bot": "I am a bot"},
        )
        result = await provider.generate([
            _msg("system", "You are a bot"),
            _msg("user", "Hello"),
        ])
        assert result == "I am a bot"

    @pytest.mark.asyncio
    async def test_template_mode_fallback(self) -> None:
        provider = MockLLMProvider(mode="template", responses={})
        result = await provider.generate([_msg("user", "unknown")])
        assert result == "Mock template response"

    @pytest.mark.asyncio
    async def test_template_empty(self) -> None:
        provider = MockLLMProvider(mode="template")
        result = await provider.generate([])
        assert result == ""

    def test_invalid_mode(self) -> None:
        with pytest.raises(ValueError, match="Unknown MockLLMProvider mode"):
            MockLLMProvider(mode="invalid")

    @pytest.mark.asyncio
    async def test_ignores_temperature_and_stop(self) -> None:
        provider = MockLLMProvider(mode="echo")
        result = await provider.generate(
            [_msg("user", "Hi")],
            temperature=0.9,
            max_tokens=999,
            stop=["\n"],
        )
        assert result == "Hi"

    def test_protocol_compliance(self) -> None:
        """Проверка что MockLLMProvider соответствует LLMProvider protocol."""
        provider = MockLLMProvider(mode="simple")
        # Проверяем наличие метода generate
        assert hasattr(provider, "generate")
        # Проверяем что он callable
        assert callable(provider.generate)


# ── OllamaProvider ─────────────────────────────────────────────────


class TestOllamaProvider:
    """OllamaProvider — с мокированным httpx."""

    @pytest.fixture
    def mock_client(self) -> AsyncMock:
        """Создаём мок для httpx.AsyncClient."""
        client = AsyncMock(spec=httpx.AsyncClient)
        response = AsyncMock(spec=httpx.Response)
        response.status_code = 200
        response.json.return_value = {
            "choices": [{"message": {"content": "Hello from Ollama"}}],
        }
        response.raise_for_status.return_value = None
        client.post.return_value = response
        return client

    @pytest.fixture
    def provider(self, mock_client: AsyncMock) -> OllamaProvider:
        p = OllamaProvider(base_url="http://test:11434/v1", model="test-model", timeout=5)
        # Подменяем клиент
        p._client = mock_client
        return p

    async def test_generate_basic(self, provider: OllamaProvider, mock_client: AsyncMock) -> None:
        """Базовый запрос → получение ответа."""
        result = await provider.generate([_msg("user", "Hi")])

        assert result == "Hello from Ollama"
        mock_client.post.assert_called_once()

        # Проверяем тело запроса
        call_kwargs = mock_client.post.call_args[1]
        assert call_kwargs["json"]["model"] == "test-model"
        assert call_kwargs["json"]["messages"][0]["content"] == "Hi"
        assert call_kwargs["json"]["stream"] is False

    async def test_generate_with_options(self, provider: OllamaProvider, mock_client: AsyncMock) -> None:
        """Параметры temperature, max_tokens, stop передаются корректно."""
        await provider.generate(
            [_msg("user", "Hi")],
            temperature=0.3,
            max_tokens=512,
            stop=["\n", "END"],
        )
        call_kwargs = mock_client.post.call_args[1]
        payload = call_kwargs["json"]
        assert payload["temperature"] == 0.3
        assert payload["max_tokens"] == 512
        assert payload["stop"] == ["\n", "END"]

    async def test_generate_without_stop(self, provider: OllamaProvider, mock_client: AsyncMock) -> None:
        """Если stop не передан — его не должно быть в payload."""
        await provider.generate([_msg("user", "Hi")])
        call_kwargs = mock_client.post.call_args[1]
        assert "stop" not in call_kwargs["json"]

    async def test_http_error_4xx(self, provider: OllamaProvider, mock_client: AsyncMock) -> None:
        """4xx ошибка → InfrastructureError без retry."""
        response = AsyncMock(spec=httpx.Response)
        response.status_code = 400
        response.text = '{"error": "bad request"}'
        response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "400 Bad Request", request=AsyncMock(), response=response,
        )
        mock_client.post.return_value = response

        with pytest.raises(InfrastructureError, match="Ollama HTTP 400"):
            await provider.generate([_msg("user", "Hi")])
        # 4xx — retry не делаем
        assert mock_client.post.call_count == 1

    async def test_http_error_5xx_retry(self, provider: OllamaProvider, mock_client: AsyncMock) -> None:
        """5xx ошибка → ретрай, потом InfrastructureError."""
        response = AsyncMock(spec=httpx.Response)
        response.status_code = 503
        response.text = "Service Unavailable"
        response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "503 Service Unavailable", request=AsyncMock(), response=response,
        )
        mock_client.post.return_value = response

        with pytest.raises(InfrastructureError, match="Ollama HTTP 503"):
            await provider.generate([_msg("user", "Hi")])
        # 3 попытки (1 + max_retries=2)
        assert mock_client.post.call_count == 3

    async def test_timeout_retry(self, provider: OllamaProvider, mock_client: AsyncMock) -> None:
        """Таймаут → ретрай, потом AITimeoutError."""
        mock_client.post.side_effect = httpx.TimeoutException("timeout")

        with pytest.raises(AITimeoutError, match="Ollama timeout"):
            await provider.generate([_msg("user", "Hi")])
        assert mock_client.post.call_count == 3  # 1 + max_retries=2

    async def test_connection_error_retry(self, provider: OllamaProvider, mock_client: AsyncMock) -> None:
        """Connection error → ретрай, потом InfrastructureError."""
        mock_client.post.side_effect = httpx.RequestError("connection refused")

        with pytest.raises(InfrastructureError, match="Cannot connect to Ollama"):
            await provider.generate([_msg("user", "Hi")])
        assert mock_client.post.call_count == 3

    async def test_unexpected_response_format(self, provider: OllamaProvider, mock_client: AsyncMock) -> None:
        """Ответ без choices → InfrastructureError."""
        response = AsyncMock(spec=httpx.Response)
        response.status_code = 200
        response.json.return_value = {"foo": "bar"}
        response.raise_for_status.return_value = None
        mock_client.post.return_value = response

        with pytest.raises(InfrastructureError, match="Unexpected Ollama response"):
            await provider.generate([_msg("user", "Hi")])

    async def test_aclose(self, provider: OllamaProvider, mock_client: AsyncMock) -> None:
        """aclose закрывает HTTP-клиент."""
        await provider.aclose()
        mock_client.aclose.assert_called_once()

    async def test_async_context_manager(self, provider: OllamaProvider, mock_client: AsyncMock) -> None:
        """Контекстный менеджер закрывает клиент."""
        async with provider as p:
            assert p is provider
        mock_client.aclose.assert_called_once()

    def test_protocol_compliance(self) -> None:
        """Проверка что OllamaProvider соответствует LLMProvider protocol."""
        provider = OllamaProvider()
        assert hasattr(provider, "generate")
        assert callable(provider.generate)


# ── Factory ────────────────────────────────────────────────────────


class TestProviderFactory:
    """create_llm_provider — фабрика провайдеров."""

    def test_mock_default(self) -> None:
        """Без env → MockLLMProvider."""
        with patch.dict(os.environ, {}, clear=True):
            provider = create_llm_provider()
        assert isinstance(provider, MockLLMProvider)

    def test_mock_explicit(self) -> None:
        """LLM_PROVIDER=mock → MockLLMProvider."""
        with patch.dict(os.environ, {"LLM_PROVIDER": "mock"}, clear=True):
            provider = create_llm_provider()
        assert isinstance(provider, MockLLMProvider)

    def test_ollama(self) -> None:
        """LLM_PROVIDER=ollama → OllamaProvider."""
        with patch.dict(
            os.environ,
            {"LLM_PROVIDER": "ollama"},
            clear=True,
        ):
            provider = create_llm_provider()
        assert isinstance(provider, OllamaProvider)
        assert provider._base_url == "http://localhost:11434/v1"
        assert provider._model == "qwen2.5:7b"

    def test_ollama_custom_url(self) -> None:
        """LLM_BASE_URL переопределяет базовый адрес."""
        with patch.dict(
            os.environ,
            {"LLM_PROVIDER": "ollama", "LLM_BASE_URL": "http://custom:8080/v1"},
            clear=True,
        ):
            provider = create_llm_provider()
        assert provider._base_url == "http://custom:8080/v1"

    def test_ollama_custom_model(self) -> None:
        """LLM_MODEL переопределяет модель."""
        with patch.dict(
            os.environ,
            {"LLM_PROVIDER": "ollama", "LLM_MODEL": "phi3:mini"},
            clear=True,
        ):
            provider = create_llm_provider()
        assert provider._model == "phi3:mini"

    def test_ollama_custom_timeout(self) -> None:
        """LLM_TIMEOUT переопределяет таймаут."""
        with patch.dict(
            os.environ,
            {"LLM_PROVIDER": "ollama", "LLM_TIMEOUT": "120"},
            clear=True,
        ):
            provider = create_llm_provider()
        assert provider._timeout == 120

    def test_openai_compat_goes_to_ollama_provider(self) -> None:
        """LLM_PROVIDER=openai_compat → тоже OllamaProvider (через тот же API)."""
        with patch.dict(
            os.environ,
            {"LLM_PROVIDER": "openai_compat"},
            clear=True,
        ):
            provider = create_llm_provider()
        assert isinstance(provider, OllamaProvider)

    def test_invalid_provider(self) -> None:
        """Неизвестный провайдер → ConfigurationError."""
        with patch.dict(
            os.environ,
            {"LLM_PROVIDER": "invalid"},
            clear=True,
        ), pytest.raises(ConfigurationError, match="Unknown LLM_PROVIDER"):
            create_llm_provider()

    def test_mock_case_insensitive(self) -> None:
        """LLM_PROVIDER регистронезависим."""
        with patch.dict(
            os.environ,
            {"LLM_PROVIDER": "Mock"},
            clear=True,
        ):
            provider = create_llm_provider()
        assert isinstance(provider, MockLLMProvider)

    def test_ollama_factory_passes_api_key(self) -> None:
        """Factory passes LLM_API_KEY to OllamaProvider."""
        with patch.dict(
            os.environ,
            {
                "LLM_PROVIDER": "ollama",
                "LLM_API_KEY": "test-key-123",
            },
            clear=True,
        ):
            provider = create_llm_provider()
        assert isinstance(provider, OllamaProvider)
        assert provider._api_key == "test-key-123"


    def test_ollama_with_api_key_sets_bearer_header(self) -> None:
        """OllamaProvider with api_key gets Bearer token."""
        tkey = "TEST-BEARER-FOR-TESTS"
        provider = OllamaProvider(api_key=tkey)
        assert provider._api_key == tkey
        headers = provider._client.headers
        auth = headers.get("Authorization") or headers.get("authorization")
        assert auth == "Bearer " + tkey


    def test_ollama_without_api_key_no_bearer(self) -> None:
        """OllamaProvider without api_key has no Authorization header."""
        provider = OllamaProvider()
        headers = provider._client.headers
        auth = headers.get("Authorization") or headers.get("authorization")
        assert auth is None
