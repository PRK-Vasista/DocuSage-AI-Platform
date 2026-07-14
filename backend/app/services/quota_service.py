# This is Copyright of DocuSage 2026 Owner Rohith Kumar Vasista P.

"""
Storage quota service.

Calculates and enforces the per-user total storage limit.
"""

import logging

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import app_settings
from ..core.exceptions import DatabaseOperationError, StorageQuotaExceededError
from ..models.document import Document
from ..schemas.document_schemas import StorageQuotaResponse

logger = logging.getLogger("services.quota")


async def get_user_storage_usage(db: AsyncSession, user_id: int) -> int:
    """
    Calculate total storage used by a user's active (non-deleted) documents.

    Args:
        db: Async SQLAlchemy session.
        user_id: Owner user identifier.

    Returns:
        int: Total bytes used by active documents.

    Raises:
        DatabaseOperationError: If the aggregate query fails.
    """
    logger.debug("Calculating storage usage for user_id=%s", user_id)
    try:
        stmt = select(func.coalesce(func.sum(Document.size_bytes), 0)).where(
            Document.user_id == user_id,
            Document.is_deleted.is_(False),
        )
        result = await db.execute(stmt)
        used_bytes = int(result.scalar_one())
        logger.info("Storage usage for user_id=%s: %s bytes", user_id, used_bytes)
        return used_bytes
    except SQLAlchemyError as exc:
        logger.error(
            "Failed to calculate storage usage for user_id=%s: %s",
            user_id,
            exc,
        )
        raise DatabaseOperationError(
            "Failed to calculate user storage usage."
        ) from exc


async def get_storage_quota_summary(
    db: AsyncSession,
    user_id: int,
) -> StorageQuotaResponse:
    """
    Build a storage quota summary for API responses.

    Args:
        db: Async SQLAlchemy session.
        user_id: Owner user identifier.

    Returns:
        StorageQuotaResponse: Used, limit, and remaining bytes.
    """
    used_bytes = await get_user_storage_usage(db, user_id)
    limit_bytes = app_settings.MAX_USER_STORAGE_BYTES
    remaining_bytes = max(limit_bytes - used_bytes, 0)
    logger.debug(
        "Quota summary for user_id=%s: used=%s, limit=%s, remaining=%s",
        user_id,
        used_bytes,
        limit_bytes,
        remaining_bytes,
    )
    return StorageQuotaResponse(
        used_bytes=used_bytes,
        limit_bytes=limit_bytes,
        remaining_bytes=remaining_bytes,
    )


async def ensure_quota_available(
    db: AsyncSession,
    user_id: int,
    incoming_file_size: int,
) -> None:
    """
    Ensure the user has enough remaining quota for a new upload.

    Args:
        db: Async SQLAlchemy session.
        user_id: Owner user identifier.
        incoming_file_size: Size of the incoming upload in bytes.

    Raises:
        StorageQuotaExceededError: If the upload would exceed the user quota.
        DatabaseOperationError: If usage calculation fails.
    """
    used_bytes = await get_user_storage_usage(db, user_id)
    projected_total = used_bytes + incoming_file_size
    logger.debug(
        "Quota check for user_id=%s: used=%s, incoming=%s, projected=%s, limit=%s",
        user_id,
        used_bytes,
        incoming_file_size,
        projected_total,
        app_settings.MAX_USER_STORAGE_BYTES,
    )

    if projected_total > app_settings.MAX_USER_STORAGE_BYTES:
        remaining_bytes = max(app_settings.MAX_USER_STORAGE_BYTES - used_bytes, 0)
        logger.warning(
            "Quota exceeded for user_id=%s: projected=%s, limit=%s",
            user_id,
            projected_total,
            app_settings.MAX_USER_STORAGE_BYTES,
        )
        raise StorageQuotaExceededError(
            "Upload would exceed your 1 GB storage quota. "
            f"Remaining space: {remaining_bytes} bytes."
        )

    logger.info("Quota check passed for user_id=%s", user_id)
