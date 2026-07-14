# This is Copyright of DocuSage 2026 Owner Rohith Kumar Vasista P.

"""
Authentication-related Pydantic schemas.
"""

import logging
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

logger = logging.getLogger("schemas.auth")


class UserCreate(BaseModel):
    """Schema for user registration and login payloads."""

    email: EmailStr
    password: str

    def __init__(self, **data):
        super().__init__(**data)
        logger.debug("Validated UserCreate schema for email: %s", self.email)


class Token(BaseModel):
    """Schema for JWT access token responses."""

    access_token: str
    token_type: str = "bearer"

    def __init__(self, **data):
        super().__init__(**data)
        logger.debug("Token response schema created.")


class TokenData(BaseModel):
    """Schema for decoded JWT payload data exposed by protected routes."""

    email: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    """Authenticated password change payload."""

    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)


class ForgotPasswordRequest(BaseModel):
    """Forgot-password request payload."""

    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Reset-password request payload."""

    token: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)


class MessageResponse(BaseModel):
    """Generic success message response."""

    message: str
