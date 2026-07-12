"""
Integration tests for document management API endpoints.
"""

import io

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_upload_list_soft_delete_and_permanent_delete_flow(
    client: AsyncClient,
    auth_headers: dict[str, str],
):
    """Documents should support upload, list, soft delete, and permanent delete."""
    file_content = b"DocuSage Sprint 3 integration test file."
    files = {
        "file": ("sample.txt", io.BytesIO(file_content), "text/plain"),
    }

    upload_response = await client.post(
        "/api/v1/files/upload",
        headers=auth_headers,
        files=files,
    )
    assert upload_response.status_code == 200
    uploaded = upload_response.json()
    document_id = uploaded["id"]
    assert uploaded["filename"] == "sample.txt"

    list_response = await client.get("/api/v1/files/", headers=auth_headers)
    assert list_response.status_code == 200
    listed = list_response.json()
    assert listed["total_count"] == 1
    assert listed["documents"][0]["id"] == document_id

    soft_delete_response = await client.delete(
        f"/api/v1/files/{document_id}",
        headers=auth_headers,
    )
    assert soft_delete_response.status_code == 200
    assert soft_delete_response.json()["deletion_type"] == "soft"

    active_list_response = await client.get("/api/v1/files/", headers=auth_headers)
    assert active_list_response.status_code == 200
    assert active_list_response.json()["total_count"] == 0

    trash_list_response = await client.get(
        "/api/v1/files/?include_deleted=true",
        headers=auth_headers,
    )
    assert trash_list_response.status_code == 200
    assert trash_list_response.json()["total_count"] == 1

    permanent_delete_response = await client.delete(
        f"/api/v1/files/{document_id}/permanent",
        headers=auth_headers,
    )
    assert permanent_delete_response.status_code == 200
    assert permanent_delete_response.json()["deletion_type"] == "permanent"

    final_trash_response = await client.get(
        "/api/v1/files/?include_deleted=true",
        headers=auth_headers,
    )
    assert final_trash_response.status_code == 200
    assert final_trash_response.json()["total_count"] == 0


@pytest.mark.asyncio
async def test_permanent_delete_requires_soft_delete_first(
    client: AsyncClient,
    auth_headers: dict[str, str],
):
    """Permanent deletion must be blocked until the document is soft-deleted."""
    files = {
        "file": ("guard.txt", io.BytesIO(b"guard"), "text/plain"),
    }
    upload_response = await client.post(
        "/api/v1/files/upload",
        headers=auth_headers,
        files=files,
    )
    document_id = upload_response.json()["id"]

    permanent_delete_response = await client.delete(
        f"/api/v1/files/{document_id}/permanent",
        headers=auth_headers,
    )
    assert permanent_delete_response.status_code == 409


@pytest.mark.asyncio
async def test_upload_rejects_unsupported_file_type(
    client: AsyncClient,
    auth_headers: dict[str, str],
):
    """Unsupported binary uploads must be rejected by the API."""
    files = {
        "file": ("binary.exe", io.BytesIO(b"fake-binary"), "application/octet-stream"),
    }
    response = await client.post(
        "/api/v1/files/upload",
        headers=auth_headers,
        files=files,
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_permanent_delete_removes_chat_messages(
    client: AsyncClient,
    auth_headers: dict[str, str],
    db_session,
    test_user,
):
    """Permanent delete must remove related chat messages without FK null errors."""
    from datetime import datetime, timezone

    from sqlalchemy import select

    from app.core.config import PROCESSING_STATUS_READY
    from app.models.chat_message import ChatMessage
    from app.models.document import Document

    document = Document(
        user_id=test_user.id,
        original_filename="chat-doc.txt",
        stored_filename="chat-doc.txt",
        file_path="user_uploads/1/chat-doc.txt",
        mime_type="text/plain",
        size_bytes=20,
        processing_status=PROCESSING_STATUS_READY,
        document_summary="Summary for delete test.",
        processed_at=datetime.now(timezone.utc),
        is_deleted=True,
        deleted_at=datetime.now(timezone.utc),
    )
    db_session.add(document)
    await db_session.commit()
    await db_session.refresh(document)

    db_session.add_all(
        [
            ChatMessage(
                document_id=document.id,
                user_id=test_user.id,
                role="user",
                content="What is this?",
            ),
            ChatMessage(
                document_id=document.id,
                user_id=test_user.id,
                role="assistant",
                content="A test document.",
            ),
        ]
    )
    await db_session.commit()

    response = await client.delete(
        f"/api/v1/files/{document.id}/permanent",
        headers=auth_headers,
    )
    assert response.status_code == 200

    remaining = await db_session.execute(
        select(ChatMessage).where(ChatMessage.document_id == document.id)
    )
    assert remaining.scalars().all() == []
