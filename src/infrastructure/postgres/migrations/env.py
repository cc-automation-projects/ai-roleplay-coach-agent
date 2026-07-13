"""Alembic environment configuration for async PostgreSQL."""

import asyncio
import logging

from alembic import context
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

from infrastructure.postgres.models import Base  # used by alembic metadata

# Alembic Config object
config = context.config

# Set up logging manually (fileConfig can fail on Windows with INI paths)
logging.basicConfig(level=logging.WARNING)
logging.getLogger("alembic").setLevel(logging.INFO)

# Target metadata for autogenerate
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (emit SQL without connecting)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations with a connection."""
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in 'online' async mode."""
    url = config.get_main_option("sqlalchemy.url")
    if url is None:
        msg = "sqlalchemy.url is not set in alembic.ini"
        raise ValueError(msg)
    connectable = create_async_engine(url)

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
