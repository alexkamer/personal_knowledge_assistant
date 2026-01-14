"""add_chunk_source_constraint

Revision ID: 8ac3807b308b
Revises: 99790aa36c95
Create Date: 2026-01-14 15:44:09.613348

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8ac3807b308b'
down_revision: Union[str, Sequence[str], None] = '99790aa36c95'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add CHECK constraint ensuring chunks have exactly one source."""
    # Add constraint: exactly one of note_id, document_id, youtube_video_id must be NOT NULL
    op.create_check_constraint(
        "chunk_has_one_source",
        "chunks",
        "(note_id IS NOT NULL)::int + (document_id IS NOT NULL)::int + (youtube_video_id IS NOT NULL)::int = 1"
    )


def downgrade() -> None:
    """Remove CHECK constraint."""
    op.drop_constraint("chunk_has_one_source", "chunks", type_="check")
