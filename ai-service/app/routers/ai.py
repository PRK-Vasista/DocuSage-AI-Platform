"""
HTTP routes for the DocuSage AI service unit.
"""

import logging

from fastapi import APIRouter

from ..core.config import ai_settings
from ..core.exceptions import AIServiceError
from ..schemas.ai_schemas import (
    ChatRequest,
    ChatResponse,
    HealthResponse,
    SummarizeRequest,
    SummarizeResponse,
)
from ..services.chat_service import answer_question
from ..services.ollama_client import check_ollama_health
from ..services.summarize_service import summarize_text

router = APIRouter(tags=["AI"])
logger = logging.getLogger("ai_service.router")
logger.setLevel(logging.DEBUG)


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """
    Report AI service and Ollama connectivity status.

    Returns:
        HealthResponse: Health payload for orchestration checks.
    """
    ollama_ok = await check_ollama_health()
    return HealthResponse(
        status="ok" if ollama_ok else "degraded",
        ollama_reachable=ollama_ok,
        model=ai_settings.OLLAMA_MODEL,
    )


@router.post("/summarize", response_model=SummarizeResponse)
async def summarize(request: SummarizeRequest) -> SummarizeResponse:
    """
    Summarize document text using the local Ollama model.

    Args:
        request: Summarization request payload.

    Returns:
        SummarizeResponse: Generated summary.

    Raises:
        AIServiceError: Propagated domain failures from the AI pipeline.
    """
    logger.info("Summarize request received: text_chars=%s", len(request.text))
    try:
        summary = await summarize_text(request.text, max_chars=request.max_chars)
    except AIServiceError:
        raise
    return SummarizeResponse(summary=summary, model=ai_settings.OLLAMA_MODEL)


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Answer a document-grounded chat question using Ollama.

    Args:
        request: Chat request payload.

    Returns:
        ChatResponse: Assistant answer.

    Raises:
        AIServiceError: Propagated domain failures from the AI pipeline.
    """
    logger.info(
        "Chat request received: question_chars=%s history=%s",
        len(request.question),
        len(request.history),
    )
    try:
        answer = await answer_question(
            question=request.question,
            document_context=request.document_context,
            history=request.history,
        )
    except AIServiceError:
        raise
    return ChatResponse(answer=answer, model=ai_settings.OLLAMA_MODEL)
