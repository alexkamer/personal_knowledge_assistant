"""
Knowledge Evolution API endpoints.

Provides endpoints for:
- Creating conceptual snapshots
- Retrieving snapshots by topic
- Analyzing evolution between snapshots
- Viewing learning timeline
"""

from typing import List, Optional
from uuid import UUID, uuid4
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.knowledge_evolution_service import KnowledgeEvolutionService
from app.services.llm_service import get_llm_service
from app.schemas.knowledge_evolution import (
    SnapshotCreationRequest,
    SnapshotResponse,
    EvolutionAnalysisResponse,
    TimelineResponse,
)

router = APIRouter()


def get_knowledge_evolution_service():
    """Get Knowledge Evolution service instance."""
    llm_service = get_llm_service()
    return KnowledgeEvolutionService(llm_service)


@router.post("/snapshots", response_model=SnapshotResponse)
async def create_snapshot(
    request: SnapshotCreationRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new conceptual snapshot from a conversation.

    This captures the user's current understanding of a topic at a point in time,
    allowing tracking of learning progress over time.
    """
    service = get_knowledge_evolution_service()

    # Create snapshot using the service
    snapshot = await service.create_conceptual_snapshot(
        topic=request.topic,
        conversation_messages=request.conversation_messages,
        conversation_id=request.conversation_id,
        timestamp=request.timestamp or datetime.utcnow(),
        model=request.model,
    )

    # TODO: Store snapshot in database
    # For now, return the snapshot from LLM analysis
    return SnapshotResponse(
        id=str(uuid4()),
        topic=request.topic,
        understanding=snapshot["understanding"],
        key_concepts=snapshot["key_concepts"],
        misconceptions=snapshot["misconceptions"],
        confidence=snapshot["confidence"],
        questions_asked=snapshot["questions_asked"],
        conversation_id=request.conversation_id,
        timestamp=request.timestamp or datetime.utcnow(),
        created_at=datetime.utcnow(),
    )


@router.get("/snapshots/topic/{topic}", response_model=List[SnapshotResponse])
async def get_snapshots_by_topic(
    topic: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get all conceptual snapshots for a specific topic.

    Returns snapshots ordered by timestamp (oldest to newest).
    """
    # TODO: Query database for snapshots
    # For now, return empty list as no persistence layer yet
    return []


@router.get("/evolution/{topic}", response_model=EvolutionAnalysisResponse)
async def get_evolution_analysis(
    topic: str,
    start_date: Optional[str] = Query(None, description="Start date for comparison (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date for comparison (ISO format)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get evolution analysis for a topic between two time periods.

    Compares the earliest and latest snapshots (or snapshots within date range)
    to show how understanding has evolved.
    """
    service = get_knowledge_evolution_service()

    # TODO: Query database for snapshots in date range
    # For now, return error as no snapshots exist yet
    raise HTTPException(
        status_code=404,
        detail=f"No snapshots found for topic '{topic}'. Create snapshots first.",
    )


@router.get("/timeline", response_model=TimelineResponse)
async def get_learning_timeline(
    db: AsyncSession = Depends(get_db),
):
    """
    Get timeline of all topics the user has learned about.

    Returns a list of topics with snapshot counts and date ranges.
    """
    # TODO: Query database for all topics with snapshots
    # For now, return empty timeline
    return TimelineResponse(topics=[], total_snapshots=0)
