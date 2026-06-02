"""
Unit tests for file validation service rules.
"""

import pytest
from fastapi import UploadFile
from io import BytesIO

from app.core.exceptions import FileSizeExceededError, UnsupportedFileTypeError
from app.services.file_validation_service import validate_upload_file


class DummyUploadFile(UploadFile):
    """Minimal UploadFile test double with explicit filename and content type."""

    def __init__(self, filename: str, content_type: str):
        super().__init__(filename=filename, file=BytesIO(b"test"), headers={"content-type": content_type})
        self._content_type = content_type

    @property
    def content_type(self):
        return self._content_type


@pytest.mark.asyncio
async def test_validate_upload_file_accepts_markdown():
    """Markdown files with allowed MIME type and extension should pass validation."""
    upload = DummyUploadFile("notes.md", "text/markdown")
    safe_name = await validate_upload_file(upload, file_size_bytes=100)
    assert safe_name == "notes.md"


@pytest.mark.asyncio
async def test_validate_upload_file_rejects_binary_extension():
    """Non text-based extensions must be rejected even with a text MIME type."""
    upload = DummyUploadFile("archive.zip", "text/plain")
    with pytest.raises(UnsupportedFileTypeError):
        await validate_upload_file(upload, file_size_bytes=100)


@pytest.mark.asyncio
async def test_validate_upload_file_rejects_oversized_file():
    """Files above the per-upload limit must raise FileSizeExceededError."""
    upload = DummyUploadFile("large.txt", "text/plain")
    with pytest.raises(FileSizeExceededError):
        await validate_upload_file(upload, file_size_bytes=11 * 1024 * 1024)
