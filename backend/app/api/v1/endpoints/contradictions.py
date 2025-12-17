"""
API endpoints for contradiction detection.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_db
from app.services.contradiction_service import ContradictionDetectionService
from app.services.llm_service import get_llm_service
from app.services.rag_service import get_rag_service
from app.schemas.contradictions import ContradictionResponse
from pydantic import BaseModel

router = APIRouter()


class ContradictionSource(BaseModel):
    """Source information for a contradiction."""
    type: str
    id: str
    title: str
    excerpt: str


class ContradictionItem(BaseModel):
    """A detected contradiction."""
    source1: ContradictionSource
    source2: ContradictionSource
    contradiction_type: str
    explanation: str
    severity: str
    confidence: float


class ContradictionsListResponse(BaseModel):
    """Response containing list of contradictions."""
    source_type: str
    source_id: str
    source_title: str
    contradictions: List[ContradictionItem]


@router.get(
    "/{source_type}/{source_id}",
    response_model=ContradictionsListResponse,
    summary="Detect contradictions for a source",
    description="Analyzes a note or document for logical contradictions with other content in the knowledge base."
)
async def detect_contradictions(
    source_type: str,
    source_id: str,
    top_k: int = Query(default=5, ge=1, le=20, description="Number of similar sources to check"),
    db: AsyncSession = Depends(get_db),
):
    """
    Detect contradictions for a specific source.

    This endpoint:
    1. Finds semantically similar content
    2. Uses AI to analyze for logical contradictions
    3. Returns detected contradictions with severity and confidence

    Args:
        source_type: Type of source ("note" or "document")
        source_id: UUID of the source
        top_k: Number of similar sources to analyze (default: 5)

    Returns:
        List of detected contradictions with explanations
    """
    # Validate source type
    if source_type not in ["note", "document"]:
        raise HTTPException(
            status_code=400,
            detail="source_type must be 'note' or 'document'"
        )

    # Get services
    llm_service = get_llm_service()
    rag_service = get_rag_service()
    contradiction_service = ContradictionDetectionService(llm_service, rag_service)

    # Detect contradictions
    contradictions = await contradiction_service.detect_contradictions_for_source(
        db=db,
        source_type=source_type,
        source_id=source_id,
        top_k=top_k
    )

    # Get source title
    source_content = await contradiction_service._get_source_content(db, source_type, source_id)
    source_title = source_content["title"] if source_content else "Unknown"

    # Convert to response format
    contradiction_items = [
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
        for c in contradictions
    ]

    return ContradictionsListResponse(
        source_type=source_type,
        source_id=source_id,
        source_title=source_title,
        contradictions=contradiction_items
    )
