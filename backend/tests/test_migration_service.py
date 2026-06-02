"""
Unit tests for the fault-tolerant migration service.
"""

import pytest

from app.services import migration_service


def test_should_run_alembic_false_for_sqlite(monkeypatch):
    """Alembic must be skipped automatically for SQLite test databases."""
    monkeypatch.setattr(
        migration_service.app_settings,
        "DATABASE_URL",
        "sqlite+aiosqlite:///:memory:",
    )
    monkeypatch.setattr(
        migration_service.app_settings,
        "ENABLE_ALEMBIC_MIGRATIONS",
        True,
    )

    assert migration_service._should_run_alembic() is False


def test_should_run_alembic_false_when_disabled(monkeypatch):
    """Alembic must be skipped when ENABLE_ALEMBIC_MIGRATIONS=false."""
    monkeypatch.setattr(
        migration_service.app_settings,
        "DATABASE_URL",
        "postgresql+asyncpg://user:password@db:5432/docu_sage_db",
    )
    monkeypatch.setattr(
        migration_service.app_settings,
        "ENABLE_ALEMBIC_MIGRATIONS",
        False,
    )

    assert migration_service._should_run_alembic() is False


def test_should_run_alembic_true_for_postgres(monkeypatch):
    """Alembic should run for PostgreSQL when enabled."""
    monkeypatch.setattr(
        migration_service.app_settings,
        "DATABASE_URL",
        "postgresql+asyncpg://user:password@db:5432/docu_sage_db",
    )
    monkeypatch.setattr(
        migration_service.app_settings,
        "ENABLE_ALEMBIC_MIGRATIONS",
        True,
    )

    assert migration_service._should_run_alembic() is True


@pytest.mark.asyncio
async def test_apply_migrations_skips_when_disabled(monkeypatch):
    """apply_migrations should safely no-op when Alembic is disabled."""
    monkeypatch.setattr(
        migration_service.app_settings,
        "ENABLE_ALEMBIC_MIGRATIONS",
        False,
    )

    result = await migration_service.apply_migrations()
    assert result is False
