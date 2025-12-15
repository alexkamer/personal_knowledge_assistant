"""
Chunk model for text chunks from notes and documents.
"""
from typing import Optional
from uuid import UUID

from sqlalchemy import ForeignKey, Integer, String, Text
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

    # Source reference (either note_id or document_id)
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

    # ChromaDB reference (optional, defaults to chunk ID)
    vector_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, unique=True)

    # Metadata
    token_count: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relationships
    note: Mapped[Optional["Note"]] = relationship("Note", back_populates="chunks")
    document: Mapped[Optional["Document"]] = relationship(
        "Document", back_populates="chunks"
    )

    def __repr__(self) -> str:
        source = f"note={self.note_id}" if self.note_id else f"document={self.document_id}"
        return f"<Chunk(id={self.id}, {source}, index={self.chunk_index})>"
