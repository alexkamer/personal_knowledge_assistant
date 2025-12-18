"""
Research task model for autonomous web research.
"""
from datetime import datetime
from typing import Optional, List

from sqlalchemy import Integer, String, Text, DateTime, Float, ARRAY
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class ResearchTask(Base, UUIDMixin, TimestampMixin):
    """
    Autonomous web research task.

    Tracks the status and progress of background research jobs that
    search the web, scrape content, and add sources to the knowledge base.
    """

    __tablename__ = "research_tasks"

    # Query and settings
    query: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="queued", index=True
    )  # queued, running, completed, failed, cancelled

    max_sources: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    depth: Mapped[str] = mapped_column(
        String(20), default="thorough", nullable=False
    )  # quick, thorough, deep
    source_types: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String), nullable=True
    )  # academic, news, blogs, reddit, github

    # Progress tracking
    sources_found: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sources_scraped: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sources_added: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sources_failed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sources_skipped: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    current_step: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    progress_percentage: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    estimated_time_remaining: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # seconds

    # Results
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    key_findings: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True
    )  # Structured findings
    contradictions_found: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    suggested_followups: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String), nullable=True
    )

    # Background job tracking
    job_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )  # RQ job ID
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    sources: Mapped[List["ResearchSource"]] = relationship(
        "ResearchSource",
        back_populates="research_task",
        cascade="all, delete-orphan",
    )

    documents: Mapped[List["Document"]] = relationship(
        "Document",
        back_populates="research_task",
        foreign_keys="Document.research_task_id",
    )

    def __repr__(self) -> str:
        return f"<ResearchTask(id={self.id}, query='{self.query[:50]}...', status='{self.status}')>"
