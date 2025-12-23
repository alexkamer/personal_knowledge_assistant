"""
Research briefing model for synthesized research findings.
"""
from datetime import datetime
from typing import Optional, List

from sqlalchemy import Integer, String, Text, DateTime, ForeignKey, ARRAY
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class ResearchBriefing(Base, UUIDMixin, TimestampMixin):
    """
    Synthesized research briefing from multiple tasks/sources.

    Briefings are AI-generated summaries that synthesize findings,
    identify contradictions, and suggest follow-up research.
    """

    __tablename__ = "research_briefings"

    # Foreign key
    project_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("research_projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Briefing content
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    key_findings: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True
    )  # Structured findings with citations
    contradictions: Mapped[Optional[List[dict]]] = mapped_column(
        JSONB, nullable=True
    )  # Contradictions found across sources
    knowledge_gaps: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String), nullable=True
    )  # Identified gaps in research
    suggested_tasks: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String), nullable=True
    )  # Suggested follow-up research tasks

    # Related tasks (UUIDs of tasks included in this briefing)
    task_ids: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), nullable=True)
    sources_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Metadata
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    viewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    project: Mapped["ResearchProject"] = relationship(
        "ResearchProject",
        back_populates="briefings",
    )

    def __repr__(self) -> str:
        return f"<ResearchBriefing(id={self.id}, title='{self.title[:50]}...', generated_at='{self.generated_at}')>"
