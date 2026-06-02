"""
Authentication-related Pydantic schemas.
"""

import logging
from typing import Optional

from pydantic import BaseModel, EmailStr

logger = logging.getLogger("schemas.auth")
logger.setLevel(logging.INFO)


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
