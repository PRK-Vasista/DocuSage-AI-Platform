"""
Unit tests for document summarization service.
"""

import pytest

from app.core.config import app_settings
from app.services.summarization_service import summarize_document_text


def test_summarize_short_document_returns_full_text():
    """Short documents should be stored as a condensed full-text summary."""
    text = "DocuSage helps users upload and summarize documents securely."
    summary = summarize_document_text(text)
    assert summary == text


def test_summarize_long_document_returns_shorter_summary():
    """Long documents should produce a shorter extractive summary."""
    sentences = [
        f"This is sentence number {index} about document processing and analysis."
        for index in range(1, 120)
    ]
    full_text = " ".join(sentences)
    assert len(full_text) > app_settings.SUMMARY_TARGET_CHAR_COUNT

    summary = summarize_document_text(full_text)

    assert len(summary) < len(full_text)
    assert "document processing" in summary.lower()


def test_summarize_enforces_one_mb_storage_limit(monkeypatch):
    """Summary output must respect the 1 MB stored summary byte limit."""
    monkeypatch.setattr(app_settings, "MAX_STORED_SUMMARY_BYTES", 100)
    monkeypatch.setattr(app_settings, "SUMMARY_TARGET_CHAR_COUNT", 50)

    text = "Alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu."
    summary = summarize_document_text(text)
    assert len(summary.encode("utf-8")) <= 100


def test_summarize_empty_text_raises():
    """Empty extracted text must raise a summarization error."""
    with pytest.raises(Exception):
        summarize_document_text("   ")
