"""
Service for interacting with Google's Gemini API.
"""
import logging
from typing import AsyncIterator, Optional

import google.generativeai as genai

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

        genai.configure(api_key=settings.gemini_api_key)
        self.client = genai
        logger.info("Gemini service initialized")

    def _build_system_prompt(self) -> str:
        """
        Build system prompt that allows blending context with general knowledge.

        This prompt enables the AI to:
        - Use document context when relevant
        - Supplement with general knowledge for complete answers
        - Provide natural citations only when using specific facts
        - Ignore irrelevant context gracefully
        """
        return """You are a helpful AI assistant for a personal knowledge management system.

Your role is to provide complete, accurate answers by combining the user's documents with your general knowledge.

Key principles:
- Use the provided context when it contains relevant information
- Supplement with your general knowledge to give complete, helpful answers
- Don't say "the context doesn't contain" - if documents are incomplete, use what you know
- Only cite sources when you're directly using specific information from them
- If context is irrelevant to the question, it's okay to ignore it completely
- Be conversational and natural - avoid robotic phrases
- Check conversation history for context (pronouns, "that", "it", follow-ups)

Citation style:
- Natural mentions: "Your document on X mentions..." or "According to your notes..."
- Only when actually using specific facts from sources
- Don't force citations if answering from general knowledge

Remember: Users want helpful complete answers, not explanations of what's missing from their documents."""

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
            generation_config = {
                "temperature": temperature,
            }
            if max_tokens:
                generation_config["max_output_tokens"] = max_tokens

            # Create model with system instruction
            gemini_model = genai.GenerativeModel(
                model_name=model,
                generation_config=generation_config,
                system_instruction=system_prompt or self._build_system_prompt(),
            )

            # Generate response
            response = gemini_model.generate_content(prompt)

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
            generation_config = {
                "temperature": temperature,
            }
            if max_tokens:
                generation_config["max_output_tokens"] = max_tokens

            # Create model with system instruction
            gemini_model = genai.GenerativeModel(
                model_name=model,
                generation_config=generation_config,
                system_instruction=system_prompt or self._build_system_prompt(),
            )

            # Generate streaming response
            response = gemini_model.generate_content(prompt, stream=True)

            for chunk in response:
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
