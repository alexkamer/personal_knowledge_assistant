"""
Service for generating images using Google's Gemini Imagen API.
"""
import base64
import logging
import os
from typing import Dict, List, Optional

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    logger_temp = logging.getLogger(__name__)
    logger_temp.warning("google-genai package not installed. Install with: pip install google-genai")

from app.core.config import settings

logger = logging.getLogger(__name__)


class ImageGenerationService:
    """Service for generating images using Gemini Imagen API."""

    def __init__(self):
        """Initialize image generation service."""
        if not GENAI_AVAILABLE:
            logger.error("google-genai package not installed")
            self.client = None
            return

        if not settings.gemini_api_key:
            logger.warning("Gemini API key not configured - image generation unavailable")
            self.client = None
            return

        # Set GOOGLE_API_KEY environment variable for genai client
        # This ensures it uses generativelanguage.googleapis.com (not Vertex AI)
        os.environ['GOOGLE_API_KEY'] = settings.gemini_api_key

        # Initialize client (will automatically use GOOGLE_API_KEY)
        self.client = genai.Client()
        logger.info("Image generation service initialized")

    async def generate_images(
        self,
        prompt: str,
        aspect_ratio: str = "1:1",
        image_size: str = "2K",
        number_of_images: int = 1,
        negative_prompt: Optional[str] = None,
        model: str = "gemini-2.5-flash-image",
    ) -> List[Dict[str, str]]:
        """
        Generate images using Gemini Imagen API.

        Args:
            prompt: Text description of the image to generate
            aspect_ratio: Image aspect ratio ("1:1", "16:9", "9:16", "4:3", "3:4")
            image_size: Image resolution ("1K", "2K", "4K")
            number_of_images: Number of images to generate (1-4)
            negative_prompt: What NOT to include in the image (optional)
            model: Imagen model to use

        Returns:
            List of dicts with 'image_data' (base64) and 'format' (png/jpeg)

        Raises:
            Exception: If Gemini API is not configured or request fails
        """
        if not self.client:
            raise Exception("Gemini API key not configured")

        try:
            logger.info(
                f"Generating {number_of_images} image(s) with {model} "
                f"(aspect_ratio={aspect_ratio}, size={image_size})"
            )

            # Build the prompt with negative prompt if provided
            full_prompt = prompt
            if negative_prompt:
                full_prompt = f"{prompt}\n\nNegative prompt: {negative_prompt}"

            # Generate images using the correct API
            # Note: number_of_images is handled by making multiple requests
            # as the API generates one image per request
            images = []

            for i in range(number_of_images):
                logger.info(f"Generating image {i+1}/{number_of_images}")

                response = self.client.models.generate_content(
                    model=model,
                    contents=full_prompt,
                    config=types.GenerateContentConfig(
                        response_modalities=["IMAGE"],
                    ),
                )

                # Extract base64 images from response
                for part in response.parts:
                    if part.inline_data is not None:
                        # Get the image data (raw bytes) and encode to base64 string
                        raw_data = part.inline_data.data
                        if isinstance(raw_data, bytes):
                            # Encode bytes to base64 string
                            image_data = base64.b64encode(raw_data).decode('utf-8')
                        else:
                            # Already a string
                            image_data = raw_data

                        # Get format from MIME type
                        mime_type = part.inline_data.mime_type
                        format_type = mime_type.split("/")[1] if "/" in mime_type else "png"

                        images.append({"image_data": image_data, "format": format_type})

            if not images:
                raise Exception("No images generated in response")

            logger.info(f"Successfully generated {len(images)} image(s)")
            return images

        except Exception as e:
            logger.error(f"Error generating images: {e}", exc_info=True)
            raise


# Singleton instance
_image_generation_service: Optional[ImageGenerationService] = None


def get_image_generation_service() -> ImageGenerationService:
    """Get or create the image generation service singleton."""
    global _image_generation_service
    if _image_generation_service is None:
        _image_generation_service = ImageGenerationService()
    return _image_generation_service
