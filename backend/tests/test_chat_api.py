"""
Integration tests for document chat API (AI unit mocked).
"""

import io
from datetime import datetime, timezone

import pytest
from httpx import AsyncClient

from app.core.config import PROCESSING_STATUS_READY
from app.models.document import Document


@pytest.mark.asyncio
async def test_chat_requires_ready_document(
    client: AsyncClient,
    auth_headers: dict[str, str],
    db_session,
    test_user,
):
    """Chat must be blocked until the document is ready."""
    document = Document(
        user_id=test_user.id,
        original_filename="not-ready.txt",
        stored_filename="not-ready.txt",
        file_path="user_uploads/1/not-ready.txt",
        mime_type="text/plain",
        size_bytes=12,
        processing_status="uploaded",
        document_summary=None,
        is_deleted=False,
    )
    db_session.add(document)
    await db_session.commit()
    await db_session.refresh(document)

    response = await client.post(
        f"/api/v1/chat/{document.id}",
        headers=auth_headers,
        json={"question": "What is this about?"},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_chat_ask_and_history_with_mocked_ai(
    client: AsyncClient,
    auth_headers: dict[str, str],
    db_session,
    test_user,
    monkeypatch,
):
    """Ready documents should support chat history and ask flows via mocked AI."""
    document = Document(
        user_id=test_user.id,
        original_filename="ready.txt",
        stored_filename="ready.txt",
        file_path="user_uploads/1/ready.txt",
        mime_type="text/plain",
        size_bytes=40,
        processing_status=PROCESSING_STATUS_READY,
        document_summary="DocuSage helps users manage and chat with documents.",
        processed_at=datetime.now(timezone.utc),
        is_deleted=False,
    )
    db_session.add(document)
    await db_session.commit()
    await db_session.refresh(document)

    async def fake_chat(*, question: str, document_context: str, history=None) -> str:
        return "It is about DocuSage document management."

    monkeypatch.setattr("app.services.chat_service.request_document_chat", fake_chat)

    ask_response = await client.post(
        f"/api/v1/chat/{document.id}",
        headers=auth_headers,
        json={"question": "What is this document about?"},
    )
    assert ask_response.status_code == 200
    ask_payload = ask_response.json()
    assert "DocuSage" in ask_payload["answer"]
    assert len(ask_payload["messages"]) == 2

    history_response = await client.get(
        f"/api/v1/chat/{document.id}",
        headers=auth_headers,
    )
    assert history_response.status_code == 200
    history_payload = history_response.json()
    assert history_payload["document_id"] == document.id
    assert len(history_payload["messages"]) == 2
    assert history_payload["messages"][0]["role"] == "user"
    assert history_payload["messages"][1]["role"] == "assistant"


@pytest.mark.asyncio
async def test_processing_uses_ai_when_available(
    client: AsyncClient,
    auth_headers: dict[str, str],
    db_session,
    monkeypatch,
):
    """Background processing should store the AI summary when the AI unit succeeds."""
    from app.services.document_processing_service import process_document_by_id

    async def fake_ai_summary(text: str, max_chars: int | None = None) -> str:
        return "AI overall summary of the uploaded document."

    monkeypatch.setattr(
        "app.services.document_processing_service.request_document_summary",
        fake_ai_summary,
    )

    files = {
        "file": (
            "ai-summary.txt",
            io.BytesIO(b"DocuSage Sprint 5 AI summarization test content."),
            "text/plain",
        ),
    }
    upload_response = await client.post(
        "/api/v1/files/upload",
        headers=auth_headers,
        files=files,
    )
    assert upload_response.status_code == 200
    document_id = upload_response.json()["id"]

    await process_document_by_id(document_id, db=db_session)

    summary_response = await client.get(
        f"/api/v1/files/{document_id}/summary",
        headers=auth_headers,
    )
    assert summary_response.status_code == 200
    payload = summary_response.json()
    assert payload["processing_status"] == "ready"
    assert payload["document_summary"] == "AI overall summary of the uploaded document."
