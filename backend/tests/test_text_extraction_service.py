"""
Unit tests for text extraction service.
"""

from pathlib import Path

import pytest

from app.services.text_extraction_service import extract_text_from_file


def test_extract_text_from_plain_file(tmp_path: Path):
    """Plain text files should be extracted successfully."""
    file_path = tmp_path / "sample.txt"
    file_path.write_text("DocuSage plain text extraction test.", encoding="utf-8")

    extracted = extract_text_from_file(
        file_path=file_path,
        mime_type="text/plain",
        original_filename="sample.txt",
    )

    assert "DocuSage plain text extraction test." in extracted


def test_extract_text_truncates_at_five_mb_limit(monkeypatch, tmp_path: Path):
    """Raw extraction must be capped at the configured 5 MB limit."""
    from app.core.config import app_settings

    monkeypatch.setattr(app_settings, "MAX_EXTRACTED_TEXT_BYTES", 20)

    file_path = tmp_path / "large.txt"
    file_path.write_text("a" * 100, encoding="utf-8")

    extracted = extract_text_from_file(
        file_path=file_path,
        mime_type="text/plain",
        original_filename="large.txt",
    )

    assert len(extracted.encode("utf-8")) <= 20
