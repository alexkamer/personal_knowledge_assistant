"""
Token counting utilities for tracking context window usage.
"""
import logging
from typing import List, Dict

import tiktoken

logger = logging.getLogger(__name__)


class TokenCounter:
    """Utility for counting tokens in text and conversations."""

    # Model context limits (tokens)
    MODEL_LIMITS = {
        "qwen2.5:14b": 32768,  # Qwen 2.5 14B has 32k context
        "phi4:14b": 16384,  # Phi-4 14B has 16k context
        "llama3.2:3b": 8192,  # Llama 3.2 3B has 8k context
        "default": 32768,  # Default conservative estimate
    }

    def __init__(self, encoding_name: str = "cl100k_base"):
        """
        Initialize token counter.

        Args:
            encoding_name: tiktoken encoding to use (cl100k_base is for GPT-4/modern models)
        """
        try:
            self.encoding = tiktoken.get_encoding(encoding_name)
        except Exception as e:
            logger.warning(f"Failed to load tiktoken encoding {encoding_name}: {e}")
            logger.warning("Falling back to character-based approximation")
            self.encoding = None

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in a text string.

        Args:
            text: Text to count tokens for

        Returns:
            Number of tokens
        """
        if not text:
            return 0

        if self.encoding:
            try:
                return len(self.encoding.encode(text))
            except Exception as e:
                logger.warning(f"Token counting error: {e}, falling back to approximation")

        # Fallback: rough approximation (1 token ~= 4 characters)
        return len(text) // 4

    def count_message_tokens(self, message: Dict[str, str]) -> int:
        """
        Count tokens in a message dictionary.

        Args:
            message: Message dict with 'role' and 'content'

        Returns:
            Number of tokens including role overhead
        """
        # Count role + content + message formatting overhead (~4 tokens per message)
        role_tokens = self.count_tokens(message.get("role", ""))
        content_tokens = self.count_tokens(message.get("content", ""))
        return role_tokens + content_tokens + 4  # +4 for message formatting

    def count_conversation_tokens(self, messages: List[Dict[str, str]]) -> int:
        """
        Count total tokens in a conversation.

        Args:
            messages: List of message dicts with 'role' and 'content'

        Returns:
            Total token count for the conversation
        """
        return sum(self.count_message_tokens(msg) for msg in messages)

    def estimate_context_usage(
        self,
        messages: List[Dict[str, str]],
        model: str = "default",
    ) -> Dict[str, any]:
        """
        Calculate context window usage statistics.

        Args:
            messages: List of message dicts
            model: Model name for context limit lookup

        Returns:
            Dict with usage statistics:
                - total_tokens: Total tokens used
                - limit: Context window limit
                - usage_percent: Percentage of context used (0-100)
                - remaining: Tokens remaining
                - is_warning: True if > 70% used
                - is_critical: True if > 90% used
        """
        total_tokens = self.count_conversation_tokens(messages)
        limit = self.MODEL_LIMITS.get(model, self.MODEL_LIMITS["default"])
        usage_percent = (total_tokens / limit) * 100
        remaining = limit - total_tokens

        return {
            "total_tokens": total_tokens,
            "limit": limit,
            "usage_percent": round(usage_percent, 1),
            "remaining": remaining,
            "is_warning": usage_percent > 70,
            "is_critical": usage_percent > 90,
        }

    @staticmethod
    def get_model_limit(model: str) -> int:
        """
        Get context window limit for a model.

        Args:
            model: Model name

        Returns:
            Context window size in tokens
        """
        return TokenCounter.MODEL_LIMITS.get(model, TokenCounter.MODEL_LIMITS["default"])


# Global instance
_token_counter: TokenCounter | None = None


def get_token_counter() -> TokenCounter:
    """
    Get the global token counter instance.

    Returns:
        TokenCounter singleton
    """
    global _token_counter
    if _token_counter is None:
        _token_counter = TokenCounter()
    return _token_counter
