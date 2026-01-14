"""
Tests to verify N+1 query fixes in conversation service.
"""

import pytest
from sqlalchemy import event, select
from sqlalchemy.engine import Engine

from app.models.conversation import Conversation, Message
from app.models.message_feedback import MessageFeedback
from app.services.conversation_service import ConversationService


class QueryCounter:
    """Helper class to count SQL queries executed."""

    def __init__(self):
        self.queries = []

    def __enter__(self):
        event.listen(Engine, "before_cursor_execute", self.receive_before_cursor_execute)
        return self

    def __exit__(self, *args):
        event.remove(Engine, "before_cursor_execute", self.receive_before_cursor_execute)

    def receive_before_cursor_execute(self, conn, cursor, statement, params, context, executemany):
        """Record each query executed."""
        self.queries.append(statement)

    @property
    def count(self):
        """Get total number of queries executed."""
        return len(self.queries)


@pytest.mark.asyncio
async def test_get_conversation_messages_no_n_plus_one(test_db):
    """
    Test that get_conversation_messages doesn't cause N+1 queries
    when accessing message feedback.
    """
    # Create a conversation
    conversation = Conversation(title="Test Conversation")
    test_db.add(conversation)
    await test_db.commit()
    await test_db.refresh(conversation)

    # Create multiple messages with feedback
    messages = []
    for i in range(5):
        message = Message(
            conversation_id=str(conversation.id),
            role="user" if i % 2 == 0 else "assistant",
            content=f"Message {i}",
        )
        test_db.add(message)
        messages.append(message)

    await test_db.commit()

    # Add feedback to some messages
    for i, message in enumerate(messages):
        await test_db.refresh(message)
        if i % 2 == 0:  # Add feedback to every other message
            feedback = MessageFeedback(
                message_id=str(message.id),
                is_positive=True,
                comment=f"Good message {i}",
            )
            test_db.add(feedback)

    await test_db.commit()

    # Now test that fetching messages with feedback doesn't cause N+1
    with QueryCounter() as counter:
        result = await ConversationService.get_conversation_messages(
            db=test_db,
            conversation_id=str(conversation.id),
        )

        # Access feedback on all messages (would trigger N+1 if not eager loaded)
        for msg in result:
            _ = msg.feedback  # This should NOT trigger additional queries

    # Should be exactly 1 query (with selectinload, it uses 1 query for messages + 1 for feedback)
    # SQLite uses 2 queries: 1 for messages, 1 for all feedback
    assert counter.count <= 2, (
        f"Expected at most 2 queries (messages + feedback), got {counter.count}. "
        f"This indicates an N+1 query problem."
    )

    # Verify we got all messages and feedback
    assert len(result) == 5
    feedback_count = sum(1 for msg in result if msg.feedback is not None)
    assert feedback_count == 3  # We added feedback to 3 messages (indices 0, 2, 4)


@pytest.mark.asyncio
async def test_get_conversation_messages_without_feedback(test_db):
    """Test that get_conversation_messages works when messages have no feedback."""
    # Create a conversation
    conversation = Conversation(title="Test Conversation")
    test_db.add(conversation)
    await test_db.commit()
    await test_db.refresh(conversation)

    # Create messages without feedback
    for i in range(3):
        message = Message(
            conversation_id=str(conversation.id),
            role="user",
            content=f"Message {i}",
        )
        test_db.add(message)

    await test_db.commit()

    # Fetch messages
    result = await ConversationService.get_conversation_messages(
        db=test_db,
        conversation_id=str(conversation.id),
    )

    # Verify results
    assert len(result) == 3
    for msg in result:
        assert msg.feedback is None


@pytest.mark.asyncio
async def test_get_conversation_messages_ordering(test_db):
    """Test that messages are returned in correct chronological order."""
    # Create a conversation
    conversation = Conversation(title="Test Conversation")
    test_db.add(conversation)
    await test_db.commit()
    await test_db.refresh(conversation)

    # Create messages in specific order
    messages = []
    for i in range(3):
        message = Message(
            conversation_id=str(conversation.id),
            role="user" if i % 2 == 0 else "assistant",
            content=f"Message {i}",
        )
        test_db.add(message)
        messages.append(message)
        await test_db.commit()
        await test_db.refresh(message)

    # Fetch messages
    result = await ConversationService.get_conversation_messages(
        db=test_db,
        conversation_id=str(conversation.id),
    )

    # Verify chronological order (created_at should be ascending)
    assert len(result) == 3
    for i in range(len(result) - 1):
        assert result[i].created_at <= result[i + 1].created_at
