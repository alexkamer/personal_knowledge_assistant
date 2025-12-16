"""
Integration tests for the chat API endpoints.
"""
import pytest
from httpx import AsyncClient


class TestConversationsAPI:
    """Test suite for conversation endpoints."""

    @pytest.mark.asyncio
    async def test_create_conversation(self, client: AsyncClient):
        """Test creating a new conversation."""
        response = await client.post(
            "/api/v1/chat/conversations/",
            json={
                "title": "Test Conversation",
                "summary": "A test conversation",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Test Conversation"
        assert data["summary"] == "A test conversation"
        assert "id" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_list_conversations(self, client: AsyncClient):
        """Test listing conversations."""
        # Create a conversation first
        await client.post(
            "/api/v1/chat/conversations/",
            json={"title": "Test 1"},
        )

        response = await client.get("/api/v1/chat/conversations/")

        assert response.status_code == 200
        data = response.json()
        assert "conversations" in data
        assert len(data["conversations"]) >= 1

    @pytest.mark.asyncio
    async def test_get_conversation_by_id(self, client: AsyncClient):
        """Test getting a conversation by ID."""
        # Create a conversation
        create_response = await client.post(
            "/api/v1/chat/conversations/",
            json={"title": "Test Conversation"},
        )
        conversation_id = create_response.json()["id"]

        # Get the conversation
        response = await client.get(f"/api/v1/chat/conversations/{conversation_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == conversation_id
        assert data["title"] == "Test Conversation"

    @pytest.mark.asyncio
    async def test_get_nonexistent_conversation(self, client: AsyncClient):
        """Test getting a conversation that doesn't exist."""
        response = await client.get("/api/v1/chat/conversations/nonexistent-id")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_conversation(self, client: AsyncClient):
        """Test updating a conversation."""
        # Create a conversation
        create_response = await client.post(
            "/api/v1/chat/conversations/",
            json={"title": "Original Title"},
        )
        conversation_id = create_response.json()["id"]

        # Update the conversation
        response = await client.put(
            f"/api/v1/chat/conversations/{conversation_id}",
            json={
                "title": "Updated Title",
                "summary": "Updated summary",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["summary"] == "Updated summary"

    @pytest.mark.asyncio
    async def test_delete_conversation(self, client: AsyncClient):
        """Test deleting a conversation."""
        # Create a conversation
        create_response = await client.post(
            "/api/v1/chat/conversations/",
            json={"title": "To Delete"},
        )
        conversation_id = create_response.json()["id"]

        # Delete the conversation
        response = await client.delete(f"/api/v1/chat/conversations/{conversation_id}")

        assert response.status_code == 200

        # Verify it's deleted
        get_response = await client.get(f"/api/v1/chat/conversations/{conversation_id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_pin_conversation(self, client: AsyncClient):
        """Test pinning a conversation."""
        # Create a conversation
        create_response = await client.post(
            "/api/v1/chat/conversations/",
            json={"title": "To Pin"},
        )
        conversation_id = create_response.json()["id"]

        # Pin the conversation
        response = await client.post(f"/api/v1/chat/conversations/{conversation_id}/pin")

        assert response.status_code == 200
        data = response.json()
        assert data["is_pinned"] is True

    @pytest.mark.asyncio
    async def test_unpin_conversation(self, client: AsyncClient):
        """Test unpinning a conversation."""
        # Create and pin a conversation
        create_response = await client.post(
            "/api/v1/chat/conversations/",
            json={"title": "To Unpin"},
        )
        conversation_id = create_response.json()["id"]
        await client.post(f"/api/v1/chat/conversations/{conversation_id}/pin")

        # Unpin the conversation
        response = await client.post(f"/api/v1/chat/conversations/{conversation_id}/unpin")

        assert response.status_code == 200
        data = response.json()
        assert data["is_pinned"] is False


class TestMessagesAPI:
    """Test suite for message endpoints."""

    @pytest.mark.asyncio
    async def test_create_message(self, client: AsyncClient):
        """Test creating a message in a conversation."""
        # Create a conversation first
        conv_response = await client.post(
            "/api/v1/chat/conversations/",
            json={"title": "Test"},
        )
        conversation_id = conv_response.json()["id"]

        # Create a message
        response = await client.post(
            f"/api/v1/chat/conversations/{conversation_id}/messages",
            json={
                "role": "user",
                "content": "Hello, how are you?",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "user"
        assert data["content"] == "Hello, how are you?"
        assert data["conversation_id"] == conversation_id

    @pytest.mark.asyncio
    async def test_list_messages(self, client: AsyncClient):
        """Test listing messages in a conversation."""
        # Create a conversation and message
        conv_response = await client.post(
            "/api/v1/chat/conversations/",
            json={"title": "Test"},
        )
        conversation_id = conv_response.json()["id"]

        await client.post(
            f"/api/v1/chat/conversations/{conversation_id}/messages",
            json={"role": "user", "content": "Test message"},
        )

        # List messages
        response = await client.get(
            f"/api/v1/chat/conversations/{conversation_id}/messages"
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["content"] == "Test message"

    @pytest.mark.asyncio
    async def test_get_message_by_id(self, client: AsyncClient):
        """Test getting a specific message."""
        # Create conversation and message
        conv_response = await client.post(
            "/api/v1/chat/conversations/",
            json={"title": "Test"},
        )
        conversation_id = conv_response.json()["id"]

        msg_response = await client.post(
            f"/api/v1/chat/conversations/{conversation_id}/messages",
            json={"role": "user", "content": "Test message"},
        )
        message_id = msg_response.json()["id"]

        # Get the message
        response = await client.get(f"/api/v1/chat/messages/{message_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == message_id
        assert data["content"] == "Test message"

    @pytest.mark.asyncio
    async def test_submit_feedback(self, client: AsyncClient):
        """Test submitting feedback for a message."""
        # Create conversation and message
        conv_response = await client.post(
            "/api/v1/chat/conversations/",
            json={"title": "Test"},
        )
        conversation_id = conv_response.json()["id"]

        msg_response = await client.post(
            f"/api/v1/chat/conversations/{conversation_id}/messages",
            json={"role": "assistant", "content": "Test response"},
        )
        message_id = msg_response.json()["id"]

        # Submit positive feedback
        response = await client.post(
            f"/api/v1/chat/messages/{message_id}/feedback",
            json={"is_positive": True, "comment": "Great answer!"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_positive"] is True
        assert data["comment"] == "Great answer!"
