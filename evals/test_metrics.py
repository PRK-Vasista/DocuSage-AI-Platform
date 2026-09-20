# This is Copyright of DocuSage 2026 Owner Rohith Kumar Vasista P.

"""Unit tests for eval metric helpers (no Ollama)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from metrics import (  # noqa: E402
    keyword_hit,
    looks_like_abstention,
    percentile,
    score_item,
    summarize_latencies,
    token_overlap_ratio,
)


def test_token_overlap_high_when_answer_from_context():
    context = "Tomatoes need six hours of sun and well-drained soil."
    answer = "Tomatoes need six hours of sun."
    assert token_overlap_ratio(answer, context) >= 0.8


def test_token_overlap_low_when_invented():
    context = "Basil prefers warm nights."
    answer = "Quantum routers require liquid nitrogen cooling."
    assert token_overlap_ratio(answer, context) < 0.35


def test_abstention_detection():
    assert looks_like_abstention("I don't know based on the document.")
    assert not looks_like_abstention("Tomatoes need six hours of sun.")


def test_keyword_hit():
    assert keyword_hit("Archive keeps files for seven years.", ["seven", "7"])
    assert not keyword_hit("Files are kept forever.", ["seven", "7"])


def test_score_answerable_success():
    result = score_item(
        answerable=True,
        answer="Intake accepts PDF and DOCX uploads only.",
        context="Intake accepts PDF and DOCX uploads only. Review assigns owners.",
        must_include_any=["pdf", "docx"],
    )
    assert result["success"] is True
    assert result["grounded"] is True


def test_score_unanswerable_needs_abstention():
    bad = score_item(
        answerable=False,
        answer="Atlas uses MongoDB in every region.",
        context="Project Atlas ships three modules.",
        must_include_any=[],
    )
    good = score_item(
        answerable=False,
        answer="That detail is not mentioned in the document.",
        context="Project Atlas ships three modules.",
        must_include_any=[],
    )
    assert bad["success"] is False
    assert good["success"] is True


def test_percentile_and_latency_summary():
    assert percentile([10, 20, 30, 40], 50) == pytest.approx(25.0)
    stats = summarize_latencies([10, 20, 30, 40, 50])
    assert stats["count"] == 5
    assert stats["p50_ms"] == pytest.approx(30.0)
