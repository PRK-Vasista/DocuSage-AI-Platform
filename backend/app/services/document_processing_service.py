"""
Background document processing service for DocuSage.

Orchestrates text extraction and summarization after upload, updating document
status transitions: uploaded -> processing -> ready/failed.
"""

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
)
from ..core.exceptions import DocumentProcessingError, TextExtractionError, SummarizationError
from ..database import AsyncSessionLocal
from ..models.document import Document
from ..services.summarization_service import summarize_document_text
from ..services.text_extraction_service import extract_text_from_file

logger = logging.getLogger("services.document_processing")
logger.setLevel(logging.DEBUG)


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
    )

    try:
        extracted_text = extract_text_from_file(
            file_path=Path(document.file_path),
            mime_type=document.mime_type,
            original_filename=document.original_filename,
        )
        summary_text = summarize_document_text(extracted_text)

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
        logger.error(
            "Background processing failed for document_id=%s: %s",
            document_id,
            exc.message,
        )
        await _update_document_processing_state(
            db,
            document,
            status=PROCESSING_STATUS_FAILED,
            summary=None,
            error_message=exc.message,
            mark_processed=True,
        )
    except Exception as exc:
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
            error_message="Unexpected error during document processing.",
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
