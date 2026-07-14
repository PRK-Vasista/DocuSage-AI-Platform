# This is Copyright of DocuSage 2026 Owner Rohith Kumar Vasista P.

"""
Tests for password change and reset flows.
"""

from datetime import datetime, timedelta, timezone

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.auth_utils import verify_password
from app.core.config import app_settings
from app.database import get_db
from app.main import app
from app.models import PasswordResetToken, User
from app.routers.auth import _hash_reset_token


@pytest.mark.asyncio
async def test_change_password_success(db_session, test_user, auth_headers):
    """Authenticated users can change their password with the current password."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/change-password",
            headers=auth_headers,
            json={
                "current_password": "password123",
                "new_password": "new-password-99",
            },
        )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    refreshed = await db_session.get(User, test_user.id)
    assert verify_password("new-password-99", refreshed.password_hash)


@pytest.mark.asyncio
async def test_change_password_rejects_wrong_current(db_session, test_user, auth_headers):
    """Wrong current password must fail."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/change-password",
            headers=auth_headers,
            json={
                "current_password": "wrong-password",
                "new_password": "new-password-99",
            },
        )

    app.dependency_overrides.clear()
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_forgot_password_without_smtp_logs_in_development(db_session, test_user, monkeypatch):
    """Without SMTP in development, forgot-password still creates a token."""

    monkeypatch.setattr(app_settings, "APP_ENV", "development")
    monkeypatch.setattr(app_settings, "SMTP_HOST", "")

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/forgot-password",
            json={"email": test_user.email},
        )

    app.dependency_overrides.clear()
    assert response.status_code == 200

    result = await db_session.execute(
        select(PasswordResetToken).where(PasswordResetToken.user_id == test_user.id)
    )
    tokens = result.scalars().all()
    assert len(tokens) == 1


@pytest.mark.asyncio
async def test_forgot_password_production_requires_smtp(db_session, test_user, monkeypatch):
    """Production without SMTP must refuse forgot-password."""

    monkeypatch.setattr(app_settings, "APP_ENV", "production")
    monkeypatch.setattr(app_settings, "SMTP_HOST", "")

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/forgot-password",
            json={"email": test_user.email},
        )

    app.dependency_overrides.clear()
    assert response.status_code == 503


@pytest.mark.asyncio
async def test_reset_password_consumes_token(db_session, test_user):
    """Valid reset token updates password and cannot be reused."""

    raw_token = "test-reset-token-value"
    now = datetime.now(timezone.utc)
    db_session.add(
        PasswordResetToken(
            user_id=test_user.id,
            token_hash=_hash_reset_token(raw_token),
            expires_at=now + timedelta(hours=1),
            used_at=None,
            created_at=now,
        )
    )
    await db_session.commit()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        first = await client.post(
            "/api/v1/auth/reset-password",
            json={"token": raw_token, "new_password": "reset-pass-42"},
        )
        second = await client.post(
            "/api/v1/auth/reset-password",
            json={"token": raw_token, "new_password": "another-pass"},
        )

    app.dependency_overrides.clear()

    assert first.status_code == 200
    assert second.status_code == 400
    refreshed = await db_session.get(User, test_user.id)
    assert verify_password("reset-pass-42", refreshed.password_hash)


@pytest.mark.asyncio
async def test_reset_password_rejects_expired_token(db_session, test_user):
    """Expired tokens are rejected."""

    raw_token = "expired-token"
    now = datetime.now(timezone.utc)
    db_session.add(
        PasswordResetToken(
            user_id=test_user.id,
            token_hash=_hash_reset_token(raw_token),
            expires_at=now - timedelta(minutes=5),
            used_at=None,
            created_at=now - timedelta(hours=2),
        )
    )
    await db_session.commit()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/reset-password",
            json={"token": raw_token, "new_password": "does-not-matter"},
        )

    app.dependency_overrides.clear()
    assert response.status_code == 400
