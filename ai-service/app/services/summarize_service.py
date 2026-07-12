"""
Document summarization orchestration for the AI service unit.
"""

import logging

from ..core.config import ai_settings
from ..core.exceptions import InvalidAIRequestError
from ..services.ollama_client import generate_completion

logger = logging.getLogger("ai_service.summarize")
logger.setLevel(logging.DEBUG)


def _truncate_context(text: str) -> str:
    """
    Truncate document text to the configured context window.

    Args:
        text: Raw document text.

    Returns:
        str: Truncated text safe for local model context.
    """
    if len(text) <= ai_settings.MAX_CONTEXT_CHARS:
        return text
    logger.warning(
        "Document context truncated for summarization: original=%s limit=%s",
        len(text),
        ai_settings.MAX_CONTEXT_CHARS,
    )
    return text[: ai_settings.MAX_CONTEXT_CHARS]


async def summarize_text(text: str, max_chars: int | None = None) -> str:
    """
    Generate an overall-document summary via Ollama.

    Args:
        text: Extracted document text.
        max_chars: Optional maximum summary length.

    Returns:
        str: Generated summary text.

    Raises:
        InvalidAIRequestError: If input text is empty.
    """
    cleaned = text.strip()
    if not cleaned:
        raise InvalidAIRequestError("Cannot summarize empty document text.")

    target_chars = max_chars or ai_settings.MAX_SUMMARY_CHARS
    context = _truncate_context(cleaned)

    prompt = (
        "You are DocuSage, a careful document assistant.\n"
        "Summarize the following document as a clear overview of the whole document.\n"
        f"Keep the summary under {target_chars} characters.\n"
        "Do not invent facts that are not present in the document.\n\n"
        f"DOCUMENT:\n{context}\n\n"
        "SUMMARY:"
    )

    logger.info("Starting AI summarization: input_chars=%s", len(cleaned))
    summary = await generate_completion(prompt)
    if len(summary) > target_chars:
        summary = summary[:target_chars].rsplit(" ", 1)[0] + "..."
        logger.warning("AI summary truncated to max_chars=%s", target_chars)

    logger.info("AI summarization complete: summary_chars=%s", len(summary))
    return summary
