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

    async def generate_response(
        self,
        prompt: str,
        model: str = "gemini-1.5-flash",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Generate a non-streaming response using Gemini.

        Args:
            prompt: The prompt to send to Gemini
            model: The Gemini model to use (gemini-1.5-flash or gemini-1.5-pro)
            temperature: Temperature for response generation (0.0-1.0)
            max_tokens: Maximum tokens to generate (optional)

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

            # Create model
            gemini_model = genai.GenerativeModel(
                model_name=model,
                generation_config=generation_config,
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
    ) -> AsyncIterator[str]:
        """
        Generate a streaming response using Gemini.

        Args:
            prompt: The prompt to send to Gemini
            model: The Gemini model to use (gemini-1.5-flash or gemini-1.5-pro)
            temperature: Temperature for response generation (0.0-1.0)
            max_tokens: Maximum tokens to generate (optional)

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

            # Create model
            gemini_model = genai.GenerativeModel(
                model_name=model,
                generation_config=generation_config,
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
