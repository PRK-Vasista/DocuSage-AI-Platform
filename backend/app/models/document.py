"""
Document ORM model.

Represents a user-uploaded file and its metadata persisted in PostgreSQL.
"""

import logging
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

logger = logging.getLogger("models.document")
logger.setLevel(logging.DEBUG)


class Document(Base):
    """
    Metadata record for an uploaded document.

    The binary content is stored on the filesystem; this table tracks ownership,
    size, MIME type, lifecycle state, and soft-delete status.

    Attributes:
        id: Primary key.
        user_id: Owner foreign key referencing `users.id`.
        original_filename: Filename provided by the client at upload time.
        stored_filename: Sanitized filename used on disk.
        file_path: Absolute or relative path to the stored file.
        mime_type: Detected or reported MIME type.
        size_bytes: File size in bytes.
        processing_status: Pipeline state (uploaded, processing, ready, failed).
        document_summary: Summarized representation of the document (max 1 MB).
        processing_error: Error detail when processing_status is failed.
        processed_at: Timestamp when processing completed or failed.
        is_deleted: Soft-delete flag.
        deleted_at: Timestamp when the document was soft-deleted.
        created_at: Upload timestamp.
        updated_at: Last metadata update timestamp.
    """

    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    original_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(255), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    processing_status: Mapped[str] = mapped_column(
        String(50),
        default="uploaded",
        nullable=False,
    )
    document_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    processing_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user = relationship("User", backref="documents")

    def __repr__(self) -> str:
        """Return a debug-friendly representation of the document."""
        logger.debug(
            "Representing Document id=%s, filename=%s, is_deleted=%s",
            self.id,
            self.original_filename,
            self.is_deleted,
        )
        return (
            f"Document(id={self.id!r}, user_id={self.user_id!r}, "
            f"filename={self.original_filename!r}, is_deleted={self.is_deleted!r})"
        )
