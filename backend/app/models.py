import logging
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, Text
from .database import Base

# Set up logging for this module (primarily for debugging model loading if needed)
logger = logging.getLogger("models")
logger.setLevel(logging.DEBUG) 

# --- SQLAlchemy ORM Models (Table Definitions) ---

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    # WARNING: Password hash is stored as Text for length flexibility.
    password_hash: Mapped[str] = mapped_column(Text)
    
    def __repr__(self) -> str:
        """Helper for debugging to show object state."""
        # Logs when a User object is represented, useful for tracking loaded objects
        logger.debug(f"Representing User object with email: {self.email!r}")
        return f"User(id={self.id!r}, email={self.email!r})"
