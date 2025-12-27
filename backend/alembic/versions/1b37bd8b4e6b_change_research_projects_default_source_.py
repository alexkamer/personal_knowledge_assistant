"""change research_projects default_source_types from ARRAY to JSON for sqlite compatibility

Revision ID: 1b37bd8b4e6b
Revises: 1372f6e4ef76
Create Date: 2025-12-26 19:41:12.828116

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1b37bd8b4e6b'
down_revision: Union[str, Sequence[str], None] = '1372f6e4ef76'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Change default_source_types from ARRAY to JSON for SQLite compatibility
    # PostgreSQL: ARRAY and JSON both work
    # SQLite: Only JSON works (ARRAY not supported)
    op.alter_column(
        'research_projects',
        'default_source_types',
        type_=sa.JSON(),
        existing_type=sa.ARRAY(sa.String()),
        existing_nullable=True,
        postgresql_using='default_source_types::json'
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Revert JSON back to ARRAY (only works on PostgreSQL)
    op.alter_column(
        'research_projects',
        'default_source_types',
        type_=sa.ARRAY(sa.String()),
        existing_type=sa.JSON(),
        existing_nullable=True,
        postgresql_using='default_source_types::text[]'
    )
