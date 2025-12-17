"""
Chunk model for text chunks from notes and documents.
"""
from typing import Optional
from uuid import UUID

from sqlalchemy import Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class Chunk(Base, UUIDMixin, TimestampMixin):
    """
    Text chunk from a note or document.

    Each chunk is embedded and stored in ChromaDB for vector search.
    The chunk record links the vector embedding to its source.
    """

    __tablename__ = "chunks"

    content: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)

    # Source reference (exactly one of: note_id, document_id, youtube_video_id)
    note_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("notes.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    document_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    youtube_video_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("youtube_videos.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # ChromaDB reference (optional, defaults to chunk ID)
    vector_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, unique=True)

    # Metadata
    token_count: Mapped[int] = mapped_column(Integer, nullable=False)

    # Semantic metadata (enriched chunking)
    content_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    heading_hierarchy: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    section_title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, index=True)
    has_code: Mapped[Optional[bool]] = mapped_column(Integer, nullable=True, default=False)
    semantic_density: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Relationships
    note: Mapped[Optional["Note"]] = relationship("Note", back_populates="chunks")
    document: Mapped[Optional["Document"]] = relationship(
        "Document", back_populates="chunks"
    )
    youtube_video: Mapped[Optional["YouTubeVideo"]] = relationship(
        "YouTubeVideo", back_populates="chunks"
    )

    def __repr__(self) -> str:
        if self.note_id:
            source = f"note={self.note_id}"
        elif self.document_id:
            source = f"document={self.document_id}"
        else:
            source = f"youtube_video={self.youtube_video_id}"
        return f"<Chunk(id={self.id}, {source}, index={self.chunk_index})>"
