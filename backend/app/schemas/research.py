"""
Pydantic schemas for research operations.
"""
from datetime import datetime
from typing import List, Optional, Dict
from pydantic import BaseModel, Field, field_validator


class ResearchTaskCreate(BaseModel):
    """Schema for creating a research task."""

    query: str = Field(..., min_length=3, max_length=500, description="Research query")
    max_sources: int = Field(10, ge=1, le=50, description="Maximum sources to process")
    depth: str = Field(
        "thorough", description="Research depth: quick, thorough, or deep"
    )
    source_types: Optional[List[str]] = Field(
        None, description="Filter by source types (academic, news, blog, etc.)"
    )

    @field_validator("depth")
    @classmethod
    def validate_depth(cls, v):
        """Validate depth field."""
        allowed = ["quick", "thorough", "deep"]
        if v not in allowed:
            raise ValueError(f"Depth must be one of: {', '.join(allowed)}")
        return v

    @field_validator("source_types")
    @classmethod
    def validate_source_types(cls, v):
        """Validate source_types field."""
        if v is None:
            return v

        allowed = ["academic", "news", "blog", "reddit", "github", "general"]
        for source_type in v:
            if source_type not in allowed:
                raise ValueError(
                    f"Invalid source type '{source_type}'. Allowed: {', '.join(allowed)}"
                )
        return v


class ResearchTaskResponse(BaseModel):
    """Schema for research task response."""

    id: str
    query: str
    status: str
    max_sources: int
    depth: str
    source_types: Optional[List[str]]
    sources_found: int
    sources_scraped: int
    sources_added: int
    sources_failed: int
    sources_skipped: int
    current_step: Optional[str]
    progress_percentage: int
    estimated_time_remaining: Optional[int]
    summary: Optional[str]
    contradictions_found: int
    suggested_followups: Optional[List[str]]
    job_id: Optional[str]
    error_message: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ResearchTaskListItem(BaseModel):
    """Schema for research task list item (summary view)."""

    id: str
    query: str
    status: str
    sources_added: int
    sources_failed: int
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class ResearchTaskList(BaseModel):
    """Schema for paginated research task list."""

    tasks: List[ResearchTaskListItem]
    total: int
    limit: int
    offset: int


class ResearchSourceResponse(BaseModel):
    """Schema for research source response."""

    id: str
    url: str
    title: Optional[str]
    domain: Optional[str]
    source_type: Optional[str]
    credibility_score: Optional[float]
    credibility_reasons: Optional[List[str]]
    status: str
    failure_reason: Optional[str]
    document_id: Optional[str]
    content: Optional[str] = None  # Full scraped content
    created_at: datetime

    class Config:
        from_attributes = True


class ResearchResultsResponse(BaseModel):
    """Schema for research results response."""

    task_id: str
    query: str
    status: str
    summary: Optional[str]
    key_findings: Optional[Dict]
    sources: List[ResearchSourceResponse]
    contradictions_found: int
    suggested_followups: Optional[List[str]]
    sources_added: int
    sources_failed: int
    sources_skipped: int
    completed_at: Optional[datetime]


class ResearchTaskStart(BaseModel):
    """Response when starting a research task."""

    task_id: str
    status: str
    message: str
