# This is Copyright of DocuSage 2026 Owner Rohith Kumar Vasista P.

"""
Document chat orchestration service.

Persists conversation history and delegates inference to the isolated AI unit.
"""

import logging

from sqlalchemy import delete, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import PROCESSING_STATUS_READY, app_settings
from ..core.exceptions import (
    ChatError,
    DatabaseOperationError,
    DocumentNotFoundError,
    DocumentNotReadyError,
    DocuSageError,
)
from ..models.chat_message import ChatMessage
from ..models.document import Document
from ..schemas.chat_schemas import ChatAskResponse, ChatHistoryResponse, ChatMessageResponse
from ..services.ai_client_service import request_document_chat

logger = logging.getLogger("services.chat")


async def _get_owned_document(
    db: AsyncSession,
    user_id: int,
    document_id: int,
) -> Document:
    """
    Load a non-deleted document owned by the authenticated user.

    Args:
        db: Async SQLAlchemy session.
        user_id: Authenticated user id.
        document_id: Target document id.

    Returns:
        Document: Owned document ORM instance.

    Raises:
        DocumentNotFoundError: If the document is missing, deleted, or not owned.
        DatabaseOperationError: If the query fails.
    """
    try:
        stmt = select(Document).where(
            Document.id == document_id,
            Document.user_id == user_id,
            Document.is_deleted.is_(False),
        )
        result = await db.execute(stmt)
        document = result.scalar_one_or_none()
    except SQLAlchemyError as exc:
        logger.error("Failed to load document_id=%s for chat: %s", document_id, exc)
        raise DatabaseOperationError("Failed to load document for chat.") from exc

    if document is None:
        raise DocumentNotFoundError()
    return document


def _to_message_response(message: ChatMessage) -> ChatMessageResponse:
    """
    Convert an ORM chat message to an API response model.

    Args:
        message: ChatMessage ORM instance.

    Returns:
        ChatMessageResponse: API-facing message payload.
    """
    return ChatMessageResponse(
        id=message.id,
        role=message.role,  # type: ignore[arg-type]
        content=message.content,
        created_at=message.created_at,
    )


async def get_chat_history(
    db: AsyncSession,
    user_id: int,
    document_id: int,
) -> ChatHistoryResponse:
    """
    Return chat history for a user-owned document.

    Args:
        db: Async SQLAlchemy session.
        user_id: Authenticated user id.
        document_id: Target document id.

    Returns:
        ChatHistoryResponse: Ordered conversation history.
    """
    await _get_owned_document(db, user_id, document_id)

    try:
        stmt = (
            select(ChatMessage)
            .where(
                ChatMessage.document_id == document_id,
                ChatMessage.user_id == user_id,
            )
            .order_by(ChatMessage.created_at.asc(), ChatMessage.id.asc())
        )
        result = await db.execute(stmt)
        messages = list(result.scalars().all())
    except SQLAlchemyError as exc:
        logger.error("Failed to load chat history for document_id=%s: %s", document_id, exc)
        raise DatabaseOperationError("Failed to load chat history.") from exc

    logger.info(
        "Loaded chat history for document_id=%s user_id=%s count=%s",
        document_id,
        user_id,
        len(messages),
    )
    return ChatHistoryResponse(
        document_id=document_id,
        messages=[_to_message_response(message) for message in messages],
    )


async def _prune_old_chat_messages(
    db: AsyncSession,
    user_id: int,
    document_id: int,
) -> None:
    """
    Keep only the newest CHAT_HISTORY_LIMIT messages for a document.

    Older turns are deleted so chat storage stays bounded without loading the
    full conversation into the LLM context window.

    Args:
        db: Async SQLAlchemy session.
        user_id: Authenticated user id.
        document_id: Target document id.
    """
    keep_limit = app_settings.CHAT_HISTORY_LIMIT
    try:
        stmt = (
            select(ChatMessage.id)
            .where(
                ChatMessage.document_id == document_id,
                ChatMessage.user_id == user_id,
            )
            .order_by(ChatMessage.created_at.desc(), ChatMessage.id.desc())
        )
        result = await db.execute(stmt)
        message_ids = list(result.scalars().all())
    except SQLAlchemyError as exc:
        logger.error(
            "Failed to inspect chat history for pruning document_id=%s: %s",
            document_id,
            exc,
        )
        raise DatabaseOperationError("Failed to prune chat history.") from exc

    if len(message_ids) <= keep_limit:
        return

    ids_to_delete = message_ids[keep_limit:]
    try:
        await db.execute(delete(ChatMessage).where(ChatMessage.id.in_(ids_to_delete)))
        await db.commit()
        logger.info(
            "Pruned %s old chat message(s) for document_id=%s (kept=%s)",
            len(ids_to_delete),
            document_id,
            keep_limit,
        )
    except SQLAlchemyError as exc:
        await db.rollback()
        logger.error(
            "Failed to prune chat messages for document_id=%s: %s",
            document_id,
            exc,
        )
        raise DatabaseOperationError("Failed to prune chat history.") from exc


async def ask_document_question(
    db: AsyncSession,
    user_id: int,
    document_id: int,
    question: str,
) -> ChatAskResponse:
    """
    Ask a question about a ready document and persist the conversation turn.

    Args:
        db: Async SQLAlchemy session.
        user_id: Authenticated user id.
        document_id: Target document id.
        question: User question text.

    Returns:
        ChatAskResponse: Answer plus updated history.

    Raises:
        DocumentNotReadyError: If processing has not completed.
        AIServiceClientError: If the AI unit fails.
        ChatError: If persistence fails after inference.
    """
    cleaned_question = question.strip()
    if not cleaned_question:
        raise DocuSageError("Chat question cannot be empty.", status_code=400)

    document = await _get_owned_document(db, user_id, document_id)

    if document.processing_status != PROCESSING_STATUS_READY:
        raise DocumentNotReadyError(
            f"Document status is '{document.processing_status}'. Wait until it is ready."
        )

    if not document.document_summary:
        raise DocumentNotReadyError("Document summary is missing; chat is unavailable.")

    history_response = await get_chat_history(db, user_id, document_id)
    history_payload = [
        {"role": message.role, "content": message.content}
        for message in history_response.messages[-app_settings.CHAT_HISTORY_LIMIT :]
    ]

    answer = await request_document_chat(
        question=cleaned_question,
        document_context=document.document_summary,
        history=history_payload,
    )

    user_message = ChatMessage(
        document_id=document_id,
        user_id=user_id,
        role="user",
        content=cleaned_question,
    )
    assistant_message = ChatMessage(
        document_id=document_id,
        user_id=user_id,
        role="assistant",
        content=answer,
    )

    try:
        db.add(user_message)
        db.add(assistant_message)
        await db.commit()
        await db.refresh(user_message)
        await db.refresh(assistant_message)
    except SQLAlchemyError as exc:
        await db.rollback()
        logger.error("Failed to persist chat turn for document_id=%s: %s", document_id, exc)
        raise ChatError("Failed to save chat messages.") from exc

    await _prune_old_chat_messages(db, user_id, document_id)

    updated_history = await get_chat_history(db, user_id, document_id)
    logger.info(
        "Chat turn completed for document_id=%s user_id=%s",
        document_id,
        user_id,
    )
    return ChatAskResponse(
        document_id=document_id,
        question=cleaned_question,
        answer=answer,
        messages=updated_history.messages,
    )
