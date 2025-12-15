"""
Pydantic schemas for Note model.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class NoteBase(BaseModel):
    """Base schema with common note fields."""

    title: str = Field(..., min_length=1, max_length=255, description="Note title")
    content: str = Field(..., min_length=1, description="Note content")
    tags: Optional[str] = Field(None, max_length=500, description="Comma-separated tags")


class NoteCreate(NoteBase):
    """Schema for creating a new note."""

    pass


class NoteUpdate(BaseModel):
    """Schema for updating an existing note. All fields are optional."""

    title: Optional[str] = Field(None, min_length=1, max_length=255)
    content: Optional[str] = Field(None, min_length=1)
    tags: Optional[str] = Field(None, max_length=500)


class NoteResponse(NoteBase):
    """Schema for note response."""

    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NoteListResponse(BaseModel):
    """Schema for list of notes response."""

    notes: list[NoteResponse]
    total: int
