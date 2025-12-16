"""add_is_pinned_to_conversations

Revision ID: 7862fed0b1f1
Revises: 77a15ccbb43a
Create Date: 2025-12-16 15:05:05.956991

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7862fed0b1f1'
down_revision: Union[str, Sequence[str], None] = '77a15ccbb43a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add is_pinned column to conversations table
    op.add_column('conversations', sa.Column('is_pinned', sa.Boolean(), nullable=False, server_default='0'))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove is_pinned column from conversations table
    op.drop_column('conversations', 'is_pinned')
