"""
Pydantic schemas for Document model.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class DocumentBase(BaseModel):
    """Base schema with common document fields."""

    filename: str = Field(..., description="Original filename")
    file_type: str = Field(..., description="File extension/type")


class DocumentCreate(DocumentBase):
    """Schema for creating a new document (used internally after upload)."""

    file_path: str = Field(..., description="Path where file is stored")
    file_size: int = Field(..., ge=0, description="File size in bytes")
    content: str = Field(..., description="Extracted text content")
    metadata_: Optional[str] = Field(None, description="Additional metadata as JSON")


class DocumentResponse(DocumentBase):
    """Schema for document response."""

    id: str
    file_path: str
    file_size: int
    created_at: datetime
    updated_at: datetime

    # Optional fields
    metadata_: Optional[str] = None

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """Schema for list of documents response."""

    documents: list[DocumentResponse]
    total: int


class DocumentContentResponse(BaseModel):
    """Schema for document with full extracted content."""

    id: str
    filename: str
    file_type: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True
