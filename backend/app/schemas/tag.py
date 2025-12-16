"""
Pydantic schemas for tag operations.
"""
from datetime import datetime

from pydantic import BaseModel, Field


class TagBase(BaseModel):
    """Base schema for tags."""

    name: str = Field(..., min_length=1, max_length=50, description="Tag name")


class TagCreate(TagBase):
    """Schema for creating a tag."""

    pass


class TagResponse(TagBase):
    """Schema for tag responses."""

    id: str
    created_at: datetime

    class Config:
        from_attributes = True


class TagWithUsage(TagResponse):
    """Schema for tag with usage count."""

    note_count: int = Field(..., description="Number of notes with this tag")
