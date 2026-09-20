# This is Copyright of DocuSage 2026 Owner Rohith Kumar Vasista P.

"""
Background document processing service for DocuSage.

Orchestrates text extraction and summarization after upload, updating document
status transitions: uploaded -> processing -> ready/failed.
"""

import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import (
    PROCESSING_STATUS_FAILED,
    PROCESSING_STATUS_PROCESSING,
    PROCESSING_STATUS_READY,
    PROCESSING_STATUS_UPLOADED,
    app_settings,
)
from ..core.exceptions import (
    AIServiceClientError,
    DocumentNotFoundError,
    DocumentProcessingError,
    SummarizationError,
    TextExtractionError,
)
from ..database import AsyncSessionLocal
from ..models.document import Document
from ..services.ai_client_service import request_document_summary
from ..services.summarization_service import summarize_document_text
from ..services.text_extraction_service import extract_text_from_file

logger = logging.getLogger("services.document_processing")


def _format_processing_error(exc: Exception) -> str:
    """
    Build a clear user-facing processing_error string.

    Args:
        exc: Caught exception from the processing pipeline.

    Returns:
        str: Concise failure reason for the UI.
    """
    if isinstance(exc, TextExtractionError):
        return f"Text extraction failed: {exc.message}"
    if isinstance(exc, SummarizationError):
        return f"Summarization failed: {exc.message}"
    if isinstance(exc, AIServiceClientError):
        return f"AI service unavailable: {exc.message}"
    if isinstance(exc, DocumentProcessingError):
        return f"Processing could not finish: {exc.message}"
    return "Unexpected error during document processing."


async def _summarize_with_ai_or_fallback(extracted_text: str) -> str:
    """
    Prefer the isolated AI unit for summarization; fall back to extractive.

    Retries transient AI failures a few times with short backoff before
    extractive fallback (when enabled) or raising SummarizationError.

    Args:
        extracted_text: Extracted document text (already size-capped).

    Returns:
        str: Summary text to persist.

    Raises:
        SummarizationError: If AI and extractive summarization both fail
            (or fallback is disabled).
    """
    attempts = max(1, int(app_settings.AI_SUMMARIZE_MAX_ATTEMPTS))
    delay = float(app_settings.AI_SUMMARIZE_RETRY_SECONDS)
    last_error: Exception | None = None

    for attempt in range(1, attempts + 1):
        try:
            summary = await request_document_summary(
                extracted_text,
                max_chars=app_settings.SUMMARY_TARGET_CHAR_COUNT,
            )
            encoded = summary.encode("utf-8")
            if len(encoded) > app_settings.MAX_STORED_SUMMARY_BYTES:
                summary = encoded[: app_settings.MAX_STORED_SUMMARY_BYTES].decode(
                    "utf-8",
                    errors="ignore",
                )
                logger.warning("AI summary truncated to 1 MB storage limit.")
            if not summary.strip():
                raise SummarizationError("AI service returned an empty summary.")
            if attempt > 1:
                logger.info(
                    "AI summarization succeeded on attempt %s/%s",
                    attempt,
                    attempts,
                )
            return summary
        except (AIServiceClientError, SummarizationError) as exc:
            last_error = exc
            logger.warning(
                "AI summarization attempt %s/%s failed: %s",
                attempt,
                attempts,
                getattr(exc, "message", exc),
            )
            if attempt < attempts:
                await asyncio.sleep(delay)

    if not app_settings.AI_FALLBACK_TO_EXTRACTIVE:
        logger.error("AI summarization failed and fallback is disabled.")
        raise SummarizationError(
            str(getattr(last_error, "message", last_error) or "AI summarization failed.")
        )

    logger.warning(
        "AI summarization unavailable after %s attempts. Falling back to extractive summary.",
        attempts,
    )
    try:
        return summarize_document_text(extracted_text)
    except SummarizationError:
        raise
    except Exception as exc:
        raise SummarizationError(
            f"Extractive fallback failed after AI retries: {exc}"
        ) from exc


async def _update_document_processing_state(
    db: AsyncSession,
    document: Document,
    *,
    status: str,
    summary: str | None = None,
    error_message: str | None = None,
    mark_processed: bool = False,
) -> None:
    """
    Persist processing status and optional summary/error fields.

    Args:
        db: Async SQLAlchemy session.
        document: Target document ORM instance.
        status: New processing status value.
        summary: Optional summarized text to store.
        error_message: Optional processing error detail.
        mark_processed: Whether to set processed_at timestamp.

    Raises:
        DocumentProcessingError: If the database commit fails.
    """
    document.processing_status = status
    document.document_summary = summary
    document.processing_error = error_message
    if mark_processed:
        document.processed_at = datetime.now(timezone.utc)

    try:
        await db.commit()
        await db.refresh(document)
        logger.info(
            "Updated processing state for document_id=%s: status=%s",
            document.id,
            status,
        )
    except SQLAlchemyError as exc:
        await db.rollback()
        logger.error(
            "Failed to update processing state for document_id=%s: %s",
            document.id,
            exc,
        )
        raise DocumentProcessingError(
            "Failed to persist document processing state."
        ) from exc


