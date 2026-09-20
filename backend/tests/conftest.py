"""
Shared pytest fixtures for DocuSage backend tests.
"""

import os

# Disable Alembic during unit/API tests that use SQLite overrides.
os.environ.setdefault("ENABLE_ALEMBIC_MIGRATIONS", "false")
os.environ.setdefault("ENABLE_CREATE_ALL_FALLBACK", "true")

import asyncio
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.auth_utils import create_access_token, get_password_hash
from app.database import Base, get_db
from app.main import app
from app.models import User


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """
    Create a dedicated event loop for async pytest session scope.

    Yields:
        asyncio.AbstractEventLoop: Shared event loop instance.
    """
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def _isolate_upload_dir(tmp_path, monkeypatch: pytest.MonkeyPatch):
    """
    Route uploads into a writable temp directory for every test.

    Avoids host permission issues with the Docker-owned user_uploads folder.
    """
    from app.core.config import app_settings

    upload_root = tmp_path / "user_uploads"
    upload_root.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(app_settings, "UPLOAD_DIR", str(upload_root))


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Provide an isolated in-memory SQLite database session for each test.

    Yields:
        AsyncSession: Test-scoped async SQLAlchemy session.
    """
    engine = create_async_engine(TEST_DATABASE_URL, future=True)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """
    Create and persist a test user in the database.

    Args:
        db_session: Async SQLAlchemy session fixture.

    Returns:
        User: Persisted test user instance.
    """
    user = User(
        email="test.user@example.com",
        password_hash=get_password_hash("password123"),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def auth_headers(test_user: User) -> dict[str, str]:
    """
    Build Authorization headers for the seeded test user.

    Args:
        test_user: Persisted test user fixture.

    Returns:
        dict[str, str]: Bearer token headers.
    """
    token = create_access_token(data={"sub": test_user.email})
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def client(
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> AsyncGenerator[AsyncClient, None]:
    """
    Provide an HTTPX async client with database dependency overrides.

    Background processing is stubbed during API tests because the processing
    pipeline opens a production PostgreSQL session outside the test SQLite
    override. Dedicated processing tests invoke the service directly.

    Args:
        db_session: Async SQLAlchemy session fixture.
        monkeypatch: Pytest monkeypatch fixture.

    Yields:
        AsyncClient: Configured API test client.
    """

    async def noop_background_processing(document_id: int, db=None) -> None:
        return

    monkeypatch.setattr(
        "app.routers.files.process_document_by_id",
        noop_background_processing,
    )

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as async_client:
        yield async_client

    app.dependency_overrides.clear()
