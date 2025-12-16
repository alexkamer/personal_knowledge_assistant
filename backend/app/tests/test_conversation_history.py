"""
Comprehensive tests for conversation history feature.

Tests cover:
1. Creating conversations
2. Listing conversations with message counts
3. Getting conversation details
4. Updating conversation titles
5. Deleting conversations
6. Pagination
7. Message count accuracy
"""
import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation, Message
from app.services.conversation_service import ConversationService
from app.schemas.conversation import ConversationCreate, ConversationUpdate


class TestConversationCreation:
    """Test conversation creation."""

    @pytest.mark.asyncio
    async def test_create_conversation_with_title(self, db_session: AsyncSession):
        """Test creating a conversation with a custom title."""
        # Arrange
        conversation_data = ConversationCreate(title="My First Chat")

        # Act
        conversation = await ConversationService.create_conversation(
            db_session, conversation_data
        )

        # Assert
        assert conversation is not None
        assert conversation.title == "My First Chat"
        assert conversation.id is not None
        assert conversation.created_at is not None
        assert conversation.updated_at is not None
        assert isinstance(conversation.created_at, datetime)

    @pytest.mark.asyncio
    async def test_create_conversation_with_auto_title(self, db_session: AsyncSession):
        """Test creating a conversation with auto-generated title."""
        # Arrange
        user_message = "What is the capital of France?"
        conversation_data = ConversationCreate(
            title=f"Chat about: {user_message[:50]}"
        )

        # Act
        conversation = await ConversationService.create_conversation(
            db_session, conversation_data
        )

        # Assert
        assert conversation is not None
        assert conversation.title == "Chat about: What is the capital of France?"
        assert len(conversation.title) <= 255  # Check title length constraint


