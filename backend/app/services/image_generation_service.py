"""
Service for generating images using Google's Gemini Imagen API.
"""
import base64
import logging
import os
from typing import Dict, List, Optional
from uuid import uuid4

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    logger_temp = logging.getLogger(__name__)
    logger_temp.warning("google-genai package not installed. Install with: pip install google-genai")

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.generated_image import GeneratedImage
from app.utils.image_utils import create_thumbnail, get_image_dimensions

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
        reference_images: Optional[List[Dict[str, str]]] = None,
        enable_google_search: bool = False,
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
            reference_images: List of reference images with image_data (base64) and mime_type
            enable_google_search: Enable Google Search grounding for real-time info (sports, news, weather)

        Returns:
            List of dicts with 'image_data' (base64) and 'format' (png/jpeg)

        Raises:
            Exception: If Gemini API is not configured or request fails
        """
        if not self.client:
            raise Exception("Gemini API key not configured")

        try:
            ref_count = len(reference_images) if reference_images else 0
            logger.info(
                f"Generating {number_of_images} image(s) with {model} "
                f"(aspect_ratio={aspect_ratio}, size={image_size}, ref_images={ref_count})"
            )

            # Build the prompt with negative prompt if provided
            full_prompt = prompt
            if negative_prompt:
                full_prompt = f"{prompt}\n\nNegative prompt: {negative_prompt}"

            # Enhance prompt for Google Search grounding with specific instructions
            if enable_google_search:
                # Detect if this is a sports/news/weather prompt and add specific requirements
                prompt_lower = prompt.lower()

                if any(word in prompt_lower for word in ['game', 'match', 'score', 'sport', 'nba', 'nfl', 'mlb', 'nhl', 'soccer', 'football', 'basketball']):
                    full_prompt = f"""{prompt}

IMPORTANT: Use Google Search to find the ACTUAL game results, scores, and details. Include:
- Final score (e.g., Team A 130 - Team B 110)
- Date of the game
- Top scorers with points (e.g., Player Name: 28 pts)
- Both teams' current records (e.g., 20-15, 18-17)
- Stadium/venue if relevant

Make sure ALL information is accurate and based on real search results."""
                    logger.info("Enhanced prompt for sports game with specific data requirements")

                elif any(word in prompt_lower for word in ['weather', 'forecast', 'temperature', 'rain', 'snow']):
                    full_prompt = f"""{prompt}

Use Google Search to find the ACTUAL weather forecast. Include:
- Current or forecasted temperature
- Weather conditions (sunny, rainy, etc.)
- Date/time period
- Location"""
                    logger.info("Enhanced prompt for weather with specific data requirements")

                elif any(word in prompt_lower for word in ['news', 'announcement', 'today', 'yesterday', 'recent', 'latest']):
                    full_prompt = f"""{prompt}

Use Google Search to find the ACTUAL news/event details. Include:
- Key facts and figures
- Dates and times
- Relevant people or organizations
- Accurate quotes or statistics"""
                    logger.info("Enhanced prompt for news with specific data requirements")

            # Build contents array with text prompt and reference images
            contents = [full_prompt]

            # Add reference images if provided
            if reference_images:
                for ref_img in reference_images:
                    contents.append({
                        "inline_data": {
                            "mime_type": ref_img["mime_type"],
                            "data": ref_img["image_data"],
                        }
                    })
                logger.info(f"Added {len(reference_images)} reference image(s) to request")

            # Generate images using the correct API
            # Note: number_of_images is handled by making multiple requests
            # as the API generates one image per request
            images = []

            for i in range(number_of_images):
                logger.info(f"Generating image {i+1}/{number_of_images}")

                # Build config with Google Search grounding if enabled
                config_kwargs = {
                    "response_modalities": ["Text", "Image"] if enable_google_search else ["IMAGE"],
                }

                if enable_google_search:
                    config_kwargs["tools"] = [{"google_search": {}}]
                    logger.info("Google Search grounding enabled for real-time information")

                    # Automatically use Pro model for better grounding accuracy
                    if model == "gemini-2.5-flash-image":
                        model = "gemini-3-pro-image-preview"
                        logger.info("Switched to gemini-3-pro-image-preview for better Google Search grounding")

                response = self.client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=types.GenerateContentConfig(**config_kwargs),
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

    async def save_images_to_database(
        self,
        images: List[Dict[str, str]],
        prompt: str,
        metadata: Dict[str, str],
        db: AsyncSession,
    ) -> List[GeneratedImage]:
        """
        Save generated images to the database with thumbnails.

        Args:
            images: List of generated images with image_data and format
            prompt: Original prompt used for generation
            metadata: Generation metadata (aspect_ratio, model, negative_prompt, etc.)
            db: Database session

        Returns:
            List of saved GeneratedImage model instances

        Raises:
            Exception: If database save fails
        """
        try:
            saved_images = []

            for img_data in images:
                image_base64 = img_data["image_data"]
                image_format = img_data["format"]

                # Generate thumbnail (256x256)
                try:
                    thumbnail = create_thumbnail(image_base64, size=(256, 256), format=image_format.upper())
                except Exception as e:
                    logger.warning(f"Failed to create thumbnail: {e}")
                    thumbnail = None

                # Get image dimensions
                try:
                    dimensions = get_image_dimensions(image_base64)
                    width, height = dimensions if dimensions else (None, None)
                except Exception as e:
                    logger.warning(f"Failed to get image dimensions: {e}")
                    width, height = None, None

                # Create database record
                db_image = GeneratedImage(
                    id=str(uuid4()),
                    prompt=prompt,
                    negative_prompt=metadata.get("negative_prompt"),
                    image_data=image_base64,
                    thumbnail_data=thumbnail,
                    image_format=image_format,
                    metadata_=metadata,
                    width=width,
                    height=height,
                    is_favorite=False,
                    tags=[],
                )

                db.add(db_image)
                saved_images.append(db_image)

            # Commit all images at once
            await db.commit()

            # Refresh to get timestamps
            for img in saved_images:
                await db.refresh(img)

            logger.info(f"Saved {len(saved_images)} image(s) to database")
            return saved_images

        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to save images to database: {e}", exc_info=True)
            raise


# Singleton instance
_image_generation_service: Optional[ImageGenerationService] = None


def get_image_generation_service() -> ImageGenerationService:
    """Get or create the image generation service singleton."""
    global _image_generation_service
    if _image_generation_service is None:
        _image_generation_service = ImageGenerationService()
    return _image_generation_service
