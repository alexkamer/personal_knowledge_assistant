"""
Conceptual Snapshot database model.

Stores snapshots of user understanding at points in time for tracking learning evolution.
"""

from datetime import datetime
from typing import List
from uuid import UUID, uuid4

from sqlalchemy import Column, String, Text, Float, DateTime, ForeignKey, ARRAY
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class ConceptualSnapshot(Base):
    """
    Represents a snapshot of user's understanding of a topic at a point in time.

    Used by Innovation 5: Knowledge Evolution Timeline to track learning progress.
    """

    __tablename__ = "conceptual_snapshots"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    topic = Column(String(500), nullable=False, index=True)  # What topic this snapshot is about
    understanding = Column(Text, nullable=False)  # LLM-generated summary of understanding
    key_concepts = Column(ARRAY(String), nullable=False, default=list)  # Concepts understood
    misconceptions = Column(ARRAY(String), nullable=False, default=list)  # Incorrect beliefs
    confidence = Column(Float, nullable=False)  # 0.0-1.0 confidence score
    questions_asked = Column(ARRAY(String), nullable=False, default=list)  # Questions they asked

    # Relationships
    conversation_id = Column(PGUUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False)
    conversation = relationship("Conversation", back_populates="conceptual_snapshots")

    # Timestamps
    timestamp = Column(DateTime(timezone=True), nullable=False)  # When understanding was captured
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<ConceptualSnapshot(id={self.id}, topic='{self.topic}', confidence={self.confidence})>"
