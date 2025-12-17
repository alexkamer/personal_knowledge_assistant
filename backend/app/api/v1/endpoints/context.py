"""
Context Intelligence API endpoints.

Provides semantic discovery of related content across YouTube videos, notes,
and documents, with optional AI synthesis and suggested questions.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.context import ContextRequest, ContextResponse, ContradictionItem, ContradictionSource
from app.services.context_service import get_context_service
from app.services.contradiction_service import ContradictionDetectionService
from app.services.llm_service import get_llm_service
from app.services.rag_service import get_rag_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["context"])


@router.get("/{source_type}/{source_id}", response_model=ContextResponse)
async def get_context(
    source_type: str,
    source_id: str,
    include_synthesis: bool = Query(
        default=True, description="Include AI-generated synthesis"
    ),
    include_questions: bool = Query(
        default=True, description="Include suggested questions"
    ),
    top_k: int = Query(default=5, ge=1, le=20, description="Number of related items"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get contextual intelligence for a specific piece of content.

    This endpoint analyzes the given content (note, document, or YouTube video)
    and returns:
    - Related content items from across all source types
    - Optional AI-generated synthesis of connections
    - Optional suggested questions for further exploration

    The system uses semantic search to find content that is conceptually related,
    even if it doesn't share exact keywords.

    Args:
        source_type: Type of source ("note", "document", or "youtube")
        source_id: UUID or ID of the source
        include_synthesis: Whether to generate AI synthesis (default: True)
        include_questions: Whether to suggest questions (default: True)
        top_k: Number of related items to return (1-20, default: 5)
        db: Database session

    Returns:
        ContextResponse with related content, synthesis, and questions

    Raises:
        HTTPException: If source not found or invalid source type
    """
    # Validate source_type
    valid_types = ["note", "document", "youtube"]
    if source_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid source_type. Must be one of: {', '.join(valid_types)}",
        )

    context_service = get_context_service()

    try:
        # Find related content
        related = await context_service.get_related_content(
            db=db,
            source_type=source_type,
            source_id=source_id,
            top_k=top_k,
        )

        # Fetch source info for response
        source_content = await context_service._fetch_source_content(
            db, source_type, source_id
        )

        if not source_content:
            raise HTTPException(
                status_code=404,
                detail=f"{source_type.title()} with ID {source_id} not found",
            )

        source_title = source_content.get("title", "Unknown")

        # Generate synthesis if requested and we have related content
        synthesis = None
        if include_synthesis and related:
            synthesis = await context_service.generate_synthesis(
                db=db,
                current_content=source_content,
                related_content=related,
                synthesis_type="connections",
            )

        # Generate questions if requested and we have related content
        questions = []
        if include_questions and related:
            questions = await context_service.suggest_questions(
                db=db,
                current_content=source_content,
                related_content=related,
            )

        # Detect contradictions (only for notes and documents)
        contradiction_items = []
        if source_type in ["note", "document"]:
            llm_service = get_llm_service()
            rag_service = get_rag_service()
            contradiction_service = ContradictionDetectionService(llm_service, rag_service)

            contradictions = await contradiction_service.detect_contradictions_for_source(
                db=db,
                source_type=source_type,
                source_id=source_id,
                top_k=3  # Check top 3 similar sources for contradictions
            )

            # Convert to schema format
            for c in contradictions:
                contradiction_items.append(
                    ContradictionItem(
                        source1=ContradictionSource(
                            type=c.source1_type,
                            id=c.source1_id,
                            title=c.source1_title,
                            excerpt=c.source1_excerpt
                        ),
                        source2=ContradictionSource(
                            type=c.source2_type,
                            id=c.source2_id,
                            title=c.source2_title,
                            excerpt=c.source2_excerpt
                        ),
                        contradiction_type=c.contradiction_type,
                        explanation=c.explanation,
                        severity=c.severity,
                        confidence=c.confidence
                    )
                )

        return ContextResponse(
            source_type=source_type,
            source_id=source_id,
            source_title=source_title,
            related_content=related,
            synthesis=synthesis if synthesis else None,
            suggested_questions=questions,
            contradictions=contradiction_items,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error generating context for {source_type}/{source_id}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate context: {str(e)}",
        )