async def _run_document_processing(db: AsyncSession, document_id: int) -> None:
    """
    Execute extraction and summarization for one document within an open session.

    Args:
        db: Active async SQLAlchemy session.
        document_id: Identifier of the uploaded document to process.
    """
    try:
        stmt = select(Document).where(Document.id == document_id)
        result = await db.execute(stmt)
        document = result.scalar_one_or_none()
    except SQLAlchemyError as exc:
        logger.critical(
            "Failed to load document_id=%s for background processing: %s",
            document_id,
            exc,
        )
        return

    if document is None:
        logger.error("Background processing aborted: document_id=%s not found", document_id)
        return

    if document.is_deleted:
        logger.warning(
            "Background processing skipped for soft-deleted document_id=%s",
            document_id,
        )
        return

    await _update_document_processing_state(
        db,
        document,
        status=PROCESSING_STATUS_PROCESSING,
        summary=None,
        error_message=None,
    )

    try:
        extracted_text = extract_text_from_file(
            file_path=Path(document.file_path),
            mime_type=document.mime_type,
            original_filename=document.original_filename,
        )
        if not extracted_text or not extracted_text.strip():
            raise TextExtractionError("Extracted text was empty.")

        summary_text = await _summarize_with_ai_or_fallback(extracted_text)

        await _update_document_processing_state(
            db,
            document,
            status=PROCESSING_STATUS_READY,
            summary=summary_text,
            error_message=None,
            mark_processed=True,
        )
        logger.info(
            "Background processing completed for document_id=%s, summary_chars=%s",
            document_id,
            len(summary_text),
        )
    except (TextExtractionError, SummarizationError, DocumentProcessingError) as exc:
        error_message = _format_processing_error(exc)
        logger.error(
            "Background processing failed for document_id=%s: %s",
            document_id,
            error_message,
        )
        await _update_document_processing_state(
            db,
            document,
            status=PROCESSING_STATUS_FAILED,
            summary=None,
            error_message=error_message,
            mark_processed=True,
        )
    except Exception as exc:
        error_message = _format_processing_error(exc)
        logger.critical(
            "Unexpected background processing failure for document_id=%s: %s",
            document_id,
            exc,
        )
        await _update_document_processing_state(
            db,
            document,
            status=PROCESSING_STATUS_FAILED,
            summary=None,
            error_message=error_message,
            mark_processed=True,
        )


async def process_document_by_id(document_id: int, db: AsyncSession | None = None) -> None:
    """
    Run the full extraction and summarization pipeline for one document.

    When called from FastAPI BackgroundTasks, opens its own database session
    independent from the request lifecycle. Tests may pass an existing session.

    Args:
        document_id: Identifier of the uploaded document to process.
        db: Optional async session (used in tests); otherwise a new session is opened.
    """
    logger.info("Background processing started for document_id=%s", document_id)

    if db is not None:
        await _run_document_processing(db, document_id)
        return

    async with AsyncSessionLocal() as session:
        await _run_document_processing(session, document_id)


async def queue_reprocess_for_user(
    db: AsyncSession,
    *,
    user_id: int,
    document_id: int,
) -> Document:
    """
    Validate ownership and mark a failed (or stuck) document for reprocessing.

    Args:
        db: Async SQLAlchemy session.
        user_id: Authenticated owner.
        document_id: Document to retry.

    Returns:
        Document: ORM row after status reset to uploaded (queued).

    Raises:
        DocumentNotFoundError: Missing, deleted, or not owned.
        DocumentProcessingError: If status is not eligible for retry.
    """
    try:
        stmt = select(Document).where(
            Document.id == document_id,
            Document.user_id == user_id,
        )
        result = await db.execute(stmt)
        document = result.scalar_one_or_none()
    except SQLAlchemyError as exc:
        raise DocumentProcessingError("Could not load document for retry.") from exc

    if document is None or document.is_deleted:
        raise DocumentNotFoundError()

    if document.processing_status not in {
        PROCESSING_STATUS_FAILED,
        PROCESSING_STATUS_UPLOADED,
    }:
        raise DocumentProcessingError(
            "Only failed (or not-yet-started) documents can be retried. "
            f"Current status: {document.processing_status}.",
            status_code=409,
        )

    await _update_document_processing_state(
        db,
        document,
        status=PROCESSING_STATUS_UPLOADED,
        summary=None,
        error_message=None,
        mark_processed=False,
    )
    logger.info(
        "Queued reprocess for document_id=%s user_id=%s",
        document_id,
        user_id,
    )
    return document
