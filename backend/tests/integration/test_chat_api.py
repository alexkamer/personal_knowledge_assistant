"""
Integration tests for the chat API endpoints.
"""
import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, Mock, patch


class TestChatAPI:
    """Test suite for the main chat endpoint."""

    @pytest.mark.asyncio
    @patch('app.api.v1.endpoints.chat.get_llm_service')
    @patch('app.api.v1.endpoints.chat.get_rag_service')
    @patch('app.api.v1.endpoints.chat.get_token_counter')
    async def test_chat_creates_new_conversation(
        self, mock_token_counter, mock_rag_service, mock_llm_service, client: AsyncClient
    ):
        """Test sending a message creates a new conversation."""
        # Mock services
        mock_llm = Mock()
        mock_llm.generate_answer = AsyncMock(return_value="Test answer")
        mock_llm.generate_follow_up_questions = AsyncMock(return_value=["Question 1?", "Question 2?"])
        mock_llm.primary_model = "qwen2.5:14b"
        mock_llm_service.return_value = mock_llm

        mock_rag = Mock()
        mock_rag.retrieve_and_assemble = AsyncMock(return_value=("Test context", []))
        mock_rag_service.return_value = mock_rag

        mock_counter = Mock()
        mock_counter.count_tokens.return_value = 10
        mock_token_counter.return_value = mock_counter

        response = await client.post(
            "/api/v1/chat/",
            json={
                "message": "What is testing?",
                "conversation_title": "Test Conversation",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "conversation_id" in data
        assert "message_id" in data
        assert data["response"] == "Test answer"
        assert "sources" in data
        assert data["model_used"] == "qwen2.5:14b"

    @pytest.mark.asyncio
    @patch('app.api.v1.endpoints.chat.get_llm_service')
    @patch('app.api.v1.endpoints.chat.get_rag_service')
    @patch('app.api.v1.endpoints.chat.get_token_counter')
    async def test_chat_uses_existing_conversation(
        self, mock_token_counter, mock_rag_service, mock_llm_service, client: AsyncClient
    ):
        """Test sending a message to an existing conversation."""
        # Mock services
        mock_llm = Mock()
        mock_llm.generate_answer = AsyncMock(return_value="Follow-up answer")
        mock_llm.generate_follow_up_questions = AsyncMock(return_value=["Question 1?", "Question 2?"])
        mock_llm.primary_model = "qwen2.5:14b"
        mock_llm_service.return_value = mock_llm

        mock_rag = Mock()
        mock_rag.retrieve_and_assemble = AsyncMock(return_value=("Context", []))
        mock_rag_service.return_value = mock_rag

        mock_counter = Mock()
        mock_counter.count_tokens.return_value = 10
        mock_token_counter.return_value = mock_counter

        # Create first conversation
        first_response = await client.post(
            "/api/v1/chat/",
            json={"message": "First message"},
        )
        conversation_id = first_response.json()["conversation_id"]

        # Send follow-up message
        response = await client.post(
            "/api/v1/chat/",
            json={
                "message": "Follow-up message",
                "conversation_id": conversation_id,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["conversation_id"] == conversation_id
        assert data["response"] == "Follow-up answer"


class TestConversationsAPI:
    """Test suite for conversation endpoints."""

    @pytest.mark.asyncio
    @patch('app.api.v1.endpoints.chat.get_llm_service')
    @patch('app.api.v1.endpoints.chat.get_rag_service')
    @patch('app.api.v1.endpoints.chat.get_token_counter')
    async def test_list_conversations(
        self, mock_token_counter, mock_rag_service, mock_llm_service, client: AsyncClient
    ):
        """Test listing conversations."""
        # Mock services for chat endpoint
        mock_llm = Mock()
        mock_llm.generate_answer = AsyncMock(return_value="Answer")
        mock_llm.generate_follow_up_questions = AsyncMock(return_value=["Question 1?", "Question 2?"])
        mock_llm.primary_model = "qwen2.5:14b"
        mock_llm_service.return_value = mock_llm

        mock_rag = Mock()
        mock_rag.retrieve_and_assemble = AsyncMock(return_value=("", []))
        mock_rag_service.return_value = mock_rag

        mock_counter = Mock()
        mock_counter.count_tokens.return_value = 10
        mock_token_counter.return_value = mock_counter

        # Create a conversation by sending a message
        await client.post(
            "/api/v1/chat/",
            json={"message": "Test message", "conversation_title": "Test 1"},
        )

        # List conversations
        response = await client.get("/api/v1/chat/conversations/")

        assert response.status_code == 200
        data = response.json()
        assert "conversations" in data
        assert "total" in data
        assert len(data["conversations"]) >= 1

    @pytest.mark.asyncio
    @patch('app.api.v1.endpoints.chat.get_llm_service')
    @patch('app.api.v1.endpoints.chat.get_rag_service')
    @patch('app.api.v1.endpoints.chat.get_token_counter')
    async def test_get_conversation_by_id(
        self, mock_token_counter, mock_rag_service, mock_llm_service, client: AsyncClient
    ):
        """Test getting a conversation by ID."""
        # Mock services
        mock_llm = Mock()
        mock_llm.generate_answer = AsyncMock(return_value="Answer")
        mock_llm.generate_follow_up_questions = AsyncMock(return_value=["Question 1?", "Question 2?"])
        mock_llm.primary_model = "qwen2.5:14b"
        mock_llm_service.return_value = mock_llm

        mock_rag = Mock()
        mock_rag.retrieve_and_assemble = AsyncMock(return_value=("", []))
        mock_rag_service.return_value = mock_rag

        mock_counter = Mock()
        mock_counter.count_tokens.return_value = 10
        mock_token_counter.return_value = mock_counter

        # Create a conversation
        create_response = await client.post(
            "/api/v1/chat/",
            json={"message": "Test", "conversation_title": "Test Conversation"},
        )
        conversation_id = create_response.json()["conversation_id"]

        # Get the conversation
        response = await client.get(f"/api/v1/chat/conversations/{conversation_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == conversation_id
        assert data["title"] == "Test Conversation"
        assert "messages" in data
        assert len(data["messages"]) == 2  # User message + Assistant message

    @pytest.mark.asyncio
    async def test_get_nonexistent_conversation(self, client: AsyncClient):
        """Test getting a conversation that doesn't exist."""
        response = await client.get("/api/v1/chat/conversations/nonexistent-id")

        assert response.status_code == 404

    @pytest.mark.asyncio
    @patch('app.api.v1.endpoints.chat.get_llm_service')
    @patch('app.api.v1.endpoints.chat.get_rag_service')
    @patch('app.api.v1.endpoints.chat.get_token_counter')
    async def test_update_conversation(
        self, mock_token_counter, mock_rag_service, mock_llm_service, client: AsyncClient
    ):
        """Test updating a conversation."""
        # Mock services
        mock_llm = Mock()
        mock_llm.generate_answer = AsyncMock(return_value="Answer")
        mock_llm.generate_follow_up_questions = AsyncMock(return_value=["Question 1?", "Question 2?"])
        mock_llm.primary_model = "qwen2.5:14b"
        mock_llm_service.return_value = mock_llm

        mock_rag = Mock()
        mock_rag.retrieve_and_assemble = AsyncMock(return_value=("", []))
        mock_rag_service.return_value = mock_rag

        mock_counter = Mock()
        mock_counter.count_tokens.return_value = 10
        mock_token_counter.return_value = mock_counter

        # Create a conversation
        create_response = await client.post(
            "/api/v1/chat/",
            json={"message": "Test", "conversation_title": "Original Title"},
        )
        conversation_id = create_response.json()["conversation_id"]

        # Update the conversation (use PATCH, not PUT)
        response = await client.patch(
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
    @patch('app.api.v1.endpoints.chat.get_llm_service')
    @patch('app.api.v1.endpoints.chat.get_rag_service')
    @patch('app.api.v1.endpoints.chat.get_token_counter')
    async def test_delete_conversation(
        self, mock_token_counter, mock_rag_service, mock_llm_service, client: AsyncClient
    ):
        """Test deleting a conversation."""
        # Mock services
        mock_llm = Mock()
        mock_llm.generate_answer = AsyncMock(return_value="Answer")
        mock_llm.generate_follow_up_questions = AsyncMock(return_value=["Question 1?", "Question 2?"])
        mock_llm.primary_model = "qwen2.5:14b"
        mock_llm_service.return_value = mock_llm

        mock_rag = Mock()
        mock_rag.retrieve_and_assemble = AsyncMock(return_value=("", []))
        mock_rag_service.return_value = mock_rag

        mock_counter = Mock()
        mock_counter.count_tokens.return_value = 10
        mock_token_counter.return_value = mock_counter

        # Create a conversation
        create_response = await client.post(
            "/api/v1/chat/",
            json={"message": "Test", "conversation_title": "To Delete"},
        )
        conversation_id = create_response.json()["conversation_id"]

        # Delete the conversation
        response = await client.delete(f"/api/v1/chat/conversations/{conversation_id}")

        assert response.status_code == 204

        # Verify it's deleted
        get_response = await client.get(f"/api/v1/chat/conversations/{conversation_id}")
        assert get_response.status_code == 404


class TestMessageFeedbackAPI:
    """Test suite for message feedback endpoints."""

    @pytest.mark.asyncio
    @patch('app.api.v1.endpoints.chat.get_llm_service')
    @patch('app.api.v1.endpoints.chat.get_rag_service')
    @patch('app.api.v1.endpoints.chat.get_token_counter')
    async def test_submit_feedback(
        self, mock_token_counter, mock_rag_service, mock_llm_service, client: AsyncClient
    ):
        """Test submitting feedback for a message."""
        # Mock services
        mock_llm = Mock()
        mock_llm.generate_answer = AsyncMock(return_value="Test response")
        mock_llm.generate_follow_up_questions = AsyncMock(return_value=["Question 1?", "Question 2?"])
        mock_llm.primary_model = "qwen2.5:14b"
        mock_llm_service.return_value = mock_llm

        mock_rag = Mock()
        mock_rag.retrieve_and_assemble = AsyncMock(return_value=("", []))
        mock_rag_service.return_value = mock_rag

        mock_counter = Mock()
        mock_counter.count_tokens.return_value = 10
        mock_token_counter.return_value = mock_counter

        # Create a conversation and get assistant message ID
        chat_response = await client.post(
            "/api/v1/chat/",
            json={"message": "Test question"},
        )
        message_id = chat_response.json()["message_id"]

        # Submit positive feedback
        response = await client.post(
            f"/api/v1/chat/messages/{message_id}/feedback",
            json={"is_positive": True, "comment": "Great answer!"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_positive"] is True
        assert data["comment"] == "Great answer!"
        assert data["message_id"] == message_id
