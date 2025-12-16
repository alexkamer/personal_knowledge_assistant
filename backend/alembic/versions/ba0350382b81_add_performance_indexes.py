"""add_performance_indexes

Revision ID: ba0350382b81
Revises: 7862fed0b1f1
Create Date: 2025-12-16 15:25:29.696635

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ba0350382b81'
down_revision: Union[str, Sequence[str], None] = '7862fed0b1f1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Composite index for conversation sorting (pinned first, then by date)
    op.create_index(
        'ix_conversations_pinned_updated',
        'conversations',
        ['is_pinned', sa.text('updated_at DESC')],
        unique=False
    )

    # Composite index for message retrieval
    op.create_index(
        'ix_messages_conversation_created',
        'messages',
        ['conversation_id', sa.text('created_at ASC')],
        unique=False
    )

    # Composite index for chunk retrieval
    op.create_index(
        'ix_chunks_document_index',
        'chunks',
        ['document_id', 'chunk_index'],
        unique=False
    )

    # Simple index for conversation list sorting
    op.create_index(
        'ix_conversations_updated_desc',
        'conversations',
        [sa.text('updated_at DESC')],
        unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_conversations_updated_desc', table_name='conversations')
    op.drop_index('ix_chunks_document_index', table_name='chunks')
    op.drop_index('ix_messages_conversation_created', table_name='messages')
    op.drop_index('ix_conversations_pinned_updated', table_name='conversations')
