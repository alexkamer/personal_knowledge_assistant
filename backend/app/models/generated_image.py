"""
Generated image model for AI-generated images.
"""
from typing import Optional

from sqlalchemy import Boolean, String, Text, Integer, ARRAY
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class GeneratedImage(Base, UUIDMixin, TimestampMixin):
    """
    AI-generated image from Gemini Imagen API.

    Stores generated images with their prompts, metadata, and user preferences.
    Supports favorites, tags, and image management features.
    """

    __tablename__ = "generated_images"

    # Generation parameters
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    negative_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Image data (hybrid storage strategy)
    # For now: base64 in DB, can migrate to S3/disk later
    image_data: Mapped[str] = mapped_column(Text, nullable=False)
    thumbnail_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    image_format: Mapped[str] = mapped_column(String(10), nullable=False, default="png")

    # Generation metadata (aspect_ratio, model, image_size, etc.)
    metadata_: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # User organization
    is_favorite: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    tags: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String), nullable=True)

    # Optional project/collection grouping (for future use)
    project_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)

    # Image dimensions (extracted from metadata for quick filtering)
    width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    def __repr__(self) -> str:
        return f"<GeneratedImage(id={self.id}, prompt='{self.prompt[:50]}...')>"
