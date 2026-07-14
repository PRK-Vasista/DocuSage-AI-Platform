# This is Copyright of DocuSage 2026 Owner Rohith Kumar Vasista P.

"""
Document-related Pydantic schemas.
"""

import logging
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger("schemas.document")


class DocumentResponse(BaseModel):
    """Public metadata returned for a single document."""

    id: int = Field(..., description="Unique document identifier.")
    filename: str = Field(..., description="Original uploaded filename.")
    mime_type: str = Field(..., description="Detected MIME type.")
    size_bytes: int = Field(..., description="File size in bytes.")
    processing_status: str = Field(..., description="Processing pipeline status.")
    document_summary: Optional[str] = Field(
        None,
        description="Summarized document text (available when status is ready).",
    )
    processing_error: Optional[str] = Field(
        None,
        description="Processing failure detail (available when status is failed).",
    )
    processed_at: Optional[datetime] = Field(
        None,
        description="Timestamp when processing completed or failed.",
    )
    is_deleted: bool = Field(..., description="Whether the document is soft-deleted.")
    deleted_at: Optional[datetime] = Field(None, description="Soft-delete timestamp.")
    created_at: datetime = Field(..., description="Upload timestamp.")
    updated_at: datetime = Field(..., description="Last metadata update timestamp.")

    class Config:
        """Pydantic model configuration."""
        from_attributes = True


class StorageQuotaResponse(BaseModel):
    """Storage usage summary for the authenticated user."""

    used_bytes: int = Field(..., description="Total bytes currently used by active documents.")
    limit_bytes: int = Field(..., description="Maximum allowed storage per user.")
    remaining_bytes: int = Field(..., description="Remaining storage capacity.")


class DocumentListResponse(BaseModel):
    """Paginated-like list wrapper for user documents."""

    documents: List[DocumentResponse] = Field(default_factory=list)
    total_count: int = Field(..., description="Number of documents returned.")
    storage: StorageQuotaResponse = Field(..., description="Current storage usage.")


class DocumentDeleteResponse(BaseModel):
    """Response returned after soft or permanent deletion."""

    message: str = Field(..., description="Human-readable deletion result.")
    document_id: int = Field(..., description="Affected document identifier.")
    deletion_type: str = Field(..., description="Either 'soft' or 'permanent'.")


class DocumentSummaryResponse(BaseModel):
    """Response returned for a document summary request."""

    document_id: int = Field(..., description="Document identifier.")
    filename: str = Field(..., description="Original uploaded filename.")
    processing_status: str = Field(..., description="Current processing status.")
    document_summary: Optional[str] = Field(
        None,
        description="Summarized document text when processing is complete.",
    )
    processing_error: Optional[str] = Field(
        None,
        description="Processing error detail when status is failed.",
    )
    processed_at: Optional[datetime] = Field(
        None,
        description="Timestamp when processing completed or failed.",
    )
