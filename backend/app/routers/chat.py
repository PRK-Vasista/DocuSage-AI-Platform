# This is Copyright of DocuSage 2026 Owner Rohith Kumar Vasista P.

"""
Document chat API routes for DocuSage.

Frontend calls the main backend only. The backend proxies inference to the
isolated AI service unit.
"""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.exceptions import DocuSageError
from ..database import get_db
from ..dependencies.auth import AuthenticatedUser, get_current_user
from ..schemas.chat_schemas import ChatAskRequest, ChatAskResponse, ChatHistoryResponse
from ..services import chat_service

router = APIRouter(tags=["Chat"])
logger = logging.getLogger("chat_router")


@router.get("/{document_id}", response_model=ChatHistoryResponse)
async def get_document_chat_history(
    document_id: int,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ChatHistoryResponse:
    """
    Return chat history for a single document owned by the current user.

    Args:
        document_id: Target document identifier.
        current_user: Authenticated user dependency.
        db: Async SQLAlchemy session.

    Returns:
        ChatHistoryResponse: Conversation history payload.
    """
    logger.info(
        "Chat history request for document_id=%s by user_id=%s",
        document_id,
        current_user["id"],
    )
    try:
        return await chat_service.get_chat_history(
            db=db,
            user_id=current_user["id"],
            document_id=document_id,
        )
    except DocuSageError:
        raise


@router.post("/{document_id}", response_model=ChatAskResponse)
async def ask_document_chat(
    document_id: int,
    payload: ChatAskRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ChatAskResponse:
    """
    Ask a question about a ready document and return the AI answer.

    Args:
        document_id: Target document identifier.
        payload: Chat ask request body.
        current_user: Authenticated user dependency.
        db: Async SQLAlchemy session.

    Returns:
        ChatAskResponse: Answer and updated history.
    """
    logger.info(
        "Chat ask request for document_id=%s by user_id=%s",
        document_id,
        current_user["id"],
    )
    try:
        return await chat_service.ask_document_question(
            db=db,
            user_id=current_user["id"],
            document_id=document_id,
            question=payload.question,
        )
    except DocuSageError:
        raise
