"""
Research project model for Research Autopilot.

A research project is a collection of related research tasks that run on a schedule.
"""
from datetime import datetime
from typing import Optional, List

from sqlalchemy import Integer, String, Text, DateTime, Boolean, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class ResearchProject(Base, UUIDMixin, TimestampMixin):
    """
    Research project for autonomous, scheduled research.

    Projects are long-term research goals that generate and execute
    multiple research tasks on a schedule.
    """

    __tablename__ = "research_projects"

    # Basic info
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    goal: Mapped[str] = mapped_column(
        Text, nullable=False
    )  # Main research objective

    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active", index=True
    )  # active, paused, completed, archived

    # Scheduling
    schedule_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="manual"
    )  # manual, daily, weekly, monthly, custom
    schedule_cron: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )  # Custom cron expression
    next_run_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_run_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Task generation settings
    auto_generate_tasks: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    max_tasks_per_run: Mapped[int] = mapped_column(
        Integer, default=5, nullable=False
    )  # Max tasks to run per scheduled execution

    # Research settings (defaults for generated tasks)
    default_max_sources: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    default_depth: Mapped[str] = mapped_column(
        String(20), default="thorough", nullable=False
    )
    # Use JSON instead of ARRAY for SQLite compatibility in tests
    default_source_types: Mapped[Optional[List[str]]] = mapped_column(
        JSON, nullable=True
    )

    # Progress tracking
    total_tasks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completed_tasks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_tasks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_sources_added: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    tasks: Mapped[List["ResearchTask"]] = relationship(
        "ResearchTask",
        back_populates="project",
        foreign_keys="ResearchTask.project_id",
        cascade="all, delete-orphan",
    )

    briefings: Mapped[List["ResearchBriefing"]] = relationship(
        "ResearchBriefing",
        back_populates="project",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<ResearchProject(id={self.id}, name='{self.name}', status='{self.status}')>"
