"""
Pydantic schemas for image generation.
"""
from typing import Literal, Optional

from pydantic import BaseModel, Field


class ImageGenerationRequest(BaseModel):
    """Request schema for image generation."""

    prompt: str = Field(..., min_length=1, max_length=2000, description="Text description of the image to generate")
    negative_prompt: Optional[str] = Field(
        None, max_length=1000, description="What NOT to include in the image"
    )
    aspect_ratio: Literal["1:1", "16:9", "9:16", "4:3", "3:4"] = Field(
        "1:1", description="Image aspect ratio"
    )
    image_size: Literal["1K", "2K", "4K"] = Field("2K", description="Image resolution")
    number_of_images: int = Field(1, ge=1, le=4, description="Number of images to generate (1-4)")
    model: Literal["gemini-2.5-flash-image", "gemini-3-pro-image-preview"] = Field(
        "gemini-2.5-flash-image", description="Imagen model to use"
    )


class GeneratedImage(BaseModel):
    """Single generated image."""

    image_data: str = Field(..., description="Base64 encoded image data")
    format: str = Field(..., description="Image format (png or jpeg)")


class ImageGenerationResponse(BaseModel):
    """Response schema for image generation."""

    images: list[GeneratedImage] = Field(..., description="List of generated images")
    prompt: str = Field(..., description="Original prompt used for generation")
    metadata: dict = Field(..., description="Generation metadata (aspect_ratio, size, model, etc.)")
