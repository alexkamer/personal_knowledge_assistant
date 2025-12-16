"""
Unit tests for the LLM service.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import ollama

from app.services.llm_service import LLMService, get_llm_service
from app.core.exceptions import ModelNotFoundError, OllamaConnectionError


class TestLLMService:
    """Test suite for LLMService."""

    @patch('app.services.llm_service.ollama.AsyncClient')
    def test_initialization(self, mock_client):
        """Test LLM service initialization."""
        service = LLMService()

        assert service.client is not None
        assert service.primary_model is not None
        assert service.timeout is not None
        mock_client.assert_called_once()

    @patch('app.services.llm_service.ollama.AsyncClient')
    @pytest.mark.asyncio
    async def test_generate_answer_basic(self, mock_client):
        """Test generating a basic answer without streaming."""
        # Setup mock
        mock_instance = AsyncMock()
        mock_client.return_value = mock_instance
        mock_instance.chat.return_value = {
            "message": {"content": "Test answer"}
        }

        service = LLMService()
        answer = await service.generate_answer(
            query="What is testing?",
            context="Testing is important.",
            stream=False,
        )

        assert answer == "Test answer"
        mock_instance.chat.assert_called_once()

        # Verify the call arguments
        call_args = mock_instance.chat.call_args
        assert call_args[1]["model"] == service.primary_model
        assert len(call_args[1]["messages"]) == 2  # System + User message

    @patch('app.services.llm_service.ollama.AsyncClient')
    @pytest.mark.asyncio
    async def test_generate_answer_with_conversation_history(self, mock_client):
        """Test generating answer with conversation history."""
        mock_instance = AsyncMock()
        mock_client.return_value = mock_instance
        mock_instance.chat.return_value = {
            "message": {"content": "Follow-up answer"}
        }

        service = LLMService()
        conversation_history = [
            {"role": "user", "content": "First question"},
            {"role": "assistant", "content": "First answer"},
        ]

        answer = await service.generate_answer(
            query="Follow-up question",
            context="",
            conversation_history=conversation_history,
            stream=False,
        )

        assert answer == "Follow-up answer"

        # Verify conversation history was included
        call_args = mock_instance.chat.call_args
        messages = call_args[1]["messages"]
        assert len(messages) == 4  # System + 2 history + User

    @patch('app.services.llm_service.ollama.AsyncClient')
    @pytest.mark.asyncio
    async def test_generate_answer_with_custom_model(self, mock_client):
        """Test generating answer with custom model."""
        mock_instance = AsyncMock()
        mock_client.return_value = mock_instance
        mock_instance.chat.return_value = {
            "message": {"content": "Custom model answer"}
        }

        service = LLMService()
        answer = await service.generate_answer(
            query="Test query",
            context="",
            model="custom-model:latest",
            stream=False,
        )

        assert answer == "Custom model answer"

        # Verify custom model was used
        call_args = mock_instance.chat.call_args
        assert call_args[1]["model"] == "custom-model:latest"

    @patch('app.services.llm_service.ollama.AsyncClient')
    @pytest.mark.asyncio
    async def test_generate_answer_with_custom_temperature(self, mock_client):
        """Test generating answer with custom temperature."""
        mock_instance = AsyncMock()
        mock_client.return_value = mock_instance
        mock_instance.chat.return_value = {
            "message": {"content": "Answer"}
        }

        service = LLMService()
        await service.generate_answer(
            query="Test",
            context="",
            temperature=0.5,
            stream=False,
        )

        # Verify temperature was set
        call_args = mock_instance.chat.call_args
        assert call_args[1]["options"]["temperature"] == 0.5

    @patch('app.services.llm_service.ollama.AsyncClient')
    @pytest.mark.asyncio
    async def test_generate_answer_with_custom_system_prompt(self, mock_client):
        """Test generating answer with custom system prompt."""
        mock_instance = AsyncMock()
        mock_client.return_value = mock_instance
        mock_instance.chat.return_value = {
            "message": {"content": "Answer"}
        }

        service = LLMService()
        custom_prompt = "You are a specialized assistant."

        await service.generate_answer(
            query="Test",
            context="",
            system_prompt=custom_prompt,
            stream=False,
        )

        # Verify custom system prompt was used
        call_args = mock_instance.chat.call_args
        messages = call_args[1]["messages"]
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == custom_prompt

    @patch('app.services.llm_service.ollama.AsyncClient')
    @pytest.mark.asyncio
    async def test_generate_answer_model_not_found_error(self, mock_client):
        """Test handling of model not found error."""
        mock_instance = AsyncMock()
        mock_client.return_value = mock_instance
        mock_instance.chat.side_effect = ollama.ResponseError("model not found")

        service = LLMService()

        with pytest.raises(ModelNotFoundError):
            await service.generate_answer(
                query="Test",
                context="",
                model="nonexistent-model",
                stream=False,
            )

    @patch('app.services.llm_service.ollama.AsyncClient')
    @pytest.mark.asyncio
    async def test_generate_answer_connection_error(self, mock_client):
        """Test handling of Ollama connection error."""
        mock_instance = AsyncMock()
        mock_client.return_value = mock_instance
        mock_instance.chat.side_effect = ollama.RequestError("Connection refused")

        service = LLMService()

        with pytest.raises(OllamaConnectionError):
            await service.generate_answer(
                query="Test",
                context="",
                stream=False,
            )

    @patch('app.services.llm_service.ollama.AsyncClient')
    @pytest.mark.asyncio
    async def test_generate_follow_up_questions(self, mock_client):
        """Test generating follow-up questions."""
        mock_instance = AsyncMock()
        mock_client.return_value = mock_instance
        mock_instance.chat.return_value = {
            "message": {
                "content": "Question 1?\nQuestion 2?\nQuestion 3?"
            }
        }

        service = LLMService()
        questions = await service.generate_follow_up_questions(
            query="What is testing?",
            answer="Testing is important for quality.",
            context="Context about testing",
        )

        assert len(questions) == 3
        assert "Question 1?" in questions
        assert "Question 2?" in questions
        assert "Question 3?" in questions

    @patch('app.services.llm_service.ollama.AsyncClient')
    @pytest.mark.asyncio
    async def test_generate_follow_up_questions_empty_on_error(self, mock_client):
        """Test that follow-up questions returns empty list on error."""
        mock_instance = AsyncMock()
        mock_client.return_value = mock_instance
        mock_instance.chat.side_effect = Exception("Test error")

        service = LLMService()
        questions = await service.generate_follow_up_questions(
            query="Test",
            answer="Answer",
            context="",
        )

        assert questions == []

    @patch('app.services.llm_service.ollama.AsyncClient')
    @pytest.mark.asyncio
    async def test_generate_follow_up_questions_filters_short_lines(self, mock_client):
        """Test that short lines are filtered from follow-up questions."""
        mock_instance = AsyncMock()
        mock_client.return_value = mock_instance
        mock_instance.chat.return_value = {
            "message": {
                "content": "Good question?\nShort\nAnother good question here?"
            }
        }

        service = LLMService()
        questions = await service.generate_follow_up_questions(
            query="Test",
            answer="Answer",
            context="",
        )

        # Should only include questions longer than 10 characters
        assert len(questions) == 2
        assert "Good question?" in questions
        assert "Another good question here?" in questions

    @patch('app.services.llm_service.ollama.AsyncClient')
    @pytest.mark.asyncio
    async def test_generate_follow_up_questions_max_four(self, mock_client):
        """Test that follow-up questions are limited to 4."""
        mock_instance = AsyncMock()
        mock_client.return_value = mock_instance
        mock_instance.chat.return_value = {
            "message": {
                "content": "\n".join([f"Question {i}?" for i in range(10)])
            }
        }

        service = LLMService()
        questions = await service.generate_follow_up_questions(
            query="Test",
            answer="Answer",
            context="",
        )

        assert len(questions) == 4

    @patch('app.services.llm_service.ollama.AsyncClient')
    @pytest.mark.asyncio
    async def test_list_available_models(self, mock_client):
        """Test listing available models."""
        mock_instance = AsyncMock()
        mock_client.return_value = mock_instance
        mock_instance.list.return_value = {
            "models": [
                {"name": "model1", "size": 1000},
                {"name": "model2", "size": 2000},
            ]
        }

        service = LLMService()
        models = await service.list_available_models()

        assert len(models) == 2
        assert models[0]["name"] == "model1"
        assert models[1]["name"] == "model2"

    @patch('app.services.llm_service.ollama.AsyncClient')
    @pytest.mark.asyncio
    async def test_list_available_models_empty_on_error(self, mock_client):
        """Test that list_available_models returns empty list on error."""
        mock_instance = AsyncMock()
        mock_client.return_value = mock_instance
        mock_instance.list.side_effect = Exception("Connection error")

        service = LLMService()
        models = await service.list_available_models()

        assert models == []

    @patch('app.services.llm_service.ollama.AsyncClient')
    @pytest.mark.asyncio
    async def test_check_model_available_true(self, mock_client):
        """Test checking if a model is available (positive case)."""
        mock_instance = AsyncMock()
        mock_client.return_value = mock_instance
        mock_instance.list.return_value = {
            "models": [
                {"name": "test-model"},
            ]
        }

        service = LLMService()
        is_available = await service.check_model_available("test-model")

        assert is_available is True

    @patch('app.services.llm_service.ollama.AsyncClient')
    @pytest.mark.asyncio
    async def test_check_model_available_false(self, mock_client):
        """Test checking if a model is available (negative case)."""
        mock_instance = AsyncMock()
        mock_client.return_value = mock_instance
        mock_instance.list.return_value = {
            "models": [
                {"name": "other-model"},
            ]
        }

        service = LLMService()
        is_available = await service.check_model_available("nonexistent-model")

        assert is_available is False

    def test_build_system_prompt(self):
        """Test building system prompt."""
        service = LLMService()
        prompt = service._build_system_prompt()

        assert "helpful AI assistant" in prompt
        assert "knowledge management" in prompt

    def test_build_user_message_with_context(self):
        """Test building user message with context."""
        service = LLMService()
        message = service._build_user_message("What is X?", "Context about X")

        assert "What is X?" in message
        assert "Context about X" in message
        assert "Available context" in message

    def test_build_user_message_without_context(self):
        """Test building user message without context."""
        service = LLMService()
        message = service._build_user_message("General question", "")

        assert message == "General question"
        assert "Available context" not in message

    @patch('app.services.llm_service.LLMService')
    def test_get_llm_service_singleton(self, mock_service_class):
        """Test get_llm_service returns singleton."""
        # Reset the global instance
        import app.services.llm_service
        app.services.llm_service._llm_service = None

        # Create mock instance
        mock_instance = Mock()
        mock_service_class.return_value = mock_instance

        service1 = get_llm_service()
        service2 = get_llm_service()

        # Should return the same instance
        assert service1 is service2
        mock_service_class.assert_called_once()
