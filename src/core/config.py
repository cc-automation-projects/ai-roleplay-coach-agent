"""Application settings via pydantic-settings (environment variables)."""

from __future__ import annotations

import os
import re

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application-wide settings loaded from environment / .env file."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # ── JWT ──────────────────────────────────────────────────────────────
    JWT_SIGNING_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_EXPIRE_DAYS: int = 7

    # ── Database ────────────────────────────────────────────────────────
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "coach"
    POSTGRES_PASSWORD: str = "changeme"  # noqa: S105
    POSTGRES_DB: str = "coach_hub"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    # ── LLM ─────────────────────────────────────────────────────────────
    LLM_PROVIDER: str = "mock"  # mock, ollama, openai_compat
    LLM_MODEL: str = "mistral:7b-instruct"
    LLM_BASE_URL: str = "http://localhost:11434/v1"
    LLM_API_KEY: str | None = None
    LLM_TIMEOUT: int = 60

    # ── Embedding ──────────────────────────────────────────────────────
    EMBEDDING_URL: str = "http://localhost:8001/v1/embeddings"
    EMBEDDING_MODEL: str = "intfloat/multilingual-e5-large"

    # ── Qdrant ─────────────────────────────────────────────────────────
    QDRANT_HOST: str = "localhost"
    QDRANT_HTTP_PORT: int = 6333
    VECTOR_SIZE: int = 1024

    # ── Observability ──────────────────────────────────────────────────
    LOG_FORMAT: str = "console"  # json | console
    LOG_LEVEL: str = "INFO"

    # ── Rate Limiting ──────────────────────────────────────────────────
    RATE_LIMIT_DEFAULT: int = 100
    RATE_LIMIT_AUTH: int = 10
    RATE_LIMIT_WINDOW: int = 60

    # ── Redis ──────────────────────────────────────────────────────────
    REDIS_URL: str = ""

    # ── Fairness ────────────────────────────────────────────────────────
    FAIRNESS_ENABLED: bool = True
    FAIRNESS_CONFIG_PATH: str = "fairness_config.yaml"
    FAIRNESS_AUDIT_INTERVAL_HOURS: int = 168

    # ── CORS ────────────────────────────────────────────────────────────
    CORS_ORIGINS: list[str] = ["*"]

    @field_validator("JWT_SIGNING_KEY")
    @classmethod
    def validate_jwt_key(cls, v: str) -> str:
        if not v:
            # In tests, allow empty, but warn at runtime
            return v
        if len(v) < 32:
            msg = "JWT_SIGNING_KEY must be at least 32 characters long"
            raise ValueError(msg)
        return v

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in allowed:
            msg = f"LOG_LEVEL must be one of {allowed}"
            raise ValueError(msg)
        return v.upper()

    @field_validator("LLM_BASE_URL")
    @classmethod
    def validate_llm_url(cls, v: str) -> str:
        if v and not re.match(r"^https?://", v):
            msg = "LLM_BASE_URL must be a valid HTTP/HTTPS URL"
            raise ValueError(msg)
        return v

    def validate(self) -> None:
        """Perform comprehensive validation, raising ValueError on any issue."""
        if self.LLM_PROVIDER not in ("mock", "ollama", "openai_compat"):
            msg = f"Unsupported LLM_PROVIDER: {self.LLM_PROVIDER}"
            raise ValueError(msg)
        if self.VECTOR_SIZE <= 0:
            msg = "VECTOR_SIZE must be positive"
            raise ValueError(msg)
        if self.DB_POOL_SIZE < 1:
            msg = "DB_POOL_SIZE must be at least 1"
            raise ValueError(msg)
        if self.RATE_LIMIT_DEFAULT < 1 or self.RATE_LIMIT_AUTH < 1:
            msg = "Rate limits must be positive"
            raise ValueError(msg)
        # Check JWT key for production (only if not test)
        if not os.getenv("PYTEST_VERSION") and len(self.JWT_SIGNING_KEY) < 32:
            msg = "JWT_SIGNING_KEY must be at least 32 characters in production"
            raise ValueError(msg)
        # Check LLM base URL if provider is not mock
        if self.LLM_PROVIDER != "mock" and not self.LLM_BASE_URL.startswith(("http://", "https://")):
            msg = f"LLM_BASE_URL must be a valid URL for provider {self.LLM_PROVIDER}"
            raise ValueError(msg)


settings = Settings()
