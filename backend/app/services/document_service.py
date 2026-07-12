"""
Document domain service.

Coordinates validation, quota checks, database persistence, and filesystem
operations for user documents.
"""

import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import delete, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.exceptions import (
    DatabaseOperationError,
    DocumentAlreadyDeletedError,
    DocumentNotFoundError,
    DocumentNotSoftDeletedError,
    FileStorageError,
)
from ..models.chat_message import ChatMessage
from ..models.document import Document
from ..schemas.document_schemas import DocumentListResponse, DocumentResponse, DocumentSummaryResponse
from ..services.file_validation_service import validate_upload_file
from ..services.quota_service import ensure_quota_available, get_storage_quota_summary
from ..services.storage_service import (
    build_storage_path,
    delete_file_from_disk,
    read_file_bytes,
    save_file_bytes,
)

logger = logging.getLogger("services.document")
logger.setLevel(logging.DEBUG)


def _to_document_response(document: Document) -> DocumentResponse:
    """
    Convert a SQLAlchemy Document model into an API response schema.

    Args:
        document: ORM document instance.

    Returns:
        DocumentResponse: Serialized document metadata.
    """
    return DocumentResponse(
        id=document.id,
        filename=document.original_filename,
        mime_type=document.mime_type,
        size_bytes=document.size_bytes,
        processing_status=document.processing_status,
        document_summary=document.document_summary,
        processing_error=document.processing_error,
        processed_at=document.processed_at,
        is_deleted=document.is_deleted,
        deleted_at=document.deleted_at,
        created_at=document.created_at,
        updated_at=document.updated_at,
    )


def _generate_stored_filename(original_filename: str) -> str:
    """
    Generate a unique stored filename while preserving the original extension.

    Args:
        original_filename: Sanitized client filename.

    Returns:
        str: Unique filename safe for disk storage.
    """
    extension = Path(original_filename).suffix.lower()
    stored_filename = f"{uuid.uuid4().hex}{extension}"
    logger.debug(
        "Generated stored filename: original=%s, stored=%s",
        original_filename,
        stored_filename,
    )
    return stored_filename


async def _get_user_document(
    db: AsyncSession,
    user_id: int,
    document_id: int,
) -> Document:
    """
    Fetch a document owned by the given user.

    Args:
        db: Async SQLAlchemy session.
        user_id: Authenticated user identifier.
        document_id: Requested document identifier.

    Returns:
        Document: Matching ORM instance.

    Raises:
        DocumentNotFoundError: If the document does not exist for the user.
        DatabaseOperationError: If the lookup query fails.
    """
    logger.debug(
        "Fetching document_id=%s for user_id=%s",
        document_id,
        user_id,
    )
    try:
        stmt = select(Document).where(
            Document.id == document_id,
            Document.user_id == user_id,
        )
        result = await db.execute(stmt)
        document = result.scalar_one_or_none()
    except SQLAlchemyError as exc:
        logger.error(
            "Database error fetching document_id=%s for user_id=%s: %s",
            document_id,
            user_id,
            exc,
        )
        raise DatabaseOperationError("Failed to retrieve document.") from exc

    if document is None:
        logger.warning(
            "Document not found: document_id=%s, user_id=%s",
            document_id,
            user_id,
        )
        raise DocumentNotFoundError(
            f"Document with id {document_id} was not found."
        )

    return document


