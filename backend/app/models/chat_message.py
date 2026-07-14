# This is Copyright of DocuSage 2026 Owner Rohith Kumar Vasista P.

"""
Chat message ORM model for per-document conversations.
"""

import logging
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

logger = logging.getLogger("models.chat_message")


class ChatMessage(Base):
    """
    A single chat turn between a user and the assistant for one document.

    Attributes:
        id: Primary key.
        document_id: Target document foreign key.
        user_id: Owner foreign key.
        role: Message role (`user` or `assistant`).
        content: Message text.
        created_at: Timestamp when the message was stored.
    """

    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    document_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("documents.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    document = relationship(
        "Document",
        backref="chat_messages",
        passive_deletes=True,
    )
    user = relationship("User", backref="chat_messages")

    def __repr__(self) -> str:
        """Return a debug-friendly representation of the chat message."""
        return (
            f"ChatMessage(id={self.id!r}, document_id={self.document_id!r}, "
            f"role={self.role!r})"
        )
