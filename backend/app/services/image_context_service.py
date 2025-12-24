"""
Service for detecting iterative image generation prompts and building context.
Uses local LLM to understand user intent and enhance prompts with conversation history.
"""
import logging
from typing import Optional, Dict, Any
import httpx

logger = logging.getLogger(__name__)


class ImageContextService:
    """Service for managing conversation context in image generation."""

    def __init__(self, ollama_base_url: str = "http://localhost:11434"):
        self.ollama_base_url = ollama_base_url
        self.model = "llama3.2:3b"  # Fast model for quick analysis

    async def is_iterative_prompt(
        self, current_prompt: str, previous_prompt: Optional[str] = None
    ) -> bool:
        """
        Detect if the current prompt is iterating on a previous image.

        Examples of iterative prompts:
        - "add a car in the background"
        - "make it more colorful"
        - "remove the person"
        - "change the lighting to sunset"

        Args:
            current_prompt: The new prompt from the user
            previous_prompt: The previous prompt (if any)

        Returns:
            True if prompt is iterative, False if it's a new image request
        """
        if not previous_prompt:
            return False

        # Quick heuristic checks first (no LLM needed)
        iterative_keywords = [
            "add", "remove", "change", "make it", "make the",
            "modify", "adjust", "update", "fix", "improve",
            "more", "less", "without", "with", "instead of"
        ]

        current_lower = current_prompt.lower()

        # If prompt starts with an action verb, likely iterative
        for keyword in iterative_keywords:
            if current_lower.startswith(keyword) or f" {keyword} " in current_lower:
                logger.info(f"Detected iterative prompt via keyword: {keyword}")
                return True

        # If prompt is very short (< 10 words), likely iterative
        if len(current_prompt.split()) < 10:
            logger.info("Detected iterative prompt via length heuristic")
            return True

        # For ambiguous cases, use LLM (optional, can skip for speed)
        # return await self._llm_detect_iterative(current_prompt, previous_prompt)

        return False

    async def _llm_detect_iterative(
        self, current_prompt: str, previous_prompt: str
    ) -> bool:
        """
        Use LLM to detect if prompt is iterative (fallback for ambiguous cases).

        Args:
            current_prompt: Current user prompt
            previous_prompt: Previous prompt

        Returns:
            True if iterative, False otherwise
        """
        try:
            system_prompt = """You are a helpful assistant that determines if a new image prompt is trying to iterate/modify a previous image, or if it's requesting a completely new image.

Iterative prompts reference the previous image with words like "add", "remove", "change", "make it", etc.
New prompts describe a completely different scene/subject.

Respond with only "ITERATIVE" or "NEW"."""

            user_prompt = f"""Previous prompt: "{previous_prompt}"

New prompt: "{current_prompt}"

Is the new prompt iterating on the previous image, or requesting a completely new image?"""

            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    f"{self.ollama_base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": f"{system_prompt}\n\n{user_prompt}",
                        "stream": False,
                        "options": {"temperature": 0.1},
                    },
                )
                response.raise_for_status()
                result = response.json()
                answer = result.get("response", "").strip().upper()

                return "ITERATIVE" in answer

        except Exception as e:
            logger.error(f"LLM detection failed: {e}")
            # Default to false on error
            return False

    async def enhance_prompt_with_context(
        self,
        current_prompt: str,
        previous_prompt: str,
        previous_metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Enhance an iterative prompt by adding context from previous generation.

        Args:
            current_prompt: User's new prompt (e.g., "add a car in the background")
            previous_prompt: Previous full prompt
            previous_metadata: Optional metadata from previous generation

        Returns:
            Enhanced prompt that includes context

        Example:
            current: "add a car in the background"
            previous: "A vintage 1940s Ford Deluxe with rounded curves"
            result: "A vintage 1940s Ford Deluxe with rounded curves, with a car in the background"
        """
        # Build enhanced prompt
        enhanced = f"{previous_prompt}, {current_prompt}"

        logger.info(f"Enhanced prompt: {enhanced}")
        return enhanced

    async def should_use_reference_image(
        self, current_prompt: str, previous_prompt: Optional[str] = None
    ) -> bool:
        """
        Determine if we should use the previous image as a reference image.

        Args:
            current_prompt: Current user prompt
            previous_prompt: Previous prompt (if any)

        Returns:
            True if we should use previous image as reference
        """
        # If prompt is iterative, use reference image for consistency
        return await self.is_iterative_prompt(current_prompt, previous_prompt)


# Singleton instance
_context_service: Optional[ImageContextService] = None


def get_image_context_service() -> ImageContextService:
    """Get the singleton ImageContextService instance."""
    global _context_service
    if _context_service is None:
        _context_service = ImageContextService()
    return _context_service