async def upload_document(
    db: AsyncSession,
    user_id: int,
    file: UploadFile,
) -> DocumentResponse:
    """
    Validate, store, and persist a new user document.

    Args:
        db: Async SQLAlchemy session.
        user_id: Authenticated user identifier.
        file: Uploaded file from the HTTP request.

    Returns:
        DocumentResponse: Metadata for the newly created document.

    Raises:
        UnsupportedFileTypeError: If validation fails.
        FileSizeExceededError: If the file exceeds per-upload limits.
        StorageQuotaExceededError: If the user quota would be exceeded.
        FileStorageError: If saving to disk fails.
        DatabaseOperationError: If persisting metadata fails.
    """
    logger.info("Starting document upload for user_id=%s, filename=%s", user_id, file.filename)

    content = await file.read()
    file_size = len(content)
    safe_filename = await validate_upload_file(file, file_size)
    await ensure_quota_available(db, user_id, file_size)

    stored_filename = _generate_stored_filename(safe_filename)
    file_path = build_storage_path(user_id, stored_filename)

    try:
        save_file_bytes(file_path, content)
    except FileStorageError:
        raise
    finally:
        await file.close()

    document = Document(
        user_id=user_id,
        original_filename=safe_filename,
        stored_filename=stored_filename,
        file_path=str(file_path),
        mime_type=(file.content_type or "application/octet-stream").split(";")[0].strip().lower(),
        size_bytes=file_size,
        processing_status="uploaded",
        is_deleted=False,
    )

    try:
        db.add(document)
        await db.commit()
        await db.refresh(document)
        logger.info(
            "Document persisted: id=%s, user_id=%s, filename=%s",
            document.id,
            user_id,
            safe_filename,
        )
    except SQLAlchemyError as exc:
        await db.rollback()
        logger.error(
            "Database commit failed for upload user_id=%s. Rolling back disk write.",
            user_id,
        )
        delete_file_from_disk(file_path)
        raise DatabaseOperationError(
            "Failed to save document metadata after upload."
        ) from exc

    return _to_document_response(document)


async def list_user_documents(
    db: AsyncSession,
    user_id: int,
    include_deleted: bool = False,
) -> DocumentListResponse:
    """
    List documents for a user, optionally including soft-deleted items.

    Args:
        db: Async SQLAlchemy session.
        user_id: Authenticated user identifier.
        include_deleted: Whether to include documents in the trash.

    Returns:
        DocumentListResponse: Documents plus storage quota summary.
    """
    logger.info(
        "Listing documents for user_id=%s, include_deleted=%s",
        user_id,
        include_deleted,
    )

    try:
        stmt = select(Document).where(Document.user_id == user_id)
        if not include_deleted:
            stmt = stmt.where(Document.is_deleted.is_(False))
        stmt = stmt.order_by(Document.created_at.desc())

        result = await db.execute(stmt)
        documents = result.scalars().all()
    except SQLAlchemyError as exc:
        logger.error("Failed to list documents for user_id=%s: %s", user_id, exc)
        raise DatabaseOperationError("Failed to list documents.") from exc

    storage = await get_storage_quota_summary(db, user_id)
    response = DocumentListResponse(
        documents=[_to_document_response(doc) for doc in documents],
        total_count=len(documents),
        storage=storage,
    )
    logger.info(
        "Listed %s documents for user_id=%s",
        response.total_count,
        user_id,
    )
    return response


async def get_document_metadata(
    db: AsyncSession,
    user_id: int,
    document_id: int,
) -> DocumentResponse:
    """
    Retrieve metadata for a single user-owned document.

    Args:
        db: Async SQLAlchemy session.
        user_id: Authenticated user identifier.
        document_id: Requested document identifier.

    Returns:
        DocumentResponse: Serialized document metadata.
    """
    document = await _get_user_document(db, user_id, document_id)
    logger.info("Retrieved metadata for document_id=%s", document_id)
    return _to_document_response(document)


async def get_document_download(
    db: AsyncSession,
    user_id: int,
    document_id: int,
) -> tuple[bytes, DocumentResponse]:
    """
    Load a document's bytes from disk along with its metadata.

    Args:
        db: Async SQLAlchemy session.
        user_id: Authenticated user identifier.
        document_id: Requested document identifier.

    Returns:
        tuple[bytes, DocumentResponse]: File bytes and metadata.

    Raises:
        DocumentNotFoundError: If the document does not exist.
        FileStorageError: If the file cannot be read from disk.
    """
    document = await _get_user_document(db, user_id, document_id)

    if document.is_deleted:
        logger.warning(
            "Download blocked for soft-deleted document_id=%s",
            document_id,
        )
        raise DocumentNotFoundError(
            "Document is in the trash. Restore is not yet supported; permanently delete or re-upload."
        )

    content = read_file_bytes(Path(document.file_path))
    logger.info("Prepared download for document_id=%s", document_id)
    return content, _to_document_response(document)


