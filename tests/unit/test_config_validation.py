"""Tests for Settings validation."""

import pytest
from pydantic import ValidationError

from core.config import Settings


def test_valid_config():
    s = Settings(
        JWT_SIGNING_KEY="a" * 32,
        LOG_LEVEL="INFO",
        LLM_BASE_URL="http://localhost:11434/v1",
        VECTOR_SIZE=768,
    )
    s.validate()  # should not raise


def test_short_jwt_key_raises():
    """Short non-empty key raises ValueError during field validation."""
    with pytest.raises(ValidationError, match="at least 32 characters"):
        Settings(JWT_SIGNING_KEY="a" * 31)


def test_invalid_log_level():
    """Pydantic field_validator runs at init and raises ValidationError."""
    with pytest.raises(ValidationError, match="LOG_LEVEL must be one of"):
        Settings(LOG_LEVEL="VERBOSE")


def test_invalid_llm_url():
    """Invalid URL raises ValidationError from field_validator at init."""
    with pytest.raises(ValidationError, match="valid HTTP/HTTPS URL"):
        Settings(LLM_BASE_URL="not-a-url")


def test_invalid_llm_provider():
    """LLM_PROVIDER checked in validate(), not at init."""
    s = Settings(LLM_PROVIDER="unknown")
    with pytest.raises(ValueError, match="Unsupported LLM_PROVIDER"):
        s.validate()
