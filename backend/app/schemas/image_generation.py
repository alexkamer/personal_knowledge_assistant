"""
Pydantic schemas for image generation.
"""
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


class ReferenceImage(BaseModel):
    """Reference image for guided generation."""

    image_data: str = Field(..., description="Base64 encoded image data")
    mime_type: str = Field(..., description="Image MIME type (e.g., image/jpeg, image/png)")
    image_type: Literal["human", "object", "style"] = Field(
        "object", description="Type of reference image"
    )


class ConversationContext(BaseModel):
    """Previous generation context for iterative prompts."""

    previous_prompt: str = Field(..., description="Previous prompt used")
    previous_image_data: Optional[str] = Field(None, description="Base64 of previous image to use as reference")
    previous_metadata: Optional[dict] = Field(None, description="Metadata from previous generation")


class ImageGenerationRequest(BaseModel):
    """Request schema for image generation."""

    prompt: str = Field(..., min_length=1, max_length=10000, description="Text description of the image to generate")
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
    reference_images: Optional[List[ReferenceImage]] = Field(
        None, description="Reference images for guided generation (max 14 total: 5 human, 6 object, 3 style)"
    )
    conversation_context: Optional[ConversationContext] = Field(
        None, description="Context from previous generation for iterative prompts"
    )
    enable_google_search: bool = Field(
        False, description="Enable Google Search grounding for real-time information (news, weather, sports, etc.)"
    )

    @field_validator("reference_images")
    @classmethod
    def validate_reference_images(cls, v: Optional[List[ReferenceImage]]) -> Optional[List[ReferenceImage]]:
        """Validate reference image limits."""
        if v is None:
            return v

        if len(v) > 14:
            raise ValueError("Maximum 14 reference images allowed")

        # Count by type
        human_count = sum(1 for img in v if img.image_type == "human")
        object_count = sum(1 for img in v if img.image_type == "object")
        style_count = sum(1 for img in v if img.image_type == "style")

        if human_count > 5:
            raise ValueError("Maximum 5 human reference images allowed")
        if object_count > 6:
            raise ValueError("Maximum 6 object reference images allowed")
        if style_count > 3:
            raise ValueError("Maximum 3 style reference images allowed")

        return v


class GeneratedImage(BaseModel):
    """Single generated image."""

    image_data: str = Field(..., description="Base64 encoded image data")
    format: str = Field(..., description="Image format (png or jpeg)")


class ImageGenerationResponse(BaseModel):
    """Response schema for image generation."""

    images: list[GeneratedImage] = Field(..., description="List of generated images")
    prompt: str = Field(..., description="Original prompt used for generation")
    metadata: dict = Field(..., description="Generation metadata (aspect_ratio, size, model, etc.)")