class TestConversationListing:
    """Test conversation listing with message counts."""

    @pytest.mark.asyncio
    async def test_list_empty_conversations(self, db_session: AsyncSession):
        """Test listing conversations when none exist."""
        # Act
        conversations, total = await ConversationService.list_conversations(
            db_session, skip=0, limit=100
        )

        # Assert
        assert conversations == []
        assert total == 0

    @pytest.mark.asyncio
    async def test_list_conversations_with_message_counts(
        self, db_session: AsyncSession
    ):
        """Test listing conversations includes accurate message counts."""
        # Arrange - Create 3 conversations with different message counts
        conv1_data = ConversationCreate(title="Conversation 1")
        conv1 = await ConversationService.create_conversation(db_session, conv1_data)

        conv2_data = ConversationCreate(title="Conversation 2")
        conv2 = await ConversationService.create_conversation(db_session, conv2_data)

        conv3_data = ConversationCreate(title="Conversation 3")
        conv3 = await ConversationService.create_conversation(db_session, conv3_data)

        # Add messages to conversations
        # Conv1: 2 messages (1 user, 1 assistant)
        await ConversationService.add_message(
            db_session, str(conv1.id), "user", "Hello"
        )
        await ConversationService.add_message(
            db_session, str(conv1.id), "assistant", "Hi there!"
        )

        # Conv2: 4 messages (2 user, 2 assistant)
        await ConversationService.add_message(
            db_session, str(conv2.id), "user", "Question 1"
        )
        await ConversationService.add_message(
            db_session, str(conv2.id), "assistant", "Answer 1"
        )
        await ConversationService.add_message(
            db_session, str(conv2.id), "user", "Question 2"
        )
        await ConversationService.add_message(
            db_session, str(conv2.id), "assistant", "Answer 2"
        )

        # Conv3: 0 messages (empty conversation)

        # Act
        conversations, total = await ConversationService.list_conversations(
            db_session, skip=0, limit=100
        )

        # Assert
        assert total == 3
        assert len(conversations) == 3

        # Find each conversation in results
        conv1_result = next(
            (c for c, count in conversations if c.id == conv1.id), None
        )
        conv2_result = next(
            (c for c, count in conversations if c.id == conv2.id), None
        )
        conv3_result = next(
            (c for c, count in conversations if c.id == conv3.id), None
        )

        # Check message counts
        conv1_count = next(count for c, count in conversations if c.id == conv1.id)
        conv2_count = next(count for c, count in conversations if c.id == conv2.id)
        conv3_count = next(count for c, count in conversations if c.id == conv3.id)

        assert conv1_count == 2
        assert conv2_count == 4
        assert conv3_count == 0

    @pytest.mark.asyncio
    async def test_list_conversations_ordering(self, db_session: AsyncSession):
        """Test that conversations are ordered by updated_at descending."""
        # Arrange - Create conversations
        conv1_data = ConversationCreate(title="First")
        conv1 = await ConversationService.create_conversation(db_session, conv1_data)

        conv2_data = ConversationCreate(title="Second")
        conv2 = await ConversationService.create_conversation(db_session, conv2_data)

        conv3_data = ConversationCreate(title="Third")
        conv3 = await ConversationService.create_conversation(db_session, conv3_data)

        # Update conv1 to make it the most recent
        await ConversationService.update_conversation(
            db_session, str(conv1.id), ConversationUpdate(title="First - Updated")
        )

        # Act
        conversations, total = await ConversationService.list_conversations(
            db_session, skip=0, limit=100
        )

        # Assert - Updated conversation should be first
        assert len(conversations) == 3
        conv_objects = [c for c, _ in conversations]
        assert conv_objects[0].id == conv1.id  # Most recently updated
        assert conv_objects[0].title == "First - Updated"

    @pytest.mark.asyncio
    async def test_list_conversations_pagination(self, db_session: AsyncSession):
        """Test pagination works correctly."""
        # Arrange - Create 5 conversations
        for i in range(5):
            conv_data = ConversationCreate(title=f"Conversation {i}")
            await ConversationService.create_conversation(db_session, conv_data)

        # Act - Get first page (2 items)
        page1, total = await ConversationService.list_conversations(
            db_session, skip=0, limit=2
        )

        # Get second page (2 items)
        page2, _ = await ConversationService.list_conversations(
            db_session, skip=2, limit=2
        )

        # Get third page (1 item)
        page3, _ = await ConversationService.list_conversations(
            db_session, skip=4, limit=2
        )

        # Assert
        assert total == 5
        assert len(page1) == 2
        assert len(page2) == 2
        assert len(page3) == 1


class TestConversationRetrieval:
    """Test retrieving specific conversations."""

    @pytest.mark.asyncio
    async def test_get_conversation_by_id(self, db_session: AsyncSession):
        """Test getting a conversation by ID."""
        # Arrange
        conv_data = ConversationCreate(title="Test Conversation")
        created_conv = await ConversationService.create_conversation(
            db_session, conv_data
        )

        # Act
        retrieved_conv = await ConversationService.get_conversation(
            db_session, str(created_conv.id)
        )

        # Assert
        assert retrieved_conv is not None
        assert retrieved_conv.id == created_conv.id
        assert retrieved_conv.title == "Test Conversation"

    @pytest.mark.asyncio
    async def test_get_nonexistent_conversation(self, db_session: AsyncSession):
        """Test getting a conversation that doesn't exist."""
        # Act
        retrieved_conv = await ConversationService.get_conversation(
            db_session, "nonexistent-id"
        )

        # Assert
        assert retrieved_conv is None

    @pytest.mark.asyncio
    async def test_get_conversation_messages(self, db_session: AsyncSession):
        """Test getting all messages for a conversation."""
        # Arrange
        conv_data = ConversationCreate(title="Test Conversation")
        conversation = await ConversationService.create_conversation(
            db_session, conv_data
        )

        # Add messages
        msg1 = await ConversationService.add_message(
            db_session, str(conversation.id), "user", "First message"
        )
        msg2 = await ConversationService.add_message(
            db_session, str(conversation.id), "assistant", "Second message"
        )
        msg3 = await ConversationService.add_message(
            db_session, str(conversation.id), "user", "Third message"
        )

        # Act
        messages = await ConversationService.get_conversation_messages(
            db_session, str(conversation.id)
        )

        # Assert
        assert len(messages) == 3
        assert messages[0].id == msg1.id
        assert messages[1].id == msg2.id
        assert messages[2].id == msg3.id
        assert messages[0].content == "First message"
        assert messages[1].content == "Second message"
        assert messages[2].content == "Third message"


