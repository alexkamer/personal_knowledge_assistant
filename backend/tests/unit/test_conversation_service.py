"""
Unit tests for the Conversation service.
"""
import pytest
import json
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.conversation_service import ConversationService
from app.schemas.conversation import ConversationCreate, ConversationUpdate
from app.models.conversation import Conversation, Message


class TestConversationService:
    """Test suite for ConversationService."""

    @pytest.mark.asyncio
    async def test_create_conversation(self, test_db: AsyncSession):
        """Test creating a conversation."""
        conversation_data = ConversationCreate(title="Test Conversation")

        conversation = await ConversationService.create_conversation(
            test_db, conversation_data
        )

        assert conversation.id is not None
        assert conversation.title == "Test Conversation"
        assert conversation.summary is None
        assert conversation.is_pinned is False

    @pytest.mark.asyncio
    async def test_get_conversation(self, test_db: AsyncSession):
        """Test getting a conversation by ID."""
        # Create a conversation first
        conversation_data = ConversationCreate(title="Test")
        created = await ConversationService.create_conversation(test_db, conversation_data)

        # Get it back
        conversation = await ConversationService.get_conversation(test_db, str(created.id))

        assert conversation is not None
        assert conversation.id == created.id
        assert conversation.title == "Test"

    @pytest.mark.asyncio
    async def test_get_conversation_not_found(self, test_db: AsyncSession):
        """Test getting a non-existent conversation."""
        conversation = await ConversationService.get_conversation(
            test_db, "nonexistent-id"
        )

        assert conversation is None

    @pytest.mark.asyncio
    async def test_list_conversations_empty(self, test_db: AsyncSession):
        """Test listing conversations when database is empty."""
        conversations, total = await ConversationService.list_conversations(test_db)

        assert conversations == []
        assert total == 0

    @pytest.mark.asyncio
    async def test_list_conversations(self, test_db: AsyncSession):
        """Test listing conversations."""
        # Create multiple conversations
        for i in range(3):
            conversation_data = ConversationCreate(title=f"Conversation {i}")
            await ConversationService.create_conversation(test_db, conversation_data)

        conversations, total = await ConversationService.list_conversations(test_db)

        assert len(conversations) == 3
        assert total == 3
        # Each tuple should have (conversation, message_count)
        for conv, msg_count in conversations:
            assert isinstance(conv, Conversation)
            assert msg_count == 0  # No messages yet

    @pytest.mark.asyncio
    async def test_list_conversations_with_pagination(self, test_db: AsyncSession):
        """Test listing conversations with pagination."""
        # Create 5 conversations
        for i in range(5):
            conversation_data = ConversationCreate(title=f"Conversation {i}")
            await ConversationService.create_conversation(test_db, conversation_data)

        # Get first 2
        conversations, total = await ConversationService.list_conversations(
            test_db, skip=0, limit=2
        )

        assert len(conversations) == 2
        assert total == 5

        # Get next 2
        conversations, total = await ConversationService.list_conversations(
            test_db, skip=2, limit=2
        )

        assert len(conversations) == 2
        assert total == 5

    @pytest.mark.asyncio
    async def test_list_conversations_with_messages(self, test_db: AsyncSession):
        """Test listing conversations includes message counts."""
        # Create conversation
        conversation_data = ConversationCreate(title="Test")
        conversation = await ConversationService.create_conversation(
            test_db, conversation_data
        )

        # Add messages
        await ConversationService.add_message(
            test_db, str(conversation.id), "user", "Hello"
        )
        await ConversationService.add_message(
            test_db, str(conversation.id), "assistant", "Hi there"
        )

        conversations, total = await ConversationService.list_conversations(test_db)

        assert len(conversations) == 1
        conv, msg_count = conversations[0]
        assert msg_count == 2

    @pytest.mark.asyncio
    async def test_update_conversation(self, test_db: AsyncSession):
        """Test updating a conversation."""
        # Create conversation
        conversation_data = ConversationCreate(title="Original Title")
        conversation = await ConversationService.create_conversation(
            test_db, conversation_data
        )

        # Update it
        update_data = ConversationUpdate(
            title="Updated Title",
            summary="New summary",
            is_pinned=True,
        )
        updated = await ConversationService.update_conversation(
            test_db, str(conversation.id), update_data
        )

        assert updated is not None
        assert updated.title == "Updated Title"
        assert updated.summary == "New summary"
        assert updated.is_pinned is True

    @pytest.mark.asyncio
    async def test_update_conversation_partial(self, test_db: AsyncSession):
        """Test partial update of a conversation."""
        # Create conversation
        conversation_data = ConversationCreate(title="Original")
        conversation = await ConversationService.create_conversation(
            test_db, conversation_data
        )

        # Update only title
        update_data = ConversationUpdate(title="New Title")
        updated = await ConversationService.update_conversation(
            test_db, str(conversation.id), update_data
        )

        assert updated is not None
        assert updated.title == "New Title"
        assert updated.summary is None  # Should remain unchanged

    @pytest.mark.asyncio
    async def test_update_conversation_not_found(self, test_db: AsyncSession):
        """Test updating a non-existent conversation."""
        update_data = ConversationUpdate(title="New Title")
        updated = await ConversationService.update_conversation(
            test_db, "nonexistent-id", update_data
        )

        assert updated is None

    @pytest.mark.asyncio
    async def test_delete_conversation(self, test_db: AsyncSession):
        """Test deleting a conversation."""
        # Create conversation
        conversation_data = ConversationCreate(title="To Delete")
        conversation = await ConversationService.create_conversation(
            test_db, conversation_data
        )

        # Delete it
        deleted = await ConversationService.delete_conversation(
            test_db, str(conversation.id)
        )

        assert deleted is True

        # Verify it's gone
        result = await ConversationService.get_conversation(
            test_db, str(conversation.id)
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_conversation_not_found(self, test_db: AsyncSession):
        """Test deleting a non-existent conversation."""
        deleted = await ConversationService.delete_conversation(
            test_db, "nonexistent-id"
        )

        assert deleted is False

    @pytest.mark.asyncio
    async def test_add_message(self, test_db: AsyncSession):
        """Test adding a message to a conversation."""
        # Create conversation
        conversation_data = ConversationCreate(title="Test")
        conversation = await ConversationService.create_conversation(
            test_db, conversation_data
        )

        # Add message
        message = await ConversationService.add_message(
            test_db,
            str(conversation.id),
            "user",
            "Hello, world!",
        )

        assert message.id is not None
        assert message.conversation_id == str(conversation.id)
        assert message.role == "user"
        assert message.content == "Hello, world!"
        assert message.retrieved_chunks is None
        assert message.model_used is None

    @pytest.mark.asyncio
    async def test_add_message_with_chunks(self, test_db: AsyncSession):
        """Test adding a message with retrieved chunks."""
        # Create conversation
        conversation_data = ConversationCreate(title="Test")
        conversation = await ConversationService.create_conversation(
            test_db, conversation_data
        )

        # Add message with chunks
        chunks = [
            {"chunk_id": "1", "content": "Test", "source": "note1"},
            {"chunk_id": "2", "content": "More", "source": "note2"},
        ]
        message = await ConversationService.add_message(
            test_db,
            str(conversation.id),
            "assistant",
            "Answer",
            retrieved_chunks=chunks,
            model_used="test-model",
        )

        assert message.retrieved_chunks is not None
        assert message.model_used == "test-model"

        # Verify chunks are stored as JSON
        parsed_chunks = json.loads(message.retrieved_chunks)
        assert len(parsed_chunks) == 2
        assert parsed_chunks[0]["chunk_id"] == "1"

    @pytest.mark.asyncio
    async def test_get_conversation_messages(self, test_db: AsyncSession):
        """Test getting all messages for a conversation."""
        # Create conversation
        conversation_data = ConversationCreate(title="Test")
        conversation = await ConversationService.create_conversation(
            test_db, conversation_data
        )

        # Add multiple messages
        await ConversationService.add_message(
            test_db, str(conversation.id), "user", "First message"
        )
        await ConversationService.add_message(
            test_db, str(conversation.id), "assistant", "Response"
        )
        await ConversationService.add_message(
            test_db, str(conversation.id), "user", "Follow-up"
        )

        # Get all messages
        messages = await ConversationService.get_conversation_messages(
            test_db, str(conversation.id)
        )

        assert len(messages) == 3
        assert messages[0].content == "First message"
        assert messages[1].content == "Response"
        assert messages[2].content == "Follow-up"
        # Verify they're in chronological order
        assert messages[0].created_at <= messages[1].created_at
        assert messages[1].created_at <= messages[2].created_at

    @pytest.mark.asyncio
    async def test_get_conversation_messages_empty(self, test_db: AsyncSession):
        """Test getting messages for a conversation with no messages."""
        # Create conversation
        conversation_data = ConversationCreate(title="Test")
        conversation = await ConversationService.create_conversation(
            test_db, conversation_data
        )

        # Get messages
        messages = await ConversationService.get_conversation_messages(
            test_db, str(conversation.id)
        )

        assert messages == []
