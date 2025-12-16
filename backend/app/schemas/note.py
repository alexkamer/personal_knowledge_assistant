"""
Pydantic schemas for Note model.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.tag import TagResponse


class NoteBase(BaseModel):
    """Base schema with common note fields."""

    title: str = Field(..., min_length=1, max_length=255, description="Note title")
    content: str = Field(..., min_length=1, description="Note content")
    tags: Optional[str] = Field(None, max_length=500, description="Comma-separated tags (deprecated, use tag_names)")


class NoteCreate(BaseModel):
    """Schema for creating a new note."""

    title: str = Field(..., min_length=1, max_length=255, description="Note title")
    content: str = Field(..., min_length=1, description="Note content")
    tag_names: list[str] = Field(default_factory=list, description="List of tag names")


class NoteUpdate(BaseModel):
    """Schema for updating an existing note. All fields are optional."""

    title: Optional[str] = Field(None, min_length=1, max_length=255)
    content: Optional[str] = Field(None, min_length=1)
    tag_names: Optional[list[str]] = Field(None, description="List of tag names (replaces all existing tags)")


class NoteResponse(BaseModel):
    """Schema for note response."""

    id: str
    title: str
    content: str
    tags_rel: list[TagResponse] = Field(default_factory=list, description="Associated tags")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NoteListResponse(BaseModel):
    """Schema for list of notes response."""

    notes: list[NoteResponse]
    total: int


class BacklinkResponse(BaseModel):
    """Schema for a backlink (note that links to another note)."""

    id: str
    title: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BacklinksListResponse(BaseModel):
    """Schema for list of backlinks response."""

    backlinks: list[BacklinkResponse]
    total: int


class RelatedNoteResponse(BaseModel):
    """Schema for a related note with similarity score."""

    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    similarity_score: float = Field(..., ge=0.0, le=1.0, description="Semantic similarity score (0-1)")

    class Config:
        from_attributes = True


class RelatedNotesListResponse(BaseModel):
    """Schema for list of related notes response."""

    related_notes: list[RelatedNoteResponse]
    total: int
