"""add unique constraint on documents.source

Revision ID: 002
Revises: 001
Create Date: 2026-02-13

"""

from typing import Sequence, Union

from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint("uq_documents_source", "documents", ["source"])


def downgrade() -> None:
    op.drop_constraint("uq_documents_source", "documents")
