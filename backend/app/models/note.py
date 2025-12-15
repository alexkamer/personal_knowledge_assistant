"""
Note model for user-created notes.
"""
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class Note(Base, UUIDMixin, TimestampMixin):
    """
    User note with title and content.

    Each note is chunked and embedded for RAG retrieval.
    """

    __tablename__ = "notes"

    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    tags: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Relationships
    chunks: Mapped[list["Chunk"]] = relationship(
        "Chunk",
        back_populates="note",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Note(id={self.id}, title='{self.title}')>"
