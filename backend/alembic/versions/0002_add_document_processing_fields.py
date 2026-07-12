"""Add document processing and summary fields.

Revision ID: 0002_doc_processing
Revises: 0001_initial_schema
Create Date: 2026-06-03

Adds columns for summarized document text, processing errors, and completion time.
Existing columns are detected and skipped safely for idempotent upgrades.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "0002_doc_processing"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(table_name: str, column_name: str) -> bool:
    """
    Check whether a column already exists on a table.

    Args:
        table_name: Database table name.
        column_name: Column name to inspect.

    Returns:
        bool: True when the column is already present.
    """
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = {column["name"] for column in inspector.get_columns(table_name)}
    return column_name in columns


def upgrade() -> None:
    """Add processing summary columns to the documents table when missing."""
    if not _column_exists("documents", "document_summary"):
        op.add_column("documents", sa.Column("document_summary", sa.Text(), nullable=True))

    if not _column_exists("documents", "processing_error"):
        op.add_column("documents", sa.Column("processing_error", sa.Text(), nullable=True))

    if not _column_exists("documents", "processed_at"):
        op.add_column(
            "documents",
            sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        )


def downgrade() -> None:
    """Remove processing summary columns from the documents table."""
    if _column_exists("documents", "processed_at"):
        op.drop_column("documents", "processed_at")

    if _column_exists("documents", "processing_error"):
        op.drop_column("documents", "processing_error")

    if _column_exists("documents", "document_summary"):
        op.drop_column("documents", "document_summary")
