"""
Document model for uploaded files.
"""
from sqlalchemy import Integer, String, Text
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

    # Extracted content
    content: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    chunks: Mapped[list["Chunk"]] = relationship(
        "Chunk",
        back_populates="document",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Document(id={self.id}, filename='{self.filename}')>"
