"""change generated_images metadata and tags from JSONB/ARRAY to JSON for sqlite compatibility

Revision ID: 99790aa36c95
Revises: 1b37bd8b4e6b
Create Date: 2025-12-26 19:41:56.602335

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '99790aa36c95'
down_revision: Union[str, Sequence[str], None] = '1b37bd8b4e6b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Change metadata_ from JSONB to JSON for SQLite compatibility
    op.alter_column(
        'generated_images',
        'metadata_',
        type_=sa.JSON(),
        existing_type=sa.dialects.postgresql.JSONB(),
        existing_nullable=True
    )

    # Change tags from ARRAY to JSON for SQLite compatibility
    op.alter_column(
        'generated_images',
        'tags',
        type_=sa.JSON(),
        existing_type=sa.ARRAY(sa.String()),
        existing_nullable=True,
        postgresql_using='tags::json'
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Revert metadata_ from JSON to JSONB (PostgreSQL only)
    op.alter_column(
        'generated_images',
        'metadata_',
        type_=sa.dialects.postgresql.JSONB(),
        existing_type=sa.JSON(),
        existing_nullable=True
    )

    # Revert tags from JSON to ARRAY (PostgreSQL only)
    op.alter_column(
        'generated_images',
        'tags',
        type_=sa.ARRAY(sa.String()),
        existing_type=sa.JSON(),
        existing_nullable=True,
        postgresql_using='tags::text[]'
    )
