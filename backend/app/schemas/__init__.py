# This is Copyright of DocuSage 2026 Owner Rohith Kumar Vasista P.

"""
Pydantic request/response schemas for DocuSage API endpoints.

Schemas are grouped by domain and re-exported from this package to keep router
imports concise and consistent.
"""

from .auth_schemas import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    MessageResponse,
    ResetPasswordRequest,
    Token,
    TokenData,
    UserCreate,
)
from .document_schemas import (
    DocumentDeleteResponse,
    DocumentListResponse,
    DocumentResponse,
    DocumentSummaryResponse,
    StorageQuotaResponse,
)

__all__ = [
    "UserCreate",
    "Token",
    "TokenData",
    "ChangePasswordRequest",
    "ForgotPasswordRequest",
    "ResetPasswordRequest",
    "MessageResponse",
    "DocumentResponse",
    "DocumentListResponse",
    "DocumentDeleteResponse",
    "DocumentSummaryResponse",
    "StorageQuotaResponse",
]
