import logging
from pydantic import BaseModel, EmailStr
from typing import Optional

# Set up logging for this module
logger = logging.getLogger("schemas")
logger.setLevel(logging.INFO) 

# --- User Input Schemas ---
class UserCreate(BaseModel):
    """Schema for user registration and login data."""
    email: EmailStr
    password: str
    
    # Optional logging hook, primarily for debugging pydantic validation issues
    def __init__(self, **data):
        super().__init__(**data)
        logger.debug(f"Validated UserCreate schema for email: {self.email}")

# --- Token Response Schemas ---
class Token(BaseModel):
    """Schema for the JWT access token returned after successful authentication."""
    access_token: str
    token_type: str = "bearer"
    
    def __init__(self, **data):
        super().__init__(**data)
        logger.debug("Token object successfully created.")

# --- Token Data (Decoded Payload) Schema ---
class TokenData(BaseModel):
    """Schema to hold the decoded payload of a JWT."""
    # 'sub' claim from JWT payload (typically the user's email)
    email: Optional[str] = None

