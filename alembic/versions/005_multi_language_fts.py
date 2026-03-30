"""add per-document FTS language support via trigger-maintained search_vector

Revision ID: 005
Revises: 004
Create Date: 2026-03-30

Replaces the hardcoded `to_tsvector('english', text)` generated column with a
trigger-maintained tsvector column that uses the language stored on each chunk
row. Language is declared at ingestion time and defaults to 'english'.

Upgrade steps:
  1. Add language column to documents (NOT NULL DEFAULT 'english')
  2. Add language column to chunks (NOT NULL DEFAULT 'english')
  3. Drop GIN index on search_vector
  4. Drop search_vector column (was a generated column)
  5. Add search_vector as plain tsvector (nullable)
  6. Create trigger function chunks_search_vector_update()
  7. Create trigger trg_chunks_search_vector
  8. Backfill existing chunks
  9. Recreate GIN index

Downgrade reverses all steps.
"""

from typing import Sequence, Union

from alembic import op

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add language column to documents
    op.execute(
        "ALTER TABLE documents ADD COLUMN language VARCHAR NOT NULL DEFAULT 'english'"
    )

    # 2. Add language column to chunks
    op.execute(
        "ALTER TABLE chunks ADD COLUMN language VARCHAR NOT NULL DEFAULT 'english'"
    )

    # 3. Drop GIN index (created with the column in migration 004)
    op.execute("DROP INDEX ix_chunks_search_vector")

    # 4. Drop the generated search_vector column
    op.execute("ALTER TABLE chunks DROP COLUMN search_vector")

    # 5. Add plain tsvector column (nullable — will be populated by trigger)
    op.execute("ALTER TABLE chunks ADD COLUMN search_vector tsvector")

    # 6. Create trigger function
    op.execute(
        """
        CREATE OR REPLACE FUNCTION chunks_search_vector_update() RETURNS trigger AS $$
        BEGIN
          NEW.search_vector := to_tsvector(NEW.language::regconfig, NEW.text);
          RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    # 7. Create trigger — fires BEFORE INSERT or UPDATE of text/language columns
    op.execute(
        """
        CREATE TRIGGER trg_chunks_search_vector
        BEFORE INSERT OR UPDATE OF text, language ON chunks
        FOR EACH ROW EXECUTE FUNCTION chunks_search_vector_update()
        """
    )

    # 8. Backfill existing rows (trigger only fires on future inserts/updates)
    op.execute(
        "UPDATE chunks SET search_vector = to_tsvector('english'::regconfig, text)"
    )

    # 9. Recreate GIN index on the new plain tsvector column
    op.execute(
        "CREATE INDEX ix_chunks_search_vector ON chunks USING gin(search_vector)"
    )


def downgrade() -> None:
    # 1. Drop trigger
    op.execute(
        "DROP TRIGGER IF EXISTS trg_chunks_search_vector ON chunks"
    )

    # 2. Drop trigger function
    op.execute(
        "DROP FUNCTION IF EXISTS chunks_search_vector_update()"
    )

    # 3. Drop GIN index
    op.execute("DROP INDEX IF EXISTS ix_chunks_search_vector")

    # 4. Drop plain tsvector column
    op.execute("ALTER TABLE chunks DROP COLUMN search_vector")

    # 5. Recreate search_vector as a generated column (original state from migration 004)
    op.execute(
        "ALTER TABLE chunks ADD COLUMN search_vector tsvector "
        "GENERATED ALWAYS AS (to_tsvector('english', text)) STORED"
    )

    # 6. Recreate GIN index
    op.execute(
        "CREATE INDEX ix_chunks_search_vector ON chunks USING gin(search_vector)"
    )

    # 7. Drop language column from chunks
    op.execute("ALTER TABLE chunks DROP COLUMN language")

    # 8. Drop language column from documents
    op.execute("ALTER TABLE documents DROP COLUMN language")
