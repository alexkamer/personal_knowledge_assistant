"""
Learning Gaps Detection API endpoints.

Provides endpoints for analyzing user questions to detect foundational knowledge gaps
and generate personalized learning paths.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.learning_gaps import (
    LearningGapRequest,
    LearningGapResponse,
    LearningPathRequest,
    LearningPathResponse,
)
from app.services.learning_gaps_service import LearningGapsService
from app.services.llm_service import get_llm_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["learning_gaps"])


@router.post("/detect", response_model=LearningGapResponse)
async def detect_learning_gaps(
    request: LearningGapRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Detect foundational knowledge gaps based on user's question.

    This endpoint analyzes the user's question and conversation history to identify
    prerequisite concepts they may be missing. It helps users build complete
    understanding by revealing what they need to learn first.

    Args:
        request: Contains user_question, conversation_history, and optional context
        db: Database session

    Returns:
        LearningGapResponse with detected gaps and importance levels

    Raises:
        HTTPException: If gap detection fails
    """
    try:
        llm_service = get_llm_service()
        gaps_service = LearningGapsService(llm_service)

        # Detect gaps
        gaps = await gaps_service.detect_gaps(
            user_question=request.user_question,
            conversation_history=request.conversation_history or [],
            context=request.context or "",
            model=request.model or "qwen2.5:14b",
        )

        return LearningGapResponse(
            user_question=request.user_question,
            gaps=[
                {
                    "topic": gap.topic,
                    "description": gap.description,
                    "prerequisite_for": gap.prerequisite_for,
                    "importance": gap.importance,
                    "learning_resources": gap.learning_resources,
                    "estimated_time": gap.estimated_time,
                }
                for gap in gaps
            ],
            total_gaps=len(gaps),
        )

    except Exception as e:
        logger.error(f"Error detecting learning gaps: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to detect learning gaps: {str(e)}",
        )


@router.post("/path", response_model=LearningPathResponse)
async def generate_learning_path(
    request: LearningPathRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Generate a personalized learning path from detected gaps.

    Takes detected knowledge gaps and creates an optimal learning sequence that
    orders topics from foundational to advanced, showing dependencies and
    providing a structured progression.

    Args:
        request: Contains user_question and detected gaps
        db: Database session

    Returns:
        LearningPathResponse with sequenced learning steps

    Raises:
        HTTPException: If path generation fails
    """
    try:
        llm_service = get_llm_service()
        gaps_service = LearningGapsService(llm_service)

        # Convert request gaps to LearningGap objects
        from app.services.learning_gaps_service import LearningGap

        gap_objects = [
            LearningGap(
                topic=gap["topic"],
                description=gap["description"],
                prerequisite_for=gap["prerequisite_for"],
                importance=gap["importance"],
                learning_resources=gap["learning_resources"],
                estimated_time=gap["estimated_time"],
            )
            for gap in request.gaps
        ]

        # Generate learning path
        path = await gaps_service.generate_learning_path(
            user_question=request.user_question,
            gaps=gap_objects,
            model=request.model or "qwen2.5:14b",
        )

        return LearningPathResponse(
            target_topic=path.target_topic,
            learning_sequence=path.learning_sequence,
            total_estimated_time=path.total_estimated_time,
            gaps=[
                {
                    "topic": gap.topic,
                    "description": gap.description,
                    "prerequisite_for": gap.prerequisite_for,
                    "importance": gap.importance,
                    "learning_resources": gap.learning_resources,
                    "estimated_time": gap.estimated_time,
                }
                for gap in path.gaps
            ],
        )

    except Exception as e:
        logger.error(f"Error generating learning path: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate learning path: {str(e)}",
        )
