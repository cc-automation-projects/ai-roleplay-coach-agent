"""Async SQLAlchemy engine and session factory."""

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy import text
from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

__all__ = [
    "Database",
    "make_url",
]


def make_url() -> URL:
    """Build a PostgreSQL connection URL from environment variables."""
    return URL.create(
        "postgresql+asyncpg",
        username=os.environ.get("POSTGRES_USER", "postgres"),
        password=os.environ.get("POSTGRES_PASSWORD", ""),
        host=os.environ.get("POSTGRES_HOST", "localhost"),
        port=int(os.environ.get("POSTGRES_PORT", "5432")),
        database=os.environ.get("POSTGRES_DB", "coach_hub"),
    )


class Database:
    """Async SQLAlchemy engine and session factory.

    Engine is created lazily on first access (get_session or session).
    """

    def __init__(self, url: URL | None = None, *, echo: bool = False) -> None:
        self._url = url or make_url()
        self._echo = echo
        self._engine: AsyncSession | None = None
        self._factory: async_sessionmaker[AsyncSession] | None = None
        self._lock = __import__("threading").Lock()

    def _ensure_engine(self) -> None:
        """Create the engine on first call (thread-safe)."""
        if self._factory is not None:
            return
        with self._lock:
            if self._factory is not None:
                return
            ps = int(os.environ.get("DB_POOL_SIZE", "10"))
            mo = int(os.environ.get("DB_MAX_OVERFLOW", "20"))
            self._engine = create_async_engine(
                self._url,
                echo=self._echo,
                pool_size=ps,
                max_overflow=mo,
            )
            self._factory = async_sessionmaker(
                self._engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )

    async def close(self) -> None:
        if self._engine is not None:
            await self._engine.dispose()

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        self._ensure_engine()
        async with self._factory() as s:  # type: ignore[union-attr]
            try:
                yield s
                await s.commit()
            except Exception:
                await s.rollback()
                raise

    async def get_session(self) -> AsyncSession:
        self._ensure_engine()
        return self._factory()  # type: ignore[union-attr]

    async def health(self) -> bool:
        self._ensure_engine()
        try:
            async with self._factory() as s:  # type: ignore[union-attr]
                await s.execute(text("SELECT 1"))
        except Exception:  # noqa: BLE001
            return False
        else:
            return True
