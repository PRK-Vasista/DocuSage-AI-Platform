"""
Filesystem storage service.

Handles low-level read/write/delete operations for uploaded documents.
"""

import logging
from pathlib import Path

from ..core.config import app_settings
from ..core.exceptions import FileStorageError

logger = logging.getLogger("services.storage")
logger.setLevel(logging.DEBUG)


def get_upload_root() -> Path:
    """
    Resolve and ensure the root upload directory exists.

    Returns:
        Path: Root directory for all user uploads.
    """
    upload_root = Path(app_settings.UPLOAD_DIR)
    upload_root.mkdir(parents=True, exist_ok=True)
    logger.debug("Upload root verified at %s", upload_root)
    return upload_root


def get_user_upload_directory(user_id: int) -> Path:
    """
    Resolve and ensure a user's upload directory exists.

    Args:
        user_id: Owner user identifier.

    Returns:
        Path: Directory dedicated to the user's files.
    """
    user_dir = get_upload_root() / str(user_id)
    user_dir.mkdir(parents=True, exist_ok=True)
    logger.debug("User upload directory verified: %s", user_dir)
    return user_dir


def build_storage_path(user_id: int, stored_filename: str) -> Path:
    """
    Build the full filesystem path for a stored document.

    Args:
        user_id: Owner user identifier.
        stored_filename: Sanitized filename used on disk.

    Returns:
        Path: Absolute path where the file should be stored.
    """
    path = get_user_upload_directory(user_id) / stored_filename
    logger.debug("Built storage path for user_id=%s: %s", user_id, path)
    return path


def save_file_bytes(file_path: Path, content: bytes) -> None:
    """
    Persist raw file bytes to disk.

    Args:
        file_path: Destination path.
        content: File bytes to write.

    Raises:
        FileStorageError: If writing to disk fails.
    """
    logger.info("Saving file to disk: %s (%s bytes)", file_path, len(content))
    try:
        file_path.write_bytes(content)
        logger.info("File saved successfully: %s", file_path)
    except OSError as exc:
        logger.error("Failed to save file %s: %s", file_path, exc)
        raise FileStorageError(f"Could not save file to {file_path}.") from exc


def read_file_bytes(file_path: Path) -> bytes:
    """
    Read file bytes from disk.

    Args:
        file_path: Source path.

    Returns:
        bytes: File content.

    Raises:
        FileStorageError: If reading from disk fails.
    """
    logger.debug("Reading file from disk: %s", file_path)
    try:
        if not file_path.exists():
            logger.error("File not found on disk: %s", file_path)
            raise FileStorageError(f"File not found at {file_path}.")
        content = file_path.read_bytes()
        logger.debug("Read %s bytes from %s", len(content), file_path)
        return content
    except OSError as exc:
        logger.error("Failed to read file %s: %s", file_path, exc)
        raise FileStorageError(f"Could not read file from {file_path}.") from exc


def delete_file_from_disk(file_path: Path) -> None:
    """
    Permanently delete a file from disk if it exists.

    Args:
        file_path: Path to the file that should be removed.

    Raises:
        FileStorageError: If deletion fails unexpectedly.
    """
    logger.info("Deleting file from disk: %s", file_path)
    try:
        if file_path.exists():
            file_path.unlink()
            logger.info("File deleted from disk: %s", file_path)
        else:
            logger.warning("File already absent on disk: %s", file_path)
    except OSError as exc:
        logger.error("Failed to delete file %s: %s", file_path, exc)
        raise FileStorageError(f"Could not delete file at {file_path}.") from exc
