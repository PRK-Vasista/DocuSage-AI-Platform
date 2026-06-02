"""
Fault-tolerant Alembic migration runner for DocuSage.

Migration execution is integrated into application startup rather than relying
on standalone shell scripts. Retries, logging, and optional fallback behavior
keep database initialization resilient during Docker boot ordering.
"""

import asyncio
import logging
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy.ext.asyncio import AsyncEngine

from ..core.config import app_settings
from ..database import Base, engine

logger = logging.getLogger("services.migration")
logger.setLevel(logging.DEBUG)

# Alembic configuration file lives at the backend project root (/app in Docker).
ALEMBIC_INI_PATH = Path(__file__).resolve().parent.parent.parent / "alembic.ini"


def _is_sqlite_database() -> bool:
    """
    Determine whether the configured database URL targets SQLite.

    Returns:
        bool: True when SQLite is configured (typically unit tests).
    """
    return app_settings.DATABASE_URL.lower().startswith("sqlite")


def _should_run_alembic() -> bool:
    """
    Decide whether Alembic migrations should run for the current environment.

    Returns:
        bool: True when Alembic is enabled and a PostgreSQL URL is configured.
    """
    if not app_settings.ENABLE_ALEMBIC_MIGRATIONS:
        logger.info("Alembic migrations disabled via ENABLE_ALEMBIC_MIGRATIONS=false.")
        return False

    if _is_sqlite_database():
        logger.info("Skipping Alembic because SQLite is configured (test runtime).")
        return False

    return True


def _build_alembic_config() -> Config:
    """
    Build an Alembic Config object pointing at the project configuration.

    Returns:
        Config: Alembic configuration with DATABASE_URL injected.

    Raises:
        FileNotFoundError: If alembic.ini cannot be located.
    """
    if not ALEMBIC_INI_PATH.exists():
        logger.error("Alembic configuration file not found at %s", ALEMBIC_INI_PATH)
        raise FileNotFoundError(f"Missing Alembic config: {ALEMBIC_INI_PATH}")

    alembic_config = Config(str(ALEMBIC_INI_PATH))
    alembic_config.set_main_option("sqlalchemy.url", app_settings.DATABASE_URL)
    logger.debug("Alembic config loaded from %s", ALEMBIC_INI_PATH)
    return alembic_config


def _run_alembic_upgrade() -> None:
    """
    Execute `alembic upgrade head` synchronously.

    Raises:
        Exception: Propagates Alembic failures to the caller for retry handling.
    """
    alembic_config = _build_alembic_config()
    logger.info("Running Alembic upgrade to head...")
    command.upgrade(alembic_config, "head")
    logger.info("Alembic upgrade to head completed successfully.")


async def apply_migrations() -> bool:
    """
    Apply database migrations with retry logic for transient startup failures.

    Docker Compose may start the backend before PostgreSQL is ready to accept
    connections. This method retries migration execution before giving up.

    Returns:
        bool: True when migrations were applied successfully, False otherwise.
    """
    if not _should_run_alembic():
        return False

    max_retries = app_settings.DB_MIGRATION_MAX_RETRIES
    retry_delay = app_settings.DB_MIGRATION_RETRY_SECONDS

    for attempt in range(1, max_retries + 1):
        try:
            logger.info(
                "Alembic migration attempt %s/%s starting...",
                attempt,
                max_retries,
            )
            await asyncio.to_thread(_run_alembic_upgrade)
            return True
        except FileNotFoundError as exc:
            logger.critical("Alembic configuration error: %s", exc)
            return False
        except Exception as exc:
            logger.warning(
                "Alembic migration attempt %s/%s failed: %s - %s",
                attempt,
                max_retries,
                exc.__class__.__name__,
                exc,
            )
            if attempt < max_retries:
                logger.info("Retrying Alembic migration in %s seconds...", retry_delay)
                await asyncio.sleep(retry_delay)
            else:
                logger.error(
                    "All Alembic migration attempts failed after %s tries.",
                    max_retries,
                )

    return False


async def create_all_fallback(db_engine: AsyncEngine | None = None) -> bool:
    """
    Fallback schema initialization using SQLAlchemy metadata.create_all().

    This is used only when Alembic is disabled or fails, providing a safety
    net for local development while keeping Alembic as the primary path.

    Args:
        db_engine: Optional engine override (defaults to application engine).

    Returns:
        bool: True when tables were created successfully, False otherwise.
    """
    if not app_settings.ENABLE_CREATE_ALL_FALLBACK:
        logger.warning(
            "create_all fallback is disabled via ENABLE_CREATE_ALL_FALLBACK=false."
        )
        return False

    from .. import models  # noqa: F401

    active_engine = db_engine or engine
    logger.warning(
        "Using SQLAlchemy create_all() fallback for schema initialization."
    )

    try:
        async with active_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("create_all fallback completed successfully.")
        return True
    except Exception as exc:
        logger.critical(
            "create_all fallback failed: %s - %s",
            exc.__class__.__name__,
            exc,
        )
        return False


async def initialize_database_schema() -> bool:
    """
    Initialize the database schema using Alembic first, then optional fallback.

    Returns:
        bool: True when schema initialization succeeded via Alembic or fallback.
    """
    migration_success = await apply_migrations()

    if migration_success:
        logger.info("Database schema initialized via Alembic migrations.")
        return True

    if _should_run_alembic():
        logger.error(
            "Alembic migrations failed and no fallback was attempted because "
            "Alembic is enabled for this environment."
        )
        if app_settings.ENABLE_CREATE_ALL_FALLBACK:
            return await create_all_fallback()

        return False

    # SQLite tests and environments with Alembic intentionally disabled.
    return await create_all_fallback()
