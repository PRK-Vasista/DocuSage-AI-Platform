"""
Unit tests for the fault-tolerant migration service.
"""

from pathlib import Path

import pytest

from app.core.exceptions import AlembicRevisionIdError
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


def test_validate_alembic_revision_ids_accepts_current_migrations():
    """Existing project migrations must stay within the VARCHAR(32) limit."""
    migration_service.validate_alembic_revision_ids()


def test_validate_alembic_revision_ids_rejects_oversized_id(tmp_path: Path):
    """Oversized revision IDs must raise AlembicRevisionIdError immediately."""
    versions_dir = tmp_path / "versions"
    versions_dir.mkdir()
    oversized = "x" * (migration_service.ALEMBIC_REVISION_MAX_LENGTH + 1)
    (versions_dir / "9999_too_long.py").write_text(
        f'revision: str = "{oversized}"\n'
        'down_revision: str | None = "0001_initial_schema"\n',
        encoding="utf-8",
    )

    with pytest.raises(AlembicRevisionIdError) as exc_info:
        migration_service.validate_alembic_revision_ids(versions_dir=versions_dir)

    assert "exceeds max=32" in exc_info.value.message


def test_validate_alembic_revision_ids_rejects_oversized_down_revision(tmp_path: Path):
    """Oversized down_revision IDs must also fail validation."""
    versions_dir = tmp_path / "versions"
    versions_dir.mkdir()
    oversized = "y" * (migration_service.ALEMBIC_REVISION_MAX_LENGTH + 1)
    (versions_dir / "9999_bad_down.py").write_text(
        'revision: str = "0009_ok"\n'
        f'down_revision: str | None = "{oversized}"\n',
        encoding="utf-8",
    )

    with pytest.raises(AlembicRevisionIdError):
        migration_service.validate_alembic_revision_ids(versions_dir=versions_dir)
