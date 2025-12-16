"""
Unit tests for the TokenCounter utility.
"""
import pytest
from unittest.mock import patch, Mock

from app.utils.token_counter import TokenCounter, get_token_counter


class TestTokenCounter:
    """Test suite for TokenCounter."""

    def test_initialization_success(self):
        """Test successful initialization with tiktoken."""
        counter = TokenCounter()

        assert counter.encoding is not None

    @patch('app.utils.token_counter.tiktoken.get_encoding')
    def test_initialization_fallback(self, mock_get_encoding):
        """Test fallback when tiktoken fails to load."""
        mock_get_encoding.side_effect = Exception("Failed to load encoding")

        counter = TokenCounter()

        assert counter.encoding is None

    def test_count_tokens_empty_string(self):
        """Test counting tokens for empty string."""
        counter = TokenCounter()

        count = counter.count_tokens("")

        assert count == 0

    def test_count_tokens_with_encoding(self):
        """Test token counting with tiktoken encoding."""
        counter = TokenCounter()

        # Simple English text
        count = counter.count_tokens("Hello, world!")

        # Should use tiktoken encoding
        assert count > 0
        assert isinstance(count, int)

    @patch('app.utils.token_counter.tiktoken.get_encoding')
    def test_count_tokens_fallback_approximation(self, mock_get_encoding):
        """Test fallback to character-based approximation."""
        mock_get_encoding.side_effect = Exception("Failed")
        counter = TokenCounter()

        # "Hello world!" is 12 characters
        count = counter.count_tokens("Hello world!")

        # Should use approximation: 12 / 4 = 3 tokens
        assert count == 3

    def test_count_tokens_with_encoding_error_fallback(self):
        """Test fallback when encoding.encode() fails."""
        counter = TokenCounter()

        # Mock encoding to raise error
        mock_encoding = Mock()
        mock_encoding.encode.side_effect = Exception("Encoding error")
        counter.encoding = mock_encoding

        # Should fallback to approximation
        count = counter.count_tokens("Test text here")  # 14 chars

        assert count == 3  # 14 / 4 = 3

    def test_count_message_tokens_basic(self):
        """Test counting tokens in a message."""
        counter = TokenCounter()

        message = {
            "role": "user",
            "content": "Hello, how are you?"
        }

        count = counter.count_message_tokens(message)

        # Should include role + content + overhead (+4)
        assert count > 4  # At minimum the overhead

    def test_count_message_tokens_missing_fields(self):
        """Test counting tokens with missing message fields."""
        counter = TokenCounter()

        # Missing role
        message = {"content": "Test content"}
        count = counter.count_message_tokens(message)
        assert count >= 4  # At least overhead

        # Missing content
        message = {"role": "user"}
        count = counter.count_message_tokens(message)
        assert count >= 4

        # Empty message
        message = {}
        count = counter.count_message_tokens(message)
        assert count == 4  # Just overhead

    def test_count_conversation_tokens_empty(self):
        """Test counting tokens in empty conversation."""
        counter = TokenCounter()

        count = counter.count_conversation_tokens([])

        assert count == 0

    def test_count_conversation_tokens_multiple_messages(self):
        """Test counting tokens in multi-message conversation."""
        counter = TokenCounter()

        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there! How can I help?"},
            {"role": "user", "content": "Tell me about AI"},
        ]

        count = counter.count_conversation_tokens(messages)

        # Should be sum of all message tokens
        assert count > 0
        # Should be at least 3 * 4 = 12 (overhead for 3 messages)
        assert count >= 12

    def test_estimate_context_usage_default_model(self):
        """Test context usage estimation with default model."""
        counter = TokenCounter()

        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]

        usage = counter.estimate_context_usage(messages)

        assert "total_tokens" in usage
        assert "limit" in usage
        assert "usage_percent" in usage
        assert "remaining" in usage
        assert "is_warning" in usage
        assert "is_critical" in usage

        assert usage["limit"] == 32768  # Default limit
        assert usage["remaining"] == usage["limit"] - usage["total_tokens"]
        assert usage["is_warning"] is False  # Low usage
        assert usage["is_critical"] is False

    def test_estimate_context_usage_specific_models(self):
        """Test context usage with specific model limits."""
        counter = TokenCounter()

        messages = [{"role": "user", "content": "Test"}]

        # Test Qwen 2.5
        usage = counter.estimate_context_usage(messages, model="qwen2.5:14b")
        assert usage["limit"] == 32768

        # Test Phi-4
        usage = counter.estimate_context_usage(messages, model="phi4:14b")
        assert usage["limit"] == 16384

        # Test Llama 3.2
        usage = counter.estimate_context_usage(messages, model="llama3.2:3b")
        assert usage["limit"] == 8192

        # Test unknown model (should use default)
        usage = counter.estimate_context_usage(messages, model="unknown-model")
        assert usage["limit"] == 32768

    def test_estimate_context_usage_warning_threshold(self):
        """Test warning threshold at 70% usage."""
        counter = TokenCounter()

        # Create messages that use ~74% of context (above 70% warning threshold)
        # Llama 3.2 has 8192 tokens
        # Use varied text to get accurate token count
        line = "The quick brown fox jumps over the lazy dog in the meadow today. " * 5
        # 80 repetitions gives ~74% usage
        large_text = (line + "\n") * 80
        messages = [{"role": "user", "content": large_text}]

        usage = counter.estimate_context_usage(messages, model="llama3.2:3b")

        assert usage["is_warning"] is True
        assert usage["is_critical"] is False
        assert usage["usage_percent"] > 70

    def test_estimate_context_usage_critical_threshold(self):
        """Test critical threshold at 90% usage."""
        counter = TokenCounter()

        # Create messages that use ~91% of context (above 90% critical threshold)
        # Llama 3.2 has 8192 tokens
        # Use varied text to get accurate token count
        line = "The quick brown fox jumps over the lazy dog in the meadow today. " * 5
        # 98 repetitions gives ~91% usage
        large_text = (line + "\n") * 98
        messages = [{"role": "user", "content": large_text}]

        usage = counter.estimate_context_usage(messages, model="llama3.2:3b")

        assert usage["is_warning"] is True
        assert usage["is_critical"] is True
        assert usage["usage_percent"] > 90

    def test_estimate_context_usage_percentage_rounding(self):
        """Test that usage percentage is rounded to 1 decimal place."""
        counter = TokenCounter()

        messages = [{"role": "user", "content": "Test"}]

        usage = counter.estimate_context_usage(messages)

        # Check that usage_percent has at most 1 decimal place
        assert isinstance(usage["usage_percent"], float)
        assert usage["usage_percent"] == round(usage["usage_percent"], 1)

    def test_get_model_limit_known_models(self):
        """Test getting model limits for known models."""
        assert TokenCounter.get_model_limit("qwen2.5:14b") == 32768
        assert TokenCounter.get_model_limit("phi4:14b") == 16384
        assert TokenCounter.get_model_limit("llama3.2:3b") == 8192

    def test_get_model_limit_unknown_model(self):
        """Test getting model limit for unknown model."""
        assert TokenCounter.get_model_limit("unknown-model") == 32768  # Default

    def test_get_model_limit_empty_string(self):
        """Test getting model limit for empty string."""
        assert TokenCounter.get_model_limit("") == 32768  # Default

    @patch('app.utils.token_counter.TokenCounter')
    def test_get_token_counter_singleton(self, mock_counter_class):
        """Test get_token_counter returns singleton."""
        # Reset the global instance
        import app.utils.token_counter
        app.utils.token_counter._token_counter = None

        # Create mock instance
        mock_instance = Mock()
        mock_counter_class.return_value = mock_instance

        counter1 = get_token_counter()
        counter2 = get_token_counter()

        # Should return the same instance
        assert counter1 is counter2
        mock_counter_class.assert_called_once()

    def test_count_tokens_various_text_lengths(self):
        """Test token counting with various text lengths."""
        counter = TokenCounter()

        # Short text
        short_count = counter.count_tokens("Hi")
        assert short_count > 0

        # Medium text
        medium_text = "This is a medium length sentence with several words."
        medium_count = counter.count_tokens(medium_text)
        assert medium_count > short_count

        # Long text
        long_text = medium_text * 10
        long_count = counter.count_tokens(long_text)
        assert long_count > medium_count

    def test_count_message_tokens_long_content(self):
        """Test counting tokens in message with long content."""
        counter = TokenCounter()

        message = {
            "role": "assistant",
            "content": "This is a long assistant response. " * 50
        }

        count = counter.count_message_tokens(message)

        # Should be significantly more than overhead
        assert count > 100
