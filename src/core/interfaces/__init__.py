"""Repository and service interfaces (port/adapter pattern)."""

from core.interfaces.llm_provider import LLMMessage, LLMProvider

__all__ = [
    "LLMMessage",
    "LLMProvider",
]
