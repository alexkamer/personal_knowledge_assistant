"""
Pydantic schemas for research briefings.
"""
from datetime import datetime
from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class ResearchBriefingCreate(BaseModel):
    """Schema for creating a research briefing."""

    project_id: str = Field(..., description="Project ID")
    task_ids: Optional[List[str]] = Field(
        None, description="Specific task IDs to include (if None, includes all completed tasks)"
    )


class ResearchBriefingResponse(BaseModel):
    """Schema for research briefing response."""

    id: str
    project_id: str
    title: str
    summary: str
    key_findings: Optional[Dict]
    contradictions: Optional[List[Dict]]
    knowledge_gaps: Optional[List[str]]
    suggested_tasks: Optional[List[str]]
    task_ids: Optional[List[str]]
    sources_count: int
    generated_at: datetime
    viewed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ResearchBriefingListItem(BaseModel):
    """Schema for research briefing list item (summary view)."""

    id: str
    project_id: str
    title: str
    sources_count: int
    generated_at: datetime
    viewed_at: Optional[datetime]

    class Config:
        from_attributes = True


class ResearchBriefingList(BaseModel):
    """Schema for paginated research briefing list."""

    briefings: List[ResearchBriefingListItem]
    total: int
    limit: int
    offset: int


class BriefingMarkdown(BaseModel):
    """Schema for briefing in markdown format."""

    markdown: str
    title: str
