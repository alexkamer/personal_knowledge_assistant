"""
Context Intelligence schemas for related content discovery and synthesis.
"""
from typing import List, Optional

from pydantic import BaseModel, Field


class RelatedContentItem(BaseModel):
    """A single piece of related content."""

    source_type: str = Field(
        ..., description="Type of source: 'note', 'document', or 'youtube'"
    )
    source_id: str = Field(..., description="ID of the source")
    source_title: str = Field(..., description="Title of the source")
    similarity_score: float = Field(
        ..., description="Similarity score (0-1)", ge=0.0, le=1.0
    )
    preview: Optional[str] = Field(
        None, description="Preview snippet of matching content"
    )
    timestamp: Optional[float] = Field(
        None, description="Timestamp for YouTube videos (in seconds)"
    )
    chunk_count: int = Field(
        default=1, description="Number of matching chunks from this source"
    )


class ContextSynthesis(BaseModel):
    """AI-generated synthesis of content connections."""

    synthesis_type: str = Field(
        ..., description="Type of synthesis: 'connections', 'comparison', or 'gaps'"
    )
    content: str = Field(..., description="Generated synthesis text")


class SuggestedQuestion(BaseModel):
    """A suggested question for further exploration."""

    question: str = Field(..., description="The suggested question")
    rationale: Optional[str] = Field(
        None, description="Why this question is relevant"
    )


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
    contradiction_type: str = Field(..., description="Type of contradiction")
    explanation: str = Field(..., description="Explanation of the contradiction")
    severity: str = Field(..., description="Severity level (high/medium/low)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0.0-1.0)")


class ContextResponse(BaseModel):
    """Response containing contextual intelligence for a piece of content."""

    source_type: str = Field(..., description="Type of source being analyzed")
    source_id: str = Field(..., description="ID of the source")
    source_title: str = Field(..., description="Title of the source")
    related_content: List[RelatedContentItem] = Field(
        default_factory=list, description="Related content items"
    )
    synthesis: Optional[str] = Field(None, description="AI-generated synthesis")
    suggested_questions: List[str] = Field(
        default_factory=list, description="Suggested questions for exploration"
    )
    contradictions: List[ContradictionItem] = Field(
        default_factory=list, description="Detected logical contradictions"
    )


class ContextRequest(BaseModel):
    """Request parameters for context intelligence."""

    include_synthesis: bool = Field(
        default=True, description="Whether to include AI synthesis"
    )
    include_questions: bool = Field(
        default=True, description="Whether to include suggested questions"
    )
    top_k: int = Field(
        default=5, description="Number of related items to return", ge=1, le=20
    )
