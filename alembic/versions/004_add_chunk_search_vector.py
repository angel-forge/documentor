"""add full-text search vector column and GIN index to chunks

Revision ID: 004
Revises: 003
Create Date: 2026-03-30

Adds a stored generated tsvector column and a GIN index to support
full-text search as part of the hybrid search (vector + FTS) feature.

Note on production index creation: This migration uses plain CREATE INDEX
(transactional). For zero-downtime deployments on large tables, apply the
index manually with CREATE INDEX CONCURRENTLY outside this migration, then
run the migration with the CREATE INDEX line removed.
"""

from typing import Sequence, Union

from alembic import op

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE chunks "
        "ADD COLUMN search_vector tsvector "
        "GENERATED ALWAYS AS (to_tsvector('english', text)) STORED"
    )
    op.execute(
        "CREATE INDEX ix_chunks_search_vector ON chunks USING gin(search_vector)"
    )


def downgrade() -> None:
    op.drop_index("ix_chunks_search_vector", table_name="chunks")
    op.execute("ALTER TABLE chunks DROP COLUMN search_vector")
