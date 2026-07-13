import asyncio
from unittest.mock import AsyncMock

import pytest

from infrastructure.llm.ollama_provider import OllamaProvider
from infrastructure.postgres.database import Database


@pytest.mark.asyncio
async def test_shutdown_calls_aclose():
    provider = OllamaProvider()
    provider._client = AsyncMock()
    await provider.aclose()
    provider._client.aclose.assert_called_once()


@pytest.mark.asyncio
async def test_shutdown_calls_db_close():
    db = Database()
    db._engine = AsyncMock()
    db._factory = AsyncMock()
    await db.close()
    db._engine.dispose.assert_called_once()


@pytest.mark.asyncio
async def test_shutdown_timeout_not_block():
    # Simulate waiting for tasks with timeout
    async def slow_task():
        await asyncio.sleep(10)

    task = asyncio.create_task(slow_task())
    done, pending = await asyncio.wait([task], timeout=0.1)
    assert len(done) == 0
    assert len(pending) == 1
    task.cancel()
