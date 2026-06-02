"""
Database engine, session factory, and initialization helpers.
"""

import logging

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from .core.config import app_settings

logger = logging.getLogger("database")
logger.setLevel(logging.DEBUG)

logger.info(
    "Database settings loaded. URL host segment: %s",
    app_settings.DATABASE_URL.split("@")[-1],
)

try:
    engine = create_async_engine(app_settings.DATABASE_URL, echo=False)
    AsyncSessionLocal = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    logger.info("SQLAlchemy engine and session maker initialized.")
except Exception as exc:
    logger.critical("Fatal: failed to initialize SQLAlchemy engine: %s", exc)
    raise


class Base(DeclarativeBase):
    """Declarative base class for all SQLAlchemy ORM models."""


async def get_db():
    """
    Provide an asynchronous database session for request-scoped dependencies.

    Yields:
        AsyncSession: Open SQLAlchemy session.

    Raises:
        Exception: Re-raises any unexpected database errors after logging them.
    """
    session = AsyncSessionLocal()
    logger.debug("New DB session acquired.")
    try:
        yield session
    except Exception as exc:
        logger.error("Error during database operation within session: %s", exc)
        raise
    finally:
        await session.close()
        logger.debug("DB session closed.")


async def init_db() -> bool:
    """
    Initialize the database schema on application startup.

    Alembic is the primary migration path. If migrations fail in development,
    an optional SQLAlchemy create_all() fallback can be enabled through
    environment settings for fault tolerance.

    Returns:
        bool: True when schema initialization succeeded, False otherwise.
    """
    from .services.migration_service import initialize_database_schema

    logger.info("Starting database schema initialization...")
    success = await initialize_database_schema()

    if success:
        logger.info("Database schema initialization completed successfully.")
    else:
        logger.critical(
            "Database schema initialization failed. "
            "Verify PostgreSQL availability and Alembic migration state."
        )

    return success
