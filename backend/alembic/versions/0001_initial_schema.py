"""Initial DocuSage schema for users and documents.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-06-03

This migration is idempotent for databases that were previously initialized
via SQLAlchemy create_all(). Existing tables are detected and skipped safely.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(table_name: str) -> bool:
    """
    Check whether a table already exists in the connected database.

    Args:
        table_name: Name of the table to inspect.

    Returns:
        bool: True when the table is already present.
    """
    bind = op.get_bind()
    inspector = inspect(bind)
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    """Create core DocuSage tables when they do not already exist."""
    if not _table_exists("users"):
        op.create_table(
            "users",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("email", sa.String(length=255), nullable=False),
            sa.Column("password_hash", sa.Text(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
        op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)

    if not _table_exists("documents"):
        op.create_table(
            "documents",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("original_filename", sa.String(length=512), nullable=False),
            sa.Column("stored_filename", sa.String(length=512), nullable=False),
            sa.Column("file_path", sa.Text(), nullable=False),
            sa.Column("mime_type", sa.String(length=255), nullable=False),
            sa.Column("size_bytes", sa.BigInteger(), nullable=False),
            sa.Column(
                "processing_status",
                sa.String(length=50),
                nullable=False,
                server_default="uploaded",
            ),
            sa.Column(
                "is_deleted",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            ),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_documents_id"), "documents", ["id"], unique=False)
        op.create_index(op.f("ix_documents_is_deleted"), "documents", ["is_deleted"], unique=False)
        op.create_index(op.f("ix_documents_user_id"), "documents", ["user_id"], unique=False)


def downgrade() -> None:
    """Drop DocuSage tables in reverse dependency order."""
    if _table_exists("documents"):
        op.drop_index(op.f("ix_documents_user_id"), table_name="documents")
        op.drop_index(op.f("ix_documents_is_deleted"), table_name="documents")
        op.drop_index(op.f("ix_documents_id"), table_name="documents")
        op.drop_table("documents")

    if _table_exists("users"):
        op.drop_index(op.f("ix_users_id"), table_name="users")
        op.drop_index(op.f("ix_users_email"), table_name="users")
        op.drop_table("users")
