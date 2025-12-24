"""
Service for grounding image generation prompts with real-time data from Google Search.
Two-step process: Search first, then generate image with verified data.
"""
import logging
import os
from typing import Optional

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

from app.core.config import settings

logger = logging.getLogger(__name__)


class GroundingService:
    """Service for fetching real-time data to ground image generation."""

    def __init__(self):
        """Initialize grounding service."""
        if not GENAI_AVAILABLE:
            logger.error("google-genai package not installed")
            self.client = None
            return

        if not settings.gemini_api_key:
            logger.warning("Gemini API key not configured - grounding unavailable")
            self.client = None
            return

        os.environ['GOOGLE_API_KEY'] = settings.gemini_api_key
        self.client = genai.Client()
        logger.info("Grounding service initialized")

    async def search_and_extract_data(self, query: str) -> Optional[str]:
        """
        Use Google Search grounding to get real-time data, then return structured text.

        Args:
            query: The search query (e.g., "last night's Spurs vs Thunder game scores")

        Returns:
            Structured text with verified data, or None if search fails
        """
        if not self.client:
            logger.warning("Grounding service not available")
            return None

        try:
            logger.info(f"Searching for real-time data: {query}")

            # Use text-only model with Google Search grounding
            response = self.client.models.generate_content(
                model="gemini-2.0-flash-exp",  # Fast text model with search
                contents=query,
                config=types.GenerateContentConfig(
                    response_modalities=["Text"],
                    tools=[{"google_search": {}}],
                ),
            )

            # Extract text response
            result_text = ""
            for part in response.parts:
                if part.text:
                    result_text += part.text

            if result_text:
                logger.info(f"Found grounded data: {result_text[:200]}...")
                return result_text
            else:
                logger.warning("No text found in grounding response")
                return None

        except Exception as e:
            logger.error(f"Error during grounding search: {e}", exc_info=True)
            return None

    async def enhance_sports_prompt(self, original_prompt: str) -> str:
        """
        For sports prompts, search for real game data and build enhanced prompt.

        Args:
            original_prompt: User's original prompt

        Returns:
            Enhanced prompt with real game data
        """
        # Build search query
        search_query = f"""Search for information about: {original_prompt}

I need the following SPECIFIC details:
- Exact final score (e.g., Team A 130, Team B 110)
- Date the game was played
- Top 2-3 scorers with their point totals
- Current win-loss records for both teams
- Stadium/arena name

Return ONLY factual information from actual game results. Be specific with numbers."""

        # Get grounded data
        grounded_data = await self.search_and_extract_data(search_query)

        if not grounded_data:
            logger.warning("Could not find grounded sports data, using original prompt")
            return original_prompt

        # Build enhanced prompt with real data
        enhanced = f"""{original_prompt}

Use the following REAL game information (verified via Google Search):

{grounded_data}

Create a stylish sports graphic that accurately displays this information. Use the exact scores, player names, and records provided above."""

        logger.info("Enhanced sports prompt with grounded data")
        return enhanced

    async def enhance_weather_prompt(self, original_prompt: str) -> str:
        """
        For weather prompts, search for real forecast data.

        Args:
            original_prompt: User's original prompt

        Returns:
            Enhanced prompt with real weather data
        """
        search_query = f"""Search for weather information about: {original_prompt}

I need:
- Current or forecasted temperature (exact number)
- Weather conditions (sunny, cloudy, rainy, etc.)
- Date/time period
- Location

Return ONLY current/forecasted information."""

        grounded_data = await self.search_and_extract_data(search_query)

        if not grounded_data:
            return original_prompt

        enhanced = f"""{original_prompt}

Use the following REAL weather data (verified via Google Search):

{grounded_data}

Create a weather graphic that accurately displays this information."""

        logger.info("Enhanced weather prompt with grounded data")
        return enhanced

    async def enhance_news_prompt(self, original_prompt: str) -> str:
        """
        For news prompts, search for real current event data.

        Args:
            original_prompt: User's original prompt

        Returns:
            Enhanced prompt with real news data
        """
        search_query = f"""Search for news/information about: {original_prompt}

I need:
- Key facts and figures
- Exact dates and times
- Names of people/organizations involved
- Relevant statistics or quotes

Return ONLY factual, current information."""

        grounded_data = await self.search_and_extract_data(search_query)

        if not grounded_data:
            return original_prompt

        enhanced = f"""{original_prompt}

Use the following REAL information (verified via Google Search):

{grounded_data}

Create a news graphic that accurately displays this information."""

        logger.info("Enhanced news prompt with grounded data")
        return enhanced


# Singleton instance
_grounding_service: Optional[GroundingService] = None


def get_grounding_service() -> GroundingService:
    """Get or create the grounding service singleton."""
    global _grounding_service
    if _grounding_service is None:
        _grounding_service = GroundingService()
    return _grounding_service
