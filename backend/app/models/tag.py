"""
Tag model for organizing notes.
"""
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class Tag(Base, UUIDMixin, TimestampMixin):
    """
    Tag for categorizing notes.

    Tags have a unique name (case-insensitive) and can be associated
    with multiple notes through the note_tags junction table.
    """

    __tablename__ = "tags"

    name: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )

    # Many-to-many relationship with notes
    notes: Mapped[list["Note"]] = relationship(
        "Note",
        secondary="note_tags",
        back_populates="tags_rel",
    )

    def __repr__(self) -> str:
        return f"<Tag(id={self.id}, name='{self.name}')>"
