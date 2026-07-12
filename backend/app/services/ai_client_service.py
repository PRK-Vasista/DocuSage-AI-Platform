"""
HTTP client for the isolated DocuSage AI service unit.

The main backend never talks to Ollama directly. All summarization and chat
requests go through this thin client to `ai-service`.
"""

import logging
from typing import Any

import httpx

from ..core.config import app_settings
from ..core.exceptions import AIServiceClientError, SummarizationError

logger = logging.getLogger("services.ai_client")
logger.setLevel(logging.DEBUG)


def _ai_base_url() -> str:
    """
    Build the AI service API base URL.

    Returns:
        str: Absolute base URL for AI endpoints.
    """
    return f"{app_settings.AI_SERVICE_URL.rstrip('/')}/api/v1/ai"


async def request_document_summary(text: str, max_chars: int | None = None) -> str:
    """
    Ask the AI service to summarize document text.

    Args:
        text: Extracted document text.
        max_chars: Optional max summary length hint.

    Returns:
        str: Generated summary text.

    Raises:
        AIServiceClientError: If the AI service is unreachable or returns an error.
        SummarizationError: If the AI service returns an empty summary.
    """
    if not app_settings.AI_SERVICE_ENABLED:
        logger.warning("AI service disabled by configuration.")
        raise AIServiceClientError("AI service is disabled.")

    payload: dict[str, Any] = {"text": text}
    if max_chars is not None:
        payload["max_chars"] = max_chars

    url = f"{_ai_base_url()}/summarize"
    logger.info("Calling AI service summarize: url=%s text_chars=%s", url, len(text))

    try:
        async with httpx.AsyncClient(timeout=app_settings.AI_SERVICE_TIMEOUT_SECONDS) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
    except httpx.RequestError as exc:
        logger.error("AI service summarize unreachable: %s", exc)
        raise AIServiceClientError("AI service is unavailable for summarization.") from exc
    except httpx.HTTPStatusError as exc:
        detail = ""
        try:
            detail = exc.response.json().get("detail", "")
        except Exception:
            detail = exc.response.text
        logger.error("AI service summarize failed: status=%s detail=%s", exc.response.status_code, detail)
        raise AIServiceClientError(
            detail or "AI service summarization request failed."
        ) from exc

    summary = (data.get("summary") or "").strip()
    if not summary:
        raise SummarizationError("AI service returned an empty summary.")

    logger.info("AI service summarize succeeded: summary_chars=%s", len(summary))
    return summary


async def request_document_chat(
    *,
    question: str,
    document_context: str,
    history: list[dict[str, str]] | None = None,
) -> str:
    """
    Ask the AI service a document-grounded chat question.

    Args:
        question: User question.
        document_context: Document summary/context.
        history: Optional prior role/content turns.

    Returns:
        str: Assistant answer.

    Raises:
        AIServiceClientError: If the AI service call fails.
    """
    if not app_settings.AI_SERVICE_ENABLED:
        logger.warning("AI service disabled by configuration.")
        raise AIServiceClientError("AI service is disabled.")

    url = f"{_ai_base_url()}/chat"
    payload = {
        "question": question,
        "document_context": document_context,
        "history": history or [],
    }
    logger.info(
        "Calling AI service chat: question_chars=%s history=%s",
        len(question),
        len(history or []),
    )

    try:
        async with httpx.AsyncClient(timeout=app_settings.AI_SERVICE_TIMEOUT_SECONDS) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
    except httpx.RequestError as exc:
        logger.error("AI service chat unreachable: %s", exc)
        raise AIServiceClientError("AI service is unavailable for chat.") from exc
    except httpx.HTTPStatusError as exc:
        detail = ""
        try:
            detail = exc.response.json().get("detail", "")
        except Exception:
            detail = exc.response.text
        logger.error("AI service chat failed: status=%s detail=%s", exc.response.status_code, detail)
        raise AIServiceClientError(detail or "AI service chat request failed.") from exc

    answer = (data.get("answer") or "").strip()
    if not answer:
        raise AIServiceClientError("AI service returned an empty chat answer.")

    logger.info("AI service chat succeeded: answer_chars=%s", len(answer))
    return answer
