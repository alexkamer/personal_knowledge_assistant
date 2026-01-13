"""
Message feedback model for rating assistant responses.
"""

from typing import Optional

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class MessageFeedback(Base, UUIDMixin, TimestampMixin):
    """
    Feedback for assistant messages.

    Stores user ratings (thumbs up/down) and optional comments
    to help improve the system.
    """

    __tablename__ = "message_feedback"

    message_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        unique=True,  # One feedback per message
    )

    # Rating: True = thumbs up, False = thumbs down
    is_positive: Mapped[bool] = mapped_column(Boolean, nullable=False)

    # Optional comment from user
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationship
    message: Mapped["Message"] = relationship("Message", back_populates="feedback")

    def __repr__(self) -> str:
        rating = "👍" if self.is_positive else "👎"
        return f"<MessageFeedback(message_id={self.message_id}, rating={rating})>"
