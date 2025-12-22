"""
Service for generating concise conversation titles using AI.
"""
import logging
from typing import Optional

import ollama

from app.core.config import settings

logger = logging.getLogger(__name__)


class TitleGeneratorService:
    """Service for generating short, descriptive conversation titles."""

    def __init__(self):
        """Initialize title generator service."""
        self.client = ollama.AsyncClient(host=settings.ollama_base_url)
        # Use the fastest, smallest model to minimize tokens
        self.model = "llama3.2:3b"
        self.timeout = 10  # Short timeout for title generation

    async def generate_title(
        self,
        first_message: str,
        first_response: Optional[str] = None,
    ) -> str:
        """
        Generate a concise title (2-5 words) for a conversation.

        Args:
            first_message: The user's first message
            first_response: The assistant's first response (optional, for better context)

        Returns:
            A short, descriptive title (2-5 words)
        """
        try:
            # Build a minimal prompt to reduce token usage
            context = f"User: {first_message}"
            if first_response:
                # Truncate response to first 200 chars to save tokens
                context += f"\nAssistant: {first_response[:200]}"

            prompt = f"""{context}

Generate a 2-5 word title for this conversation. Be concise and descriptive. No quotes or punctuation."""

            logger.info(f"Generating title for conversation starting with: {first_message[:50]}...")

            # Use minimal options to reduce overhead
            response = await self.client.generate(
                model=self.model,
                prompt=prompt,
                options={
                    "temperature": 0.3,  # Lower temperature for more focused output
                    "num_predict": 15,  # Limit to ~15 tokens (2-5 words)
                    "stop": ["\n", ".", "!", "?"],  # Stop at punctuation
                },
            )

            title = response["response"].strip()

            # Clean up the title
            title = title.replace('"', '').replace("'", '').strip()

            # Truncate if too long
            if len(title) > 50:
                title = title[:50].rsplit(' ', 1)[0]

            # Fallback if generation fails or is empty
            if not title or len(title) < 3:
                title = first_message[:40].strip()
                if len(title) < len(first_message):
                    title += "..."

            logger.info(f"Generated title: {title}")
            return title

        except Exception as e:
            logger.error(f"Error generating title: {e}")
            # Fallback to truncated first message
            fallback = first_message[:40].strip()
            if len(fallback) < len(first_message):
                fallback += "..."
            return fallback


# Singleton instance
_title_generator_service: Optional[TitleGeneratorService] = None


def get_title_generator_service() -> TitleGeneratorService:
    """Get or create the title generator service singleton."""
    global _title_generator_service
    if _title_generator_service is None:
        _title_generator_service = TitleGeneratorService()
    return _title_generator_service
