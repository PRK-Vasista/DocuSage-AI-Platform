# This is Copyright of DocuSage 2026 Owner Rohith Kumar Vasista P.

"""
File validation service.

Validates uploaded files against DocuSage business rules for MIME type,
extension, and per-file size limits.
"""

import logging
from pathlib import Path

from fastapi import UploadFile

from ..core.config import (
    ALLOWED_EXTENSIONS,
    ALLOWED_MIME_TYPES,
    TEXT_MIME_PREFIX,
    app_settings,
)
from ..core.exceptions import FileSizeExceededError, UnsupportedFileTypeError

logger = logging.getLogger("services.file_validation")


def _sanitize_filename(filename: str | None) -> str:
    """
    Sanitize a client-provided filename to prevent path traversal.

    Args:
        filename: Raw filename from the upload request.

    Returns:
        str: Safe filename with directory separators removed.

    Raises:
        UnsupportedFileTypeError: If the filename is missing or empty.
    """
    if not filename or not filename.strip():
        logger.warning("Upload rejected: missing filename.")
        raise UnsupportedFileTypeError("Filename is required.")

    safe_name = filename.replace("/", "_").replace("\\", "_").strip()
    logger.debug("Sanitized filename: raw=%s, safe=%s", filename, safe_name)
    return safe_name


def _is_allowed_mime_type(content_type: str | None) -> bool:
    """
    Determine whether a MIME type is allowed for upload.

    Args:
        content_type: MIME type reported by the client/browser.

    Returns:
        bool: True if the MIME type is allowed.
    """
    if not content_type:
        logger.debug("MIME type missing from upload request.")
        return False

    normalized = content_type.split(";")[0].strip().lower()
    if normalized in ALLOWED_MIME_TYPES:
        return True
    if normalized.startswith(TEXT_MIME_PREFIX):
        logger.debug("MIME type accepted via text/* rule: %s", normalized)
        return True
    return False


def _is_allowed_extension(filename: str) -> bool:
    """
    Determine whether a filename extension is allowed.

    Args:
        filename: Sanitized filename.

    Returns:
        bool: True if the extension is allowed.
    """
    extension = Path(filename).suffix.lower()
    allowed = extension in ALLOWED_EXTENSIONS
    logger.debug("Extension check for %s -> %s (%s)", filename, extension, allowed)
    return allowed


async def validate_upload_file(file: UploadFile, file_size_bytes: int) -> str:
    """
    Validate an uploaded file against all file-level business rules.

    Args:
        file: FastAPI UploadFile instance.
        file_size_bytes: Size of the uploaded content in bytes.

    Returns:
        str: Sanitized filename safe for storage.

    Raises:
        UnsupportedFileTypeError: If MIME type or extension is not allowed.
        FileSizeExceededError: If the file exceeds the per-upload size limit.
    """
    logger.info(
        "Validating upload: filename=%s, content_type=%s, size=%s bytes",
        file.filename,
        file.content_type,
        file_size_bytes,
    )

    safe_filename = _sanitize_filename(file.filename)

    if file_size_bytes <= 0:
        logger.warning("Upload rejected: empty file content for %s", safe_filename)
        raise UnsupportedFileTypeError("Uploaded file is empty.")

    if file_size_bytes > app_settings.MAX_FILE_SIZE_BYTES:
        logger.warning(
            "Upload rejected: file size %s exceeds limit %s",
            file_size_bytes,
            app_settings.MAX_FILE_SIZE_BYTES,
        )
        raise FileSizeExceededError(
            f"File exceeds the maximum upload size of "
            f"{app_settings.MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB."
        )

    if not _is_allowed_mime_type(file.content_type):
        logger.warning(
            "Upload rejected: unsupported MIME type %s for file %s",
            file.content_type,
            safe_filename,
        )
        raise UnsupportedFileTypeError(
            f"Unsupported file type: {file.content_type}. "
            "Only text-based files, PDF, DOCX, and Markdown are allowed."
        )

    if not _is_allowed_extension(safe_filename):
        logger.warning(
            "Upload rejected: unsupported extension for file %s",
            safe_filename,
        )
        raise UnsupportedFileTypeError(
            f"Unsupported file extension for '{safe_filename}'. "
            f"Allowed extensions: {', '.join(sorted(ALLOWED_EXTENSIONS))}."
        )

    logger.info("Upload validation passed for file %s", safe_filename)
    return safe_filename
