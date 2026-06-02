"""
Integration tests for document processing pipeline.
"""

import io

import pytest
from httpx import AsyncClient

from app.services.document_processing_service import process_document_by_id


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
