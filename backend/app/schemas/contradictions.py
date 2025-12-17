"""
Pydantic schemas for contradiction detection.
"""

from pydantic import BaseModel, Field
from typing import List


class ContradictionSource(BaseModel):
    """Source information for a contradiction."""
    type: str = Field(..., description="Type of source ('note' or 'document')")
    id: str = Field(..., description="UUID of the source")
    title: str = Field(..., description="Title of the source")
    excerpt: str = Field(..., description="Relevant excerpt from the source")


class ContradictionItem(BaseModel):
    """A detected contradiction between two sources."""
    source1: ContradictionSource = Field(..., description="First source in contradiction")
    source2: ContradictionSource = Field(..., description="Second source in contradiction")
    contradiction_type: str = Field(..., description="Type of contradiction (factual/methodological/conceptual/temporal)")
    explanation: str = Field(..., description="Explanation of the contradiction")
    severity: str = Field(..., description="Severity level (high/medium/low)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0.0-1.0)")


class ContradictionResponse(BaseModel):
    """Response containing detected contradictions for a source."""
    source_type: str = Field(..., description="Type of the analyzed source")
    source_id: str = Field(..., description="UUID of the analyzed source")
    source_title: str = Field(..., description="Title of the analyzed source")
    contradictions: List[ContradictionItem] = Field(default_factory=list, description="List of detected contradictions")
