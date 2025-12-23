"""
Pydantic schemas for research projects.
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class ResearchProjectCreate(BaseModel):
    """Schema for creating a research project."""

    name: str = Field(..., min_length=3, max_length=255, description="Project name")
    description: Optional[str] = Field(None, description="Project description")
    goal: str = Field(
        ..., min_length=10, max_length=2000, description="Main research objective"
    )

    # Scheduling
    schedule_type: str = Field("manual", description="Schedule type: manual, daily, weekly, monthly, custom")
    schedule_cron: Optional[str] = Field(None, description="Custom cron expression (required if schedule_type='custom')")

    # Task generation settings
    auto_generate_tasks: bool = Field(True, description="Auto-generate tasks from goal")
    max_tasks_per_run: int = Field(5, ge=1, le=20, description="Max tasks per scheduled run")

    # Research settings
    default_max_sources: int = Field(10, ge=1, le=50, description="Default max sources per task")
    default_depth: str = Field("thorough", description="Default research depth")
    default_source_types: Optional[List[str]] = Field(None, description="Default source type filters")

    @field_validator("schedule_type")
    @classmethod
    def validate_schedule_type(cls, v):
        """Validate schedule_type field."""
        allowed = ["manual", "daily", "weekly", "monthly", "custom"]
        if v not in allowed:
            raise ValueError(f"Schedule type must be one of: {', '.join(allowed)}")
        return v

    @field_validator("default_depth")
    @classmethod
    def validate_depth(cls, v):
        """Validate default_depth field."""
        allowed = ["quick", "thorough", "deep"]
        if v not in allowed:
            raise ValueError(f"Depth must be one of: {', '.join(allowed)}")
        return v


class ResearchProjectUpdate(BaseModel):
    """Schema for updating a research project."""

    name: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = None
    goal: Optional[str] = Field(None, min_length=10, max_length=2000)
    status: Optional[str] = None

    schedule_type: Optional[str] = None
    schedule_cron: Optional[str] = None

    auto_generate_tasks: Optional[bool] = None
    max_tasks_per_run: Optional[int] = Field(None, ge=1, le=20)

    default_max_sources: Optional[int] = Field(None, ge=1, le=50)
    default_depth: Optional[str] = None
    default_source_types: Optional[List[str]] = None


class ResearchProjectResponse(BaseModel):
    """Schema for research project response."""

    id: str
    name: str
    description: Optional[str]
    goal: str
    status: str

    schedule_type: str
    schedule_cron: Optional[str]
    next_run_at: Optional[datetime]
    last_run_at: Optional[datetime]

    auto_generate_tasks: bool
    max_tasks_per_run: int

    default_max_sources: int
    default_depth: str
    default_source_types: Optional[List[str]]

    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    total_sources_added: int

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ResearchProjectListItem(BaseModel):
    """Schema for research project list item (summary view)."""

    id: str
    name: str
    status: str
    schedule_type: str
    next_run_at: Optional[datetime]
    last_run_at: Optional[datetime]
    total_tasks: int
    completed_tasks: int
    total_sources_added: int
    created_at: datetime

    class Config:
        from_attributes = True


class ResearchProjectList(BaseModel):
    """Schema for paginated research project list."""

    projects: List[ResearchProjectListItem]
    total: int
    limit: int
    offset: int


class ResearchProjectProgress(BaseModel):
    """Schema for project progress summary."""

    project_id: str
    name: str
    status: str

    total_tasks: int
    completed_tasks: int
    running_tasks: int
    failed_tasks: int
    queued_tasks: int

    total_sources_added: int
    total_sources_failed: int

    last_run_at: Optional[datetime]
    next_run_at: Optional[datetime]

    recent_tasks: List["TaskSummary"]


class TaskSummary(BaseModel):
    """Summary of a research task for progress view."""

    id: str
    query: str
    status: str
    sources_added: int
    created_at: datetime
    completed_at: Optional[datetime]


class TaskGenerationRequest(BaseModel):
    """Request to generate tasks from project goal."""

    count: int = Field(5, ge=1, le=20, description="Number of tasks to generate")
    consider_existing: bool = Field(
        True, description="Consider existing tasks to avoid duplicates"
    )


class TaskGenerationResponse(BaseModel):
    """Response with generated task queries."""

    project_id: str
    generated_queries: List[str]
    message: str


class ScheduleUpdateRequest(BaseModel):
    """Request to update project schedule."""

    schedule_type: str = Field(..., description="Schedule type: manual, daily, weekly, monthly, custom")
    schedule_cron: Optional[str] = Field(None, description="Custom cron expression")

    @field_validator("schedule_type")
    @classmethod
    def validate_schedule_type(cls, v):
        """Validate schedule_type field."""
        allowed = ["manual", "daily", "weekly", "monthly", "custom"]
        if v not in allowed:
            raise ValueError(f"Schedule type must be one of: {', '.join(allowed)}")
        return v


class RunProjectResponse(BaseModel):
    """Response when manually running a project."""

    project_id: str
    task_ids: List[str]
    message: str
