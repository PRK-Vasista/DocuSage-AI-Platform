# This is Copyright of DocuSage 2026 Owner Rohith Kumar Vasista P.

"""
Document-grounded chat orchestration for the AI service unit.
"""

import logging

from ..core.config import ai_settings
from ..core.exceptions import InvalidAIRequestError
from ..schemas.ai_schemas import ChatMessage
from ..services.ollama_client import generate_chat

logger = logging.getLogger("ai_service.chat")


def _truncate_context(text: str) -> str:
    """
    Truncate document context for local model limits.

    Args:
        text: Document summary/context text.

    Returns:
        str: Truncated context.
    """
    if len(text) <= ai_settings.MAX_CONTEXT_CHARS:
        return text
    logger.warning(
        "Document context truncated for chat: original=%s limit=%s",
        len(text),
        ai_settings.MAX_CONTEXT_CHARS,
    )
    return text[: ai_settings.MAX_CONTEXT_CHARS]


async def answer_question(
    question: str,
    document_context: str,
    history: list[ChatMessage] | None = None,
) -> str:
    """
    Answer a user question using document context via Ollama chat.

    Args:
        question: User question.
        document_context: Document summary used to ground answers.
        history: Optional prior conversation turns.

    Returns:
        str: Assistant answer text.

    Raises:
        InvalidAIRequestError: If question or context is empty.
    """
    cleaned_question = question.strip()
    cleaned_context = document_context.strip()

    if not cleaned_question:
        raise InvalidAIRequestError("Chat question cannot be empty.")
    if not cleaned_context:
        raise InvalidAIRequestError("Document context is required for chat.")

    system_prompt = (
        "You are DocuSage, a helpful assistant that answers questions using only "
        "the provided document context. If the answer is not in the context, say so "
        "clearly. Keep answers concise and factual.\n\n"
        f"DOCUMENT CONTEXT:\n{_truncate_context(cleaned_context)}"
    )

    messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]

    for turn in history or []:
        messages.append({"role": turn.role, "content": turn.content})

    messages.append({"role": "user", "content": cleaned_question})

    logger.info(
        "Starting AI chat: question_chars=%s history_turns=%s",
        len(cleaned_question),
        len(history or []),
    )
    answer = await generate_chat(messages)
    logger.info("AI chat complete: answer_chars=%s", len(answer))
    return answer
