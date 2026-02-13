"""add chunk indexes (document_id btree + embedding HNSW)

Revision ID: 003
Revises: 002
Create Date: 2026-02-13

"""

from typing import Sequence, Union

from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index("ix_chunks_document_id", "chunks", ["document_id"])
    op.execute(
        "CREATE INDEX ix_chunks_embedding ON chunks "
        "USING hnsw (embedding vector_cosine_ops) "
        "WITH (m = 16, ef_construction = 64)"
    )


def downgrade() -> None:
    op.drop_index("ix_chunks_embedding", table_name="chunks")
    op.drop_index("ix_chunks_document_id", table_name="chunks")
