"""
YouTube video model for ingested videos.
"""
from sqlalchemy import BigInteger, Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class YouTubeVideo(Base, UUIDMixin, TimestampMixin):
    """
    YouTube video ingested into the knowledge base.

    Videos are processed, transcripts are chunked, and embedded for RAG retrieval.
    """

    __tablename__ = "youtube_videos"

    # YouTube identifiers
    video_id: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    channel: Mapped[str | None] = mapped_column(String(255), nullable=True)
    channel_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Video metadata
    duration: Mapped[int | None] = mapped_column(Integer, nullable=True)  # seconds
    upload_date: Mapped[str | None] = mapped_column(
        String(8), nullable=True
    )  # YYYYMMDD
    thumbnail: Mapped[str | None] = mapped_column(String(500), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    view_count: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    # Transcript metadata
    transcript_language: Mapped[str | None] = mapped_column(String(10), nullable=True)
    is_generated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    chunks: Mapped[list["Chunk"]] = relationship(
        "Chunk",
        back_populates="youtube_video",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<YouTubeVideo(id={self.id}, video_id='{self.video_id}', title='{self.title}')>"
