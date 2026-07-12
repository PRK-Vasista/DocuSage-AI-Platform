"""Add chat_messages table for per-document AI chat.

Revision ID: 0003_chat_messages
Revises: 0002_doc_processing
Create Date: 2026-07-12

Creates the chat_messages table used by the backend to persist single-document
conversations. Table creation is skipped if it already exists (idempotent).
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "0003_chat_messages"
down_revision: Union[str, None] = "0002_doc_processing"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(table_name: str) -> bool:
    """
    Check whether a table already exists.

    Args:
        table_name: Database table name.

    Returns:
        bool: True when the table is already present.
    """
    bind = op.get_bind()
    inspector = inspect(bind)
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    """Create the chat_messages table when missing."""
    if _table_exists("chat_messages"):
        return

    op.create_table(
        "chat_messages",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_chat_messages_id", "chat_messages", ["id"])
    op.create_index("ix_chat_messages_document_id", "chat_messages", ["document_id"])
    op.create_index("ix_chat_messages_user_id", "chat_messages", ["user_id"])


def downgrade() -> None:
    """Drop the chat_messages table when present."""
    if not _table_exists("chat_messages"):
        return

    op.drop_index("ix_chat_messages_user_id", table_name="chat_messages")
    op.drop_index("ix_chat_messages_document_id", table_name="chat_messages")
    op.drop_index("ix_chat_messages_id", table_name="chat_messages")
    op.drop_table("chat_messages")
