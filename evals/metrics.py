# This is Copyright of DocuSage 2026 Owner Rohith Kumar Vasista P.

"""
Lexical evaluation proxies for summary-grounded Q&A (stdlib only).

These are honest engineering proxies — not formal NLI faithfulness scores.
"""

from __future__ import annotations

import re
from statistics import median
from typing import Iterable, Sequence

_TOKEN_RE = re.compile(r"[a-z0-9@.]+", re.IGNORECASE)

_ABSTENTION_MARKERS = (
    "not in the document",
    "not mentioned",
    "don't know",
    "do not know",
    "doesn't say",
    "does not say",
    "no information",
    "cannot find",
    "can't find",
    "not provided",
    "insufficient",
    "i don't have",
    "not available in",
    "based on the document",
)


def tokenize(text: str) -> set[str]:
    """Lowercase alphanumeric tokens (keeps emails/domains loosely)."""
    return {m.group(0).lower() for m in _TOKEN_RE.finditer(text or "")}


def token_overlap_ratio(answer: str, context: str) -> float:
    """
    Fraction of answer tokens that also appear in context.

    Empty answers score 0. Answers whose tokens are all stop-ish short noise
    still compute normally; callers decide thresholds.
    """
    answer_tokens = tokenize(answer)
    if not answer_tokens:
        return 0.0
    context_tokens = tokenize(context)
    if not context_tokens:
        return 0.0
    overlap = answer_tokens & context_tokens
    return len(overlap) / len(answer_tokens)


def looks_like_abstention(answer: str) -> bool:
    """Heuristic: answer admits the document does not contain the info."""
    lowered = (answer or "").lower()
    return any(marker in lowered for marker in _ABSTENTION_MARKERS)


def keyword_hit(answer: str, must_include_any: Sequence[str]) -> bool:
    """True if answer contains at least one required keyword/phrase."""
    if not must_include_any:
        return True
    lowered = (answer or "").lower()
    return any(token.lower() in lowered for token in must_include_any)


def percentile(values: Sequence[float], p: float) -> float:
    """Nearest-rank style percentile for small samples."""
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return float(ordered[0])
    rank = (len(ordered) - 1) * (p / 100.0)
    low = int(rank)
    high = min(low + 1, len(ordered) - 1)
    weight = rank - low
    return float(ordered[low] * (1 - weight) + ordered[high] * weight)


def summarize_latencies(duration_ms_list: Iterable[float]) -> dict[str, float]:
    """Return count, p50, p95, mean for latency samples."""
    samples = [float(x) for x in duration_ms_list]
    if not samples:
        return {"count": 0, "p50_ms": 0.0, "p95_ms": 0.0, "mean_ms": 0.0}
    return {
        "count": len(samples),
        "p50_ms": round(percentile(samples, 50), 2),
        "p95_ms": round(percentile(samples, 95), 2),
        "mean_ms": round(sum(samples) / len(samples), 2),
        "median_ms": round(float(median(samples)), 2),
    }


def score_item(
    *,
    answerable: bool,
    answer: str,
    context: str,
    must_include_any: Sequence[str],
    groundedness_threshold: float = 0.35,
) -> dict:
    """
    Score one Q&A turn.

    Answerable items: groundedness = overlap with context; keyword hit optional.
    Unanswerable items: success if abstention-like reply.
    """
    overlap = token_overlap_ratio(answer, context)
    abstained = looks_like_abstention(answer)
    keywords_ok = keyword_hit(answer, must_include_any)

    if answerable:
        grounded = overlap >= groundedness_threshold
        success = grounded and keywords_ok
        return {
            "success": success,
            "grounded": grounded,
            "abstained": abstained,
            "keywords_ok": keywords_ok,
            "overlap": round(overlap, 4),
            "kind": "answerable",
        }

    success = abstained
    return {
        "success": success,
        "grounded": overlap >= groundedness_threshold,
        "abstained": abstained,
        "keywords_ok": True,
        "overlap": round(overlap, 4),
        "kind": "unanswerable",
    }
