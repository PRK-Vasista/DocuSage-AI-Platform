# This is Copyright of DocuSage 2026 Owner Rohith Kumar Vasista P.

"""
User ORM model.

Represents an authenticated DocuSage platform user.
"""

import logging

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base

logger = logging.getLogger("models.user")


class User(Base):
    """
    Application user account stored in the `users` table.

    Attributes:
        id: Primary key.
        email: Unique login identifier.
        password_hash: Argon2 password hash.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(Text)

    def __repr__(self) -> str:
        """Return a debug-friendly representation of the user."""
        logger.debug("Representing User object with email: %s", self.email)
        return f"User(id={self.id!r}, email={self.email!r})"
