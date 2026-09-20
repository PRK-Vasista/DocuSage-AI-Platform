"""
API tests for auth happy paths, health, and rate limiting.
"""

import pytest
from httpx import AsyncClient

from app.core.config import app_settings
from app.main import app
from app.middleware.rate_limit import RateLimitMiddleware


def _clear_rate_limit_buckets() -> None:
    """Reset in-process rate-limit counters on the live middleware instance."""
    stack = app.middleware_stack
    while stack is not None:
        if isinstance(stack, RateLimitMiddleware):
            stack._hits.clear()
            return
        stack = getattr(stack, "app", None)


@pytest.mark.asyncio
async def test_register_and_login_happy_path(client: AsyncClient):
    """New users should register and then log in with the same credentials."""
    email = "ci.user@example.com"
    password = "secure-pass-42"

    register_response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )
    assert register_response.status_code == 200
    register_payload = register_response.json()
    assert register_payload.get("access_token")
    assert register_payload.get("token_type", "bearer").lower() == "bearer"

    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login_response.status_code == 200
    login_payload = login_response.json()
    assert login_payload.get("access_token")

    me_response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {login_payload['access_token']}"},
    )
    assert me_response.status_code == 200
    assert me_response.json()["email"] == email


@pytest.mark.asyncio
async def test_health_reports_database_and_ai(client: AsyncClient, monkeypatch, db_session):
    """Health endpoint should summarize DB and AI reachability without raising."""

    class _SessionCM:
        async def __aenter__(self):
            return db_session

        async def __aexit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr("app.main.AsyncSessionLocal", lambda: _SessionCM())

    async def fake_ai_health():
        return {"status": "ok"}

    monkeypatch.setattr(
        "app.main.ai_client_service.check_ai_health",
        fake_ai_health,
    )
    monkeypatch.setattr(app_settings, "AI_SERVICE_ENABLED", True)

    response = await client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["database"] == "ok"
    assert payload["ai_service"] == "ok"
    assert payload["status"] == "ok"


@pytest.mark.asyncio
async def test_login_rate_limit_returns_429(client: AsyncClient, monkeypatch):
    """Exceeding the login rate limit must return HTTP 429."""
    monkeypatch.setattr(
        "app.middleware.rate_limit._RULES",
        (("/api/v1/auth/login", 2, 60),),
    )
    _clear_rate_limit_buckets()

    payload = {"email": "rate.limit@example.com", "password": "wrong-password"}
    first = await client.post("/api/v1/auth/login", json=payload)
    second = await client.post("/api/v1/auth/login", json=payload)
    third = await client.post("/api/v1/auth/login", json=payload)

    assert first.status_code in {401, 400}
    assert second.status_code in {401, 400}
    assert third.status_code == 429
    assert "Retry-After" in third.headers
