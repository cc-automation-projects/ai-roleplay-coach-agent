"""Tests for Database class."""

import pytest
from sqlalchemy.engine import URL

from infrastructure.postgres.database import Database, make_url


class TestDatabase:
    def test_make_url_defaults(self):
        """Default URL should contain expected parts."""
        url = make_url()
        assert isinstance(url, URL)
        assert url.drivername == "postgresql+asyncpg"

    @pytest.mark.asyncio
    async def test_health_no_server(self):
        """Health check returns False when no DB is running."""
        url = URL.create(
            drivername="postgresql+asyncpg",
            username="test",
            password="test",
            host="127.0.0.1",
            port=19999,
            database="test",
        )
        db = Database(url=url)
        healthy = await db.health()
        assert healthy is False
        await db.close()
