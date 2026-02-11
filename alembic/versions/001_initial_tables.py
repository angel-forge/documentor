"""initial tables

Revision ID: 001
Revises:
Create Date: 2026-02-11

"""

from typing import Sequence, Union

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "documents",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("source_type", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("chunk_count", sa.Integer(), default=0),
    )

    op.create_table(
        "chunks",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column(
            "document_id", sa.String(), sa.ForeignKey("documents.id"), nullable=False
        ),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("embedding", Vector(1536), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("chunks")
    op.drop_table("documents")
