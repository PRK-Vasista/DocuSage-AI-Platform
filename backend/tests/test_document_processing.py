"""
Integration tests for document processing pipeline.
"""

import io

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.core.config import app_settings
from app.core.exceptions import AIServiceClientError, SummarizationError, TextExtractionError
from app.models.document import Document
from app.services.document_processing_service import (
    _format_processing_error,
    _summarize_with_ai_or_fallback,
    process_document_by_id,
)


@pytest.mark.asyncio
async def test_upload_triggers_processing_to_ready_with_summary(
    client: AsyncClient,
    auth_headers: dict[str, str],
    db_session,
):
    """Uploaded documents should be processed into a ready state with summary text."""
    file_content = (
        b"DocuSage Sprint 4 processing test. "
        b"This document verifies extraction and summarization. "
        b"The platform stores summarized text capped at one megabyte."
    )
    files = {
        "file": ("processing.txt", io.BytesIO(file_content), "text/plain"),
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
    summary_payload = summary_response.json()
    assert summary_payload["processing_status"] == "ready"
    assert summary_payload["document_summary"]
    assert "DocuSage" in summary_payload["document_summary"]


def test_format_processing_error_is_user_clear():
    """Failed-state errors should be prefixed for the UI."""
    assert _format_processing_error(
        TextExtractionError("bad pdf")
    ).startswith("Text extraction failed:")
    assert _format_processing_error(
        SummarizationError("model empty")
    ).startswith("Summarization failed:")
    assert _format_processing_error(
        AIServiceClientError("timeout")
    ).startswith("AI service unavailable:")


@pytest.mark.asyncio
async def test_summarize_retries_then_falls_back(monkeypatch):
    """Transient AI failures should retry, then use extractive fallback."""
    monkeypatch.setattr(app_settings, "AI_SUMMARIZE_MAX_ATTEMPTS", 3)
    monkeypatch.setattr(app_settings, "AI_SUMMARIZE_RETRY_SECONDS", 0)
    monkeypatch.setattr(app_settings, "AI_FALLBACK_TO_EXTRACTIVE", True)

    calls = {"n": 0}

    async def flaky_ai(text: str, max_chars: int = 4000) -> str:
        calls["n"] += 1
        raise AIServiceClientError("temporary outage")

    monkeypatch.setattr(
        "app.services.document_processing_service.request_document_summary",
        flaky_ai,
    )

    summary = await _summarize_with_ai_or_fallback(
        "DocuSage retry test. Sentence two about processing reliability."
    )
    assert calls["n"] == 3
    assert "DocuSage" in summary or "retry" in summary.lower()


@pytest.mark.asyncio
async def test_summarize_succeeds_after_retry(monkeypatch):
    """AI summarization should succeed on a later attempt without fallback."""
    monkeypatch.setattr(app_settings, "AI_SUMMARIZE_MAX_ATTEMPTS", 3)
    monkeypatch.setattr(app_settings, "AI_SUMMARIZE_RETRY_SECONDS", 0)

    calls = {"n": 0}

    async def flaky_then_ok(text: str, max_chars: int = 4000) -> str:
        calls["n"] += 1
        if calls["n"] < 2:
            raise AIServiceClientError("blip")
        return "Retried AI summary for DocuSage."

    monkeypatch.setattr(
        "app.services.document_processing_service.request_document_summary",
        flaky_then_ok,
    )

    summary = await _summarize_with_ai_or_fallback("Some extracted document text.")
    assert calls["n"] == 2
    assert summary == "Retried AI summary for DocuSage."


@pytest.mark.asyncio
async def test_reprocess_failed_document_resets_and_queues(
    client: AsyncClient,
    auth_headers: dict[str, str],
    db_session,
):
    """Failed documents can be requeued via POST /reprocess."""
    files = {
        "file": ("retry-me.txt", io.BytesIO(b"Retry content for DocuSage."), "text/plain"),
    }
    upload_response = await client.post(
        "/api/v1/files/upload",
        headers=auth_headers,
        files=files,
    )
    assert upload_response.status_code == 200
    document_id = upload_response.json()["id"]

    result = await db_session.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one()
    document.processing_status = "failed"
    document.processing_error = "Text extraction failed: forced for test"
    await db_session.commit()

    reprocess_response = await client.post(
        f"/api/v1/files/{document_id}/reprocess",
        headers=auth_headers,
    )
    assert reprocess_response.status_code == 200
    payload = reprocess_response.json()
    assert payload["processing_status"] == "uploaded"
    assert payload.get("processing_error") in (None, "")


@pytest.mark.asyncio
async def test_reprocess_rejects_ready_document(
    client: AsyncClient,
    auth_headers: dict[str, str],
    db_session,
):
    """Ready documents must not be reprocessed through the retry endpoint."""
    files = {
        "file": ("ready.txt", io.BytesIO(b"Already ready content."), "text/plain"),
    }
    upload_response = await client.post(
        "/api/v1/files/upload",
        headers=auth_headers,
        files=files,
    )
    document_id = upload_response.json()["id"]

    result = await db_session.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one()
    document.processing_status = "ready"
    document.document_summary = "Existing summary"
    await db_session.commit()

    reprocess_response = await client.post(
        f"/api/v1/files/{document_id}/reprocess",
        headers=auth_headers,
    )
    assert reprocess_response.status_code == 409
