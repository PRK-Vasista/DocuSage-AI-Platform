"""
Alembic migration environment for DocuSage.

Uses async SQLAlchemy with asyncpg to stay aligned with the FastAPI runtime.
"""

import asyncio
import logging
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.core.config import app_settings
from app.database import Base
from app import models  # noqa: F401

config = context.config
logger = logging.getLogger("alembic.env")

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option("sqlalchemy.url", app_settings.DATABASE_URL)
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Run Alembic migrations in offline mode using a SQL script URL only.
    """
    url = config.get_main_option("sqlalchemy.url")
    logger.info("Alembic offline migration mode started.")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

    logger.info("Alembic offline migration mode completed.")


def do_run_migrations(connection: Connection) -> None:
    """
    Configure Alembic context and execute migrations against a live connection.

    Args:
        connection: Synchronous SQLAlchemy connection wrapper.
    """
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    Run Alembic migrations using an async SQLAlchemy engine.
    """
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()
    logger.info("Alembic async migrations completed.")


def run_migrations_online() -> None:
    """
    Entry point for online Alembic migrations.
    """
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
