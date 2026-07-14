# This is Copyright of DocuSage 2026 Owner Rohith Kumar Vasista P.

"""
Unit tests for AI service validation and routing (Ollama mocked).
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_health_endpoint(monkeypatch):
    """Health endpoint should report Ollama reachability from the probe."""

    async def fake_health() -> bool:
        return True

    monkeypatch.setattr("app.routers.ai.check_ollama_health", fake_health)

    async def fake_model_present() -> bool:
        return True

    monkeypatch.setattr(
        "app.routers.ai.is_configured_model_present",
        fake_model_present,
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/ai/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["ollama_reachable"] is True


@pytest.mark.asyncio
async def test_summarize_rejects_empty_text():
    """Empty summarize requests must return a validation/domain error."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/ai/summarize", json={"text": "   "})

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_summarize_success_with_mocked_ollama(monkeypatch):
    """Summarize should return model output when Ollama is mocked."""

    async def fake_summarize(text: str, max_chars: int | None = None) -> str:
        return "Mocked overall document summary."

    monkeypatch.setattr("app.routers.ai.summarize_text", fake_summarize)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/ai/summarize",
            json={"text": "DocuSage helps users manage documents."},
        )

    assert response.status_code == 200
    payload = response.json()
    assert "Mocked" in payload["summary"]
    assert payload["provider"] == "ollama"


@pytest.mark.asyncio
async def test_chat_success_with_mocked_ollama(monkeypatch):
    """Chat should return a grounded answer when Ollama is mocked."""

    async def fake_answer(question: str, document_context: str, history=None) -> str:
        return "The document discusses DocuSage."

    monkeypatch.setattr("app.routers.ai.answer_question", fake_answer)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/ai/chat",
            json={
                "question": "What is this about?",
                "document_context": "DocuSage is a document platform.",
                "history": [],
            },
        )

    assert response.status_code == 200
    assert "DocuSage" in response.json()["answer"]
