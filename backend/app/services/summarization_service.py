# This is Copyright of DocuSage 2026 Owner Rohith Kumar Vasista P.

"""
Document summarization service for DocuSage.

Provides a local extractive summarization fallback used when the isolated AI
unit (ai-service + Ollama) is unavailable. The stored summary is capped at
MAX_STORED_SUMMARY_BYTES (1 MB).
"""

import logging
import re
from collections import Counter

from ..core.config import app_settings
from ..core.exceptions import SummarizationError

logger = logging.getLogger("services.summarization")

_STOP_WORDS = frozenset({
    "a", "an", "the", "and", "or", "but", "if", "while", "with", "to", "of", "at",
    "by", "for", "in", "on", "is", "are", "was", "were", "be", "been", "being",
    "this", "that", "these", "those", "it", "its", "as", "from", "into", "about",
})


def _split_sentences(text: str) -> list[str]:
    """
    Split text into sentence-like chunks.

    Args:
        text: Input plain text.

    Returns:
        list[str]: Non-empty sentence chunks.
    """
    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized:
        return []

    parts = re.split(r"(?<=[.!?])\s+", normalized)
    return [part.strip() for part in parts if part.strip()]


def _score_sentences(sentences: list[str]) -> list[tuple[int, float]]:
    """
    Score sentences for extractive summarization.

    Args:
        sentences: Sentence chunks from the document.

    Returns:
        list[tuple[int, float]]: (index, score) pairs sorted by score descending.
    """
    word_counts = Counter()
    tokenized_sentences: list[list[str]] = []

    for sentence in sentences:
        tokens = [
            token.lower()
            for token in re.findall(r"[A-Za-z0-9']+", sentence)
            if token.lower() not in _STOP_WORDS
        ]
        tokenized_sentences.append(tokens)
        word_counts.update(tokens)

    scored: list[tuple[int, float]] = []
    for index, tokens in enumerate(tokenized_sentences):
        if not tokens:
            scored.append((index, 0.0))
            continue
        score = sum(word_counts[token] for token in tokens) / len(tokens)
        scored.append((index, score))

    scored.sort(key=lambda item: item[1], reverse=True)
    return scored


def _enforce_summary_limit(summary: str) -> str:
    """
    Ensure the summary does not exceed the stored summary byte limit.

    Args:
        summary: Generated summary text.

    Returns:
        str: Summary within MAX_STORED_SUMMARY_BYTES.

    Raises:
        SummarizationError: If the summary cannot be encoded.
    """
    try:
        encoded = summary.encode("utf-8")
    except UnicodeEncodeError as exc:
        logger.error("Summary encoding failed: %s", exc)
        raise SummarizationError("Failed to encode generated summary.") from exc

    if len(encoded) <= app_settings.MAX_STORED_SUMMARY_BYTES:
        return summary

    truncated = encoded[: app_settings.MAX_STORED_SUMMARY_BYTES].decode("utf-8", errors="ignore")
    logger.warning(
        "Summary truncated to byte limit: original=%s, limit=%s",
        len(encoded),
        app_settings.MAX_STORED_SUMMARY_BYTES,
    )
    return truncated


def summarize_document_text(full_text: str) -> str:
    """
    Generate an extractive summary representing the overall document.

    Args:
        full_text: Complete extracted document text (already capped at 5 MB).

    Returns:
        str: Summarized text capped at 1 MB for database storage.

    Raises:
        SummarizationError: If summarization fails or input is empty.
    """
    cleaned = full_text.strip()
    if not cleaned:
        logger.warning("Summarization rejected: empty extracted text.")
        raise SummarizationError("Cannot summarize an empty document.")

    logger.info("Starting extractive summarization for text length=%s chars", len(cleaned))

    if len(cleaned) <= app_settings.SUMMARY_TARGET_CHAR_COUNT:
        logger.info("Document is short; storing condensed full text as summary.")
        return _enforce_summary_limit(cleaned)

    sentences = _split_sentences(cleaned)
    if not sentences:
        logger.info("No sentence boundaries found; storing leading excerpt as summary.")
        excerpt = cleaned[: app_settings.SUMMARY_TARGET_CHAR_COUNT]
        return _enforce_summary_limit(excerpt)

    if len(sentences) == 1:
        return _enforce_summary_limit(sentences[0])

    scored = _score_sentences(sentences)
    sentence_count = len(sentences)
    summary_sentence_count = max(3, min(sentence_count, sentence_count // 3 or 1))

    selected_indexes = sorted(index for index, _ in scored[:summary_sentence_count])
    summary_parts = [sentences[index] for index in selected_indexes]

    summary = " ".join(summary_parts).strip()
    if len(summary) > app_settings.SUMMARY_TARGET_CHAR_COUNT:
        summary = summary[: app_settings.SUMMARY_TARGET_CHAR_COUNT].rsplit(" ", 1)[0] + "..."

    logger.info(
        "Summarization complete: input_chars=%s, summary_chars=%s, sentences_used=%s",
        len(cleaned),
        len(summary),
        len(summary_parts),
    )
    return _enforce_summary_limit(summary)
