"""
Pydantic schemas for generated image gallery.
"""
from typing import List, Optional
from datetime import datetime

from pydantic import BaseModel, Field


class GeneratedImageResponse(BaseModel):
    """Response schema for a single generated image."""

    id: str = Field(..., description="Image UUID")
    prompt: str = Field(..., description="Text prompt used to generate this image")
    negative_prompt: Optional[str] = Field(None, description="Negative prompt (what to avoid)")

    # Image data (can include full image or just thumbnail depending on endpoint)
    image_data: Optional[str] = Field(None, description="Base64 full image data")
    thumbnail_data: Optional[str] = Field(None, description="Base64 thumbnail data")
    image_format: str = Field(..., description="Image format (png/jpeg)")

    # Metadata
    metadata_: Optional[dict] = Field(None, description="Generation metadata")
    width: Optional[int] = Field(None, description="Image width in pixels")
    height: Optional[int] = Field(None, description="Image height in pixels")

    # User preferences
    is_favorite: bool = Field(False, description="Is this image favorited")
    tags: Optional[List[str]] = Field(None, description="User tags")

    # Timestamps
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class GalleryListResponse(BaseModel):
    """Response schema for gallery list with pagination."""

    images: List[GeneratedImageResponse] = Field(..., description="List of generated images")
    total: int = Field(..., description="Total number of images matching filters")
    limit: int = Field(..., description="Number of images per page")
    offset: int = Field(..., description="Current offset")
    has_more: bool = Field(..., description="Whether there are more images to load")


class UpdateImageRequest(BaseModel):
    """Request schema for updating image metadata."""

    is_favorite: Optional[bool] = Field(None, description="Update favorite status")
    tags: Optional[List[str]] = Field(None, description="Update tags")


class DeleteImageResponse(BaseModel):
    """Response schema for image deletion."""

    success: bool = Field(..., description="Whether deletion succeeded")
    message: str = Field(..., description="Success/error message")
