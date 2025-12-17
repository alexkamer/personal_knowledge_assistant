"""
Pydantic schemas for Knowledge Evolution API.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class SnapshotCreationRequest(BaseModel):
    """Request to create a new conceptual snapshot."""

    topic: str = Field(..., description="The topic this snapshot is about")
    conversation_messages: List[dict] = Field(
        ..., description="Conversation messages to analyze (role + content)"
    )
    conversation_id: str = Field(..., description="ID of the conversation this snapshot is from")
    timestamp: Optional[datetime] = Field(
        None, description="Timestamp for the snapshot (defaults to now)"
    )
    model: Optional[str] = Field(None, description="LLM model to use for analysis")


class SnapshotResponse(BaseModel):
    """Response containing a conceptual snapshot."""

    id: str = Field(..., description="Unique identifier for the snapshot")
    topic: str = Field(..., description="The topic this snapshot is about")
    understanding: str = Field(..., description="Summary of current understanding")
    key_concepts: List[str] = Field(..., description="List of concepts understood")
    misconceptions: List[str] = Field(..., description="List of incorrect beliefs")
    confidence: float = Field(..., description="Confidence score (0.0-1.0)")
    questions_asked: List[str] = Field(..., description="Questions asked in the conversation")
    conversation_id: str = Field(..., description="ID of the source conversation")
    timestamp: datetime = Field(..., description="When this understanding was captured")
    created_at: datetime = Field(..., description="When the snapshot was created")


class EvolutionAnalysisResponse(BaseModel):
    """Response containing evolution analysis between two snapshots."""

    topic: str = Field(..., description="The topic being analyzed")
    earlier_snapshot: SnapshotResponse = Field(..., description="Earlier snapshot")
    later_snapshot: SnapshotResponse = Field(..., description="Later snapshot")
    concepts_gained: List[str] = Field(..., description="New concepts learned")
    concepts_lost: List[str] = Field(..., description="Concepts no longer mentioned")
    misconceptions_corrected: List[str] = Field(..., description="Misconceptions fixed")
    new_misconceptions: List[str] = Field(..., description="New misconceptions introduced")
    confidence_change: float = Field(..., description="Change in confidence (-1.0 to 1.0)")
    learning_velocity: str = Field(..., description="Speed of learning (slow/moderate/fast)")
    insights: List[str] = Field(..., description="Learning insights and observations")


class TimelineItem(BaseModel):
    """A topic in the learning timeline."""

    topic: str = Field(..., description="Topic name")
    snapshot_count: int = Field(..., description="Number of snapshots for this topic")
    first_snapshot_date: datetime = Field(..., description="Date of first snapshot")
    last_snapshot_date: datetime = Field(..., description="Date of most recent snapshot")
    current_confidence: float = Field(..., description="Current confidence level (0.0-1.0)")


class TimelineResponse(BaseModel):
    """Response containing the complete learning timeline."""

    topics: List[TimelineItem] = Field(..., description="List of topics learned")
    total_snapshots: int = Field(..., description="Total number of snapshots across all topics")