async def soft_delete_document(
    db: AsyncSession,
    user_id: int,
    document_id: int,
) -> DocumentResponse:
    """
    Soft-delete a document by marking it deleted without removing disk data.

    Args:
        db: Async SQLAlchemy session.
        user_id: Authenticated user identifier.
        document_id: Document to soft-delete.

    Returns:
        DocumentResponse: Updated document metadata.

    Raises:
        DocumentAlreadyDeletedError: If the document is already soft-deleted.
    """
    document = await _get_user_document(db, user_id, document_id)

    if document.is_deleted:
        logger.warning("Soft delete requested for already deleted document_id=%s", document_id)
        raise DocumentAlreadyDeletedError()

    document.is_deleted = True
    document.deleted_at = datetime.now(timezone.utc)

    try:
        await db.commit()
        await db.refresh(document)
        logger.info("Soft deleted document_id=%s for user_id=%s", document_id, user_id)
    except SQLAlchemyError as exc:
        await db.rollback()
        logger.error("Failed to soft delete document_id=%s: %s", document_id, exc)
        raise DatabaseOperationError("Failed to soft delete document.") from exc

    return _to_document_response(document)


async def get_document_summary(
    db: AsyncSession,
    user_id: int,
    document_id: int,
) -> DocumentSummaryResponse:
    """
    Retrieve the summarized text for a processed document.

    Args:
        db: Async SQLAlchemy session.
        user_id: Authenticated user identifier.
        document_id: Requested document identifier.

    Returns:
        DocumentSummaryResponse: Summary payload and processing status.
    """
    document = await _get_user_document(db, user_id, document_id)
    logger.info("Retrieved summary metadata for document_id=%s", document_id)
    return DocumentSummaryResponse(
        document_id=document.id,
        filename=document.original_filename,
        processing_status=document.processing_status,
        document_summary=document.document_summary,
        processing_error=document.processing_error,
        processed_at=document.processed_at,
    )


async def permanently_delete_document(
    db: AsyncSession,
    user_id: int,
    document_id: int,
) -> None:
    """
    Permanently delete a document after it has been soft-deleted.

    This removes both the database record and the file from disk.

    Args:
        db: Async SQLAlchemy session.
        user_id: Authenticated user identifier.
        document_id: Document to permanently delete.

    Raises:
        DocumentNotSoftDeletedError: If the document has not been soft-deleted first.
    """
    document = await _get_user_document(db, user_id, document_id)

    if not document.is_deleted:
        logger.warning(
            "Permanent delete blocked for active document_id=%s",
            document_id,
        )
        raise DocumentNotSoftDeletedError()

    file_path = Path(document.file_path)

    try:
        # Delete chat rows first so SQLAlchemy never tries to NULL document_id
        # on related messages (NOT NULL + FK CASCADE conflict).
        chat_delete_result = await db.execute(
            delete(ChatMessage).where(ChatMessage.document_id == document_id)
        )
        logger.info(
            "Deleted %s chat message(s) for document_id=%s before permanent delete",
            chat_delete_result.rowcount,
            document_id,
        )

        await db.delete(document)
        await db.commit()
        logger.info(
            "Permanently deleted document record document_id=%s for user_id=%s",
            document_id,
            user_id,
        )
    except SQLAlchemyError as exc:
        await db.rollback()
        logger.error(
            "Failed to permanently delete document_id=%s from database: %s",
            document_id,
            exc,
        )
        raise DatabaseOperationError(
            "Failed to permanently delete document metadata."
        ) from exc

    try:
        delete_file_from_disk(file_path)
    except FileStorageError as exc:
        # Metadata is already removed; log loudly but do not roll back DB state.
        logger.error(
            "Document record deleted but disk cleanup failed for document_id=%s: %s",
            document_id,
            exc,
        )
        raise

    logger.info(
        "Permanent deletion completed for document_id=%s, user_id=%s",
        document_id,
        user_id,
    )