class TestConversationUpdate:
    """Test updating conversations."""

    @pytest.mark.asyncio
    async def test_update_conversation_title(self, db_session: AsyncSession):
        """Test updating conversation title."""
        # Arrange
        conv_data = ConversationCreate(title="Original Title")
        conversation = await ConversationService.create_conversation(
            db_session, conv_data
        )

        update_data = ConversationUpdate(title="Updated Title")

        # Act
        updated_conv = await ConversationService.update_conversation(
            db_session, str(conversation.id), update_data
        )

        # Assert
        assert updated_conv is not None
        assert updated_conv.title == "Updated Title"
        assert updated_conv.id == conversation.id

    @pytest.mark.asyncio
    async def test_update_conversation_summary(self, db_session: AsyncSession):
        """Test updating conversation summary."""
        # Arrange
        conv_data = ConversationCreate(title="Test Conversation")
        conversation = await ConversationService.create_conversation(
            db_session, conv_data
        )

        update_data = ConversationUpdate(summary="A brief summary of the conversation")

        # Act
        updated_conv = await ConversationService.update_conversation(
            db_session, str(conversation.id), update_data
        )

        # Assert
        assert updated_conv is not None
        assert updated_conv.summary == "A brief summary of the conversation"
        assert updated_conv.title == "Test Conversation"  # Title unchanged

    @pytest.mark.asyncio
    async def test_update_nonexistent_conversation(self, db_session: AsyncSession):
        """Test updating a conversation that doesn't exist."""
        # Arrange
        update_data = ConversationUpdate(title="New Title")

        # Act
        updated_conv = await ConversationService.update_conversation(
            db_session, "nonexistent-id", update_data
        )

        # Assert
        assert updated_conv is None


class TestConversationDeletion:
    """Test deleting conversations."""

    @pytest.mark.asyncio
    async def test_delete_conversation(self, db_session: AsyncSession):
        """Test deleting a conversation."""
        # Arrange
        conv_data = ConversationCreate(title="To Be Deleted")
        conversation = await ConversationService.create_conversation(
            db_session, conv_data
        )

        # Act
        deleted = await ConversationService.delete_conversation(
            db_session, str(conversation.id)
        )

        # Assert
        assert deleted is True

        # Verify it's gone
        retrieved_conv = await ConversationService.get_conversation(
            db_session, str(conversation.id)
        )
        assert retrieved_conv is None

    @pytest.mark.asyncio
    async def test_delete_conversation_cascades_messages(
        self, db_session: AsyncSession
    ):
        """Test that deleting a conversation also deletes its messages."""
        # Arrange
        conv_data = ConversationCreate(title="Conversation with Messages")
        conversation = await ConversationService.create_conversation(
            db_session, conv_data
        )

        # Add messages
        await ConversationService.add_message(
            db_session, str(conversation.id), "user", "Message 1"
        )
        await ConversationService.add_message(
            db_session, str(conversation.id), "assistant", "Message 2"
        )

        # Act
        deleted = await ConversationService.delete_conversation(
            db_session, str(conversation.id)
        )

        # Assert
        assert deleted is True

        # Verify messages are also gone
        messages = await ConversationService.get_conversation_messages(
            db_session, str(conversation.id)
        )
        assert messages == []

    @pytest.mark.asyncio
    async def test_delete_nonexistent_conversation(self, db_session: AsyncSession):
        """Test deleting a conversation that doesn't exist."""
        # Act
        deleted = await ConversationService.delete_conversation(
            db_session, "nonexistent-id"
        )

        # Assert
        assert deleted is False
