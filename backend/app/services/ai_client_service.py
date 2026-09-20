# This is Copyright of DocuSage 2026 Owner Rohith Kumar Vasista P.

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
from ..core.timing import duration_ms, monotonic_ms

logger = logging.getLogger("services.ai_client")


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
    started = monotonic_ms()
    logger.info(
        "op=ai_summarize event=start url=%s text_chars=%s",
        url,
        len(text),
    )

    try:
        async with httpx.AsyncClient(timeout=app_settings.AI_SERVICE_TIMEOUT_SECONDS) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
    except httpx.RequestError as exc:
        logger.error(
            "op=ai_summarize event=error outcome=unreachable duration_ms=%s error=%s",
            duration_ms(started),
            exc,
        )
        raise AIServiceClientError("AI service is unavailable for summarization.") from exc
    except httpx.HTTPStatusError as exc:
        detail = ""
        try:
            detail = exc.response.json().get("detail", "")
        except Exception:
            detail = exc.response.text
        logger.error(
            "op=ai_summarize event=error outcome=http_error duration_ms=%s status=%s detail=%s",
            duration_ms(started),
            exc.response.status_code,
            detail,
        )
        raise AIServiceClientError(
            detail or "AI service summarization request failed."
        ) from exc

    summary = (data.get("summary") or "").strip()
    if not summary:
        logger.error(
            "op=ai_summarize event=error outcome=empty_summary duration_ms=%s",
            duration_ms(started),
        )
        raise SummarizationError("AI service returned an empty summary.")

    logger.info(
        "op=ai_summarize event=success duration_ms=%s summary_chars=%s",
        duration_ms(started),
        len(summary),
    )
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
    started = monotonic_ms()
    logger.info(
        "op=ai_chat event=start question_chars=%s history=%s context_chars=%s",
        len(question),
        len(history or []),
        len(document_context or ""),
    )

    try:
        async with httpx.AsyncClient(timeout=app_settings.AI_SERVICE_TIMEOUT_SECONDS) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
    except httpx.RequestError as exc:
        logger.error(
            "op=ai_chat event=error outcome=unreachable duration_ms=%s error=%s",
            duration_ms(started),
            exc,
        )
        raise AIServiceClientError("AI service is unavailable for chat.") from exc
    except httpx.HTTPStatusError as exc:
        detail = ""
        try:
            detail = exc.response.json().get("detail", "")
        except Exception:
            detail = exc.response.text
        logger.error(
            "op=ai_chat event=error outcome=http_error duration_ms=%s status=%s detail=%s",
            duration_ms(started),
            exc.response.status_code,
            detail,
        )
        raise AIServiceClientError(detail or "AI service chat request failed.") from exc

    answer = (data.get("answer") or "").strip()
    if not answer:
        logger.error(
            "op=ai_chat event=error outcome=empty_answer duration_ms=%s",
            duration_ms(started),
        )
        raise AIServiceClientError("AI service returned an empty chat answer.")

    logger.info(
        "op=ai_chat event=success duration_ms=%s answer_chars=%s",
        duration_ms(started),
        len(answer),
    )
    return answer


async def check_ai_health() -> dict[str, Any]:
    """
    Fetch health status from the isolated AI service.

    Returns:
        dict: Parsed AI health payload (status, ollama_reachable, model, …).

    Raises:
        AIServiceClientError: If the AI service cannot be reached.
    """
    if not app_settings.AI_SERVICE_ENABLED:
        return {"status": "disabled", "ollama_reachable": False, "model": None}

    url = f"{_ai_base_url()}/health"
    started = monotonic_ms()
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            payload = response.json()
        logger.info(
            "op=ai_health event=success duration_ms=%s status=%s",
            duration_ms(started),
            payload.get("status"),
        )
        return payload
    except httpx.RequestError as exc:
        logger.warning(
            "op=ai_health event=error outcome=unreachable duration_ms=%s error=%s",
            duration_ms(started),
            exc,
        )
        raise AIServiceClientError("AI service health check failed.") from exc
    except httpx.HTTPStatusError as exc:
        logger.warning(
            "op=ai_health event=error outcome=http_error duration_ms=%s status=%s",
            duration_ms(started),
            exc.response.status_code,
        )
        raise AIServiceClientError("AI service health check failed.") from exc
