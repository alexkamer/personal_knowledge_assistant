"""
Research source model for tracking web sources found during research.
"""
from typing import Optional, List
import uuid

from sqlalchemy import Integer, String, Text, Float, ForeignKey, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class ResearchSource(Base, UUIDMixin, TimestampMixin):
    """
    Web source found and processed during autonomous research.

    Tracks the URL, credibility score, and processing status of each
    source discovered during a research task.
    """

    __tablename__ = "research_sources"

    # Foreign keys
    research_task_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("research_tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    document_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=True,
    )

    # Source info
    url: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    domain: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    source_type: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # academic, news, blog, reddit, github

    # Credibility
    credibility_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    credibility_reasons: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String), nullable=True
    )

    # Processing status
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", index=True
    )  # pending, scraped, failed, skipped
    failure_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    research_task: Mapped["ResearchTask"] = relationship(
        "ResearchTask",
        back_populates="sources",
    )

    document: Mapped[Optional["Document"]] = relationship(
        "Document",
        back_populates="research_source",
        foreign_keys=[document_id],
    )

    def __repr__(self) -> str:
        return f"<ResearchSource(id={self.id}, url='{self.url[:50]}...', status='{self.status}')>"
