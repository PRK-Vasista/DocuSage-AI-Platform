# This is Copyright of DocuSage 2026 Owner Rohith Kumar Vasista P.

"""
Password reset token ORM model.
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class PasswordResetToken(Base):
    """
    One-time token used for forgot-password reset flows.

    Attributes:
        id: Primary key.
        user_id: Owning user.
        token_hash: SHA-256 hash of the raw token sent to the user.
        expires_at: Expiry timestamp (UTC).
        used_at: When the token was consumed (null if unused).
        created_at: Creation timestamp (UTC).
    """

    __tablename__ = "password_reset_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
