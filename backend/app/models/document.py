"""
Document model for uploaded files.
"""
from typing import Optional
from datetime import date

from sqlalchemy import Integer, String, Text, Float, ForeignKey, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class Document(Base, UUIDMixin, TimestampMixin):
    """
    Uploaded document (PDF, DOCX, TXT, MD, etc.).

    Documents are processed, chunked, and embedded for RAG retrieval.
    """

    __tablename__ = "documents"

    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)

    # Archive fields (for external drive storage)
    archive_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    storage_location: Mapped[str] = mapped_column(
        String(20), nullable=False, default="local", index=True
    )  # local, archive

    # Extracted content
    content: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Research-related fields (for web research sources)
    source_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="upload", index=True
    )  # upload, web_research, youtube, manual_entry
    source_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    author: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    published_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    credibility_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    research_task_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("research_tasks.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Relationships
    chunks: Mapped[list["Chunk"]] = relationship(
        "Chunk",
        back_populates="document",
        cascade="all, delete-orphan",
    )

    research_task: Mapped[Optional["ResearchTask"]] = relationship(
        "ResearchTask",
        back_populates="documents",
        foreign_keys=[research_task_id],
    )

    research_source: Mapped[Optional["ResearchSource"]] = relationship(
        "ResearchSource",
        back_populates="document",
        uselist=False,
    )

    def __repr__(self) -> str:
        return f"<Document(id={self.id}, filename='{self.filename}')>"
