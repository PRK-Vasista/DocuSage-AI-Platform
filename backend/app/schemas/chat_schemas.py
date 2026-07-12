"""
Chat-related Pydantic schemas.
"""

from datetime import datetime
from typing import List, Literal

from pydantic import BaseModel, Field


class ChatMessageResponse(BaseModel):
    """A persisted chat turn returned to the client."""

    id: int = Field(..., description="Chat message identifier.")
    role: Literal["user", "assistant"] = Field(..., description="Message author role.")
    content: str = Field(..., description="Message text.")
    created_at: datetime = Field(..., description="Message creation timestamp.")

    class Config:
        """Pydantic model configuration."""

        from_attributes = True


class ChatHistoryResponse(BaseModel):
    """Conversation history for a single document."""

    document_id: int = Field(..., description="Document identifier.")
    messages: List[ChatMessageResponse] = Field(default_factory=list)


class ChatAskRequest(BaseModel):
    """Request body for asking a question about a document."""

    question: str = Field(..., min_length=1, description="User question.")


class ChatAskResponse(BaseModel):
    """Response returned after a chat turn is completed."""

    document_id: int = Field(..., description="Document identifier.")
    question: str = Field(..., description="User question that was asked.")
    answer: str = Field(..., description="Assistant answer from the AI unit.")
    messages: List[ChatMessageResponse] = Field(
        default_factory=list,
        description="Updated conversation history including this turn.",
    )
