"""
Schemas for autocomplete endpoint.
"""
from pydantic import BaseModel, Field
from typing import Optional


class AutocompleteRequest(BaseModel):
    """Request schema for autocomplete."""

    prefix: str = Field(..., description="Text prefix to complete", min_length=1)
    context: Optional[str] = Field(None, description="Additional context for completion")


class AutocompleteResponse(BaseModel):
    """Response schema for autocomplete."""

    completion: str = Field(..., description="Suggested text completion")
