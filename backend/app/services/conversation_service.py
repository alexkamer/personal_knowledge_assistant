"""
Service layer for conversation and message CRUD operations.
"""
import json
import logging
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation, Message
from app.schemas.conversation import ConversationCreate, ConversationUpdate

logger = logging.getLogger(__name__)


class ConversationService:
    """Service for managing conversations and messages."""

    @staticmethod
    async def create_conversation(
        db: AsyncSession,
        conversation_data: ConversationCreate,
    ) -> Conversation:
        """
        Create a new conversation.

        Args:
            db: Database session
            conversation_data: Conversation creation data

        Returns:
            Created conversation
        """
        conversation = Conversation(title=conversation_data.title)
        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)
        return conversation

    @staticmethod
    async def get_conversation(
        db: AsyncSession,
        conversation_id: str,
    ) -> Optional[Conversation]:
        """
        Get a conversation by ID.

        Args:
            db: Database session
            conversation_id: Conversation ID

        Returns:
            Conversation if found, None otherwise
        """
        result = await db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_conversations(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[tuple[Conversation, int]], int]:
        """
        List conversations with pagination, including message counts.

        Args:
            db: Database session
            skip: Number of conversations to skip
            limit: Maximum number of conversations to return

        Returns:
            Tuple of (list of (conversation, message_count) tuples, total count)
        """
        # Get total count
        count_result = await db.execute(select(func.count(Conversation.id)))
        total = count_result.scalar_one()

        # Get conversations with message counts
        # Sort by: pinned first (DESC), then by updated_at (DESC)
        result = await db.execute(
            select(Conversation, func.count(Message.id).label("message_count"))
            .outerjoin(Message, Conversation.id == Message.conversation_id)
            .group_by(Conversation.id)
            .order_by(Conversation.is_pinned.desc(), Conversation.updated_at.desc())
            .offset(skip)
            .limit(limit)
        )

        conversations_with_counts = [(row[0], row[1]) for row in result.all()]

        return conversations_with_counts, total

    @staticmethod
    async def update_conversation(
        db: AsyncSession,
        conversation_id: str,
        conversation_data: ConversationUpdate,
    ) -> Optional[Conversation]:
        """
        Update a conversation.

        Args:
            db: Database session
            conversation_id: Conversation ID
            conversation_data: Conversation update data

        Returns:
            Updated conversation if found, None otherwise
        """
        result = await db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conversation = result.scalar_one_or_none()

        if not conversation:
            return None

        update_data = conversation_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(conversation, field, value)

        await db.commit()
        await db.refresh(conversation)
        return conversation

    @staticmethod
    async def delete_conversation(
        db: AsyncSession,
        conversation_id: str,
    ) -> bool:
        """
        Delete a conversation.

        Args:
            db: Database session
            conversation_id: Conversation ID

        Returns:
            True if deleted, False if not found
        """
        result = await db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conversation = result.scalar_one_or_none()

        if not conversation:
            return False

        await db.delete(conversation)
        await db.commit()
        return True

    @staticmethod
    async def add_message(
        db: AsyncSession,
        conversation_id: str,
        role: str,
        content: str,
        retrieved_chunks: Optional[list[dict]] = None,
        model_used: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> Message:
        """
        Add a message to a conversation.

        Args:
            db: Database session
            conversation_id: Conversation ID
            role: Message role ('user' or 'assistant')
            content: Message content
            retrieved_chunks: Optional list of retrieved chunk citations
            model_used: Optional model name used for generation
            metadata: Optional metadata dict (e.g., for attachments)

        Returns:
            Created message
        """
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            retrieved_chunks=json.dumps(retrieved_chunks) if retrieved_chunks else None,
            model_used=model_used,
            metadata_=metadata,
        )
        db.add(message)
        await db.commit()
        await db.refresh(message)
        return message

    @staticmethod
    async def get_conversation_messages(
        db: AsyncSession,
        conversation_id: str,
    ) -> list[Message]:
        """
        Get all messages for a conversation.

        Args:
            db: Database session
            conversation_id: Conversation ID

        Returns:
            List of messages ordered by creation time
        """
        result = await db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
        )
        return list(result.scalars().all())
