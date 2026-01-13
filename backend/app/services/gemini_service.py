"""
Service for interacting with Google's Gemini API.
"""

import logging
from typing import AsyncIterator, Optional

from google import genai
from google.genai import types

from app.core.config import settings

logger = logging.getLogger(__name__)


class GeminiService:
    """Service for generating responses using Google's Gemini API."""

    def __init__(self):
        """Initialize Gemini service."""
        if not settings.gemini_api_key:
            logger.warning("Gemini API key not configured")
            self.client = None
            return

        # Use Google AI API (not Vertex AI)
        # Explicitly disable Vertex AI to override environment variables
        self.client = genai.Client(api_key=settings.gemini_api_key, vertexai=False)
        logger.info("Gemini service initialized (Google AI API mode)")

    def _build_system_prompt(self) -> str:
        """
        Build system prompt that allows blending context with general knowledge.

        This prompt enables the AI to:
        - Use document context when relevant
        - Supplement with general knowledge for complete answers
        - Provide natural citations only when using specific facts
        - Ignore irrelevant context gracefully
        - Include inline citation numbers for source tracking
        """
        return """You are a helpful AI assistant for a personal knowledge management system.

Your role is to provide complete, accurate answers by combining the user's documents with your general knowledge.

Key principles:
- Use the provided context when it contains relevant information
- Supplement with your general knowledge to give complete, helpful answers
- Don't say "the context doesn't contain" - if documents are incomplete, use what you know
- If context is irrelevant to the question, it's okay to ignore it completely
- Be conversational and natural - avoid robotic phrases
- Check conversation history for context (pronouns, "that", "it", follow-ups)

Citation style (IMPORTANT):
- When using information from a provided source, add a citation number immediately after the statement
- Format: Add [N] where N is the source number from the context (e.g., "The study found that AI improves productivity[1].")
- You can cite multiple sources: "This is supported by research[1][2]."
- Only cite when actually using specific facts from the sources
- Don't cite for general knowledge or common facts
- Natural language mentions are still good: "According to your notes on X[2], ..."

Example:
Context includes [Source 1: Research Paper] and [Source 2: Meeting Notes]
Your response: "Recent studies show AI increases productivity by 40%[1]. In your last meeting, the team discussed implementation strategies[2]."

Remember: Users want helpful complete answers with clear source attribution when you use their documents."""

    async def generate_response(
        self,
        prompt: str,
        model: str = "gemini-1.5-flash",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        Generate a non-streaming response using Gemini.

        Args:
            prompt: The prompt to send to Gemini
            model: The Gemini model to use (gemini-1.5-flash or gemini-1.5-pro)
            temperature: Temperature for response generation (0.0-1.0)
            max_tokens: Maximum tokens to generate (optional)
            system_prompt: System instruction for the model (uses default if not provided)

        Returns:
            The generated response text

        Raises:
            Exception: If Gemini API is not configured or request fails
        """
        if not self.client:
            raise Exception("Gemini API key not configured")

        try:
            logger.info(f"Generating response with {model}")

            # Create generation config
            config_params = {
                "temperature": temperature,
                "system_instruction": system_prompt or self._build_system_prompt(),
            }
            if max_tokens:
                config_params["max_output_tokens"] = max_tokens

            config = types.GenerateContentConfig(**config_params)

            # Generate response
            response = self.client.models.generate_content(
                model=model,
                contents=prompt,
                config=config,
            )

            return response.text

        except Exception as e:
            logger.error(f"Error generating Gemini response: {e}")
            raise

    async def generate_response_stream(
        self,
        prompt: str,
        model: str = "gemini-1.5-flash",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
    ) -> AsyncIterator[str]:
        """
        Generate a streaming response using Gemini.

        Args:
            prompt: The prompt to send to Gemini
            model: The Gemini model to use (gemini-1.5-flash or gemini-1.5-pro)
            temperature: Temperature for response generation (0.0-1.0)
            max_tokens: Maximum tokens to generate (optional)
            system_prompt: System instruction for the model (uses default if not provided)

        Yields:
            Text chunks as they are generated

        Raises:
            Exception: If Gemini API is not configured or request fails
        """
        if not self.client:
            raise Exception("Gemini API key not configured")

        try:
            logger.info(f"Generating streaming response with {model}")

            # Create generation config
            config_params = {
                "temperature": temperature,
                "system_instruction": system_prompt or self._build_system_prompt(),
            }
            if max_tokens:
                config_params["max_output_tokens"] = max_tokens

            config = types.GenerateContentConfig(**config_params)

            # Generate streaming response
            async for chunk in await self.client.aio.models.generate_content_stream(
                model=model,
                contents=prompt,
                config=config,
            ):
                if chunk.text:
                    yield chunk.text

        except Exception as e:
            logger.error(f"Error generating Gemini streaming response: {e}")
            raise


# Singleton instance
_gemini_service: Optional[GeminiService] = None


def get_gemini_service() -> GeminiService:
    """Get or create the Gemini service singleton."""
    global _gemini_service
    if _gemini_service is None:
        _gemini_service = GeminiService()
    return _gemini_service
