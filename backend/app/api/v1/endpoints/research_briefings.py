"""
Research briefing management endpoints.
"""
import logging
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status, Response
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.research_briefing import ResearchBriefing
from app.schemas.research_briefing import (
    ResearchBriefingCreate,
    ResearchBriefingResponse,
    ResearchBriefingList,
    ResearchBriefingListItem,
    BriefingMarkdown,
)
from app.services.briefing_generator_service import get_briefing_generator_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/briefings", response_model=ResearchBriefingList)
async def list_briefings(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> ResearchBriefingList:
    """
    List all research briefings across all projects with pagination.
    """
    try:
        # Get total count
        count_query = select(func.count()).select_from(ResearchBriefing)
        total_result = await db.execute(count_query)
        total = total_result.scalar_one()

        # Get paginated briefings
        query = (
            select(ResearchBriefing)
            .order_by(desc(ResearchBriefing.generated_at))
            .offset(offset)
            .limit(limit)
        )
        result = await db.execute(query)
        briefings = result.scalars().all()

        return ResearchBriefingList(
            briefings=[
                ResearchBriefingListItem.model_validate(briefing)
                for briefing in briefings
            ],
            total=total,
            limit=limit,
            offset=offset,
        )

    except Exception as e:
        logger.error(f"Failed to list briefings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list briefings: {str(e)}",
        )


@router.get("/briefings/{briefing_id}", response_model=ResearchBriefingResponse)
async def get_briefing(
    briefing_id: str,
    db: AsyncSession = Depends(get_db),
) -> ResearchBriefingResponse:
    """
    Get detailed information about a specific research briefing.
    """
    result = await db.execute(
        select(ResearchBriefing).where(ResearchBriefing.id == briefing_id)
    )
    briefing = result.scalar_one_or_none()

    if not briefing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Briefing {briefing_id} not found",
        )

    return ResearchBriefingResponse.model_validate(briefing)


@router.get("/projects/{project_id}/briefings", response_model=ResearchBriefingList)
async def list_project_briefings(
    project_id: str,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> ResearchBriefingList:
    """
    List all briefings for a specific project.
    """
    try:
        # Get total count for project
        count_query = select(func.count()).select_from(ResearchBriefing).where(
            ResearchBriefing.project_id == project_id
        )
        total_result = await db.execute(count_query)
        total = total_result.scalar_one()

        # Get paginated briefings
        query = (
            select(ResearchBriefing)
            .where(ResearchBriefing.project_id == project_id)
            .order_by(desc(ResearchBriefing.generated_at))
            .offset(offset)
            .limit(limit)
        )
        result = await db.execute(query)
        briefings = result.scalars().all()

        return ResearchBriefingList(
            briefings=[
                ResearchBriefingListItem.model_validate(briefing)
                for briefing in briefings
            ],
            total=total,
            limit=limit,
            offset=offset,
        )

    except Exception as e:
        logger.error(f"Failed to list briefings for project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list briefings: {str(e)}",
        )


@router.post("/projects/{project_id}/briefings", response_model=ResearchBriefingResponse, status_code=status.HTTP_201_CREATED)
async def generate_briefing(
    project_id: str,
    request: ResearchBriefingCreate,
    db: AsyncSession = Depends(get_db),
) -> ResearchBriefingResponse:
    """
    Generate a new research briefing for a project.

    Analyzes completed tasks and their sources, synthesizes findings,
    identifies contradictions, detects knowledge gaps, and suggests follow-ups.

    If task_ids is provided, only those tasks are included.
    Otherwise, all completed tasks for the project are analyzed.
    """
    try:
        service = get_briefing_generator_service()

        briefing = await service.generate_briefing(
            db,
            project_id=project_id,
            task_ids=request.task_ids,
        )

        return ResearchBriefingResponse.model_validate(briefing)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Failed to generate briefing for project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate briefing: {str(e)}",
        )


@router.delete("/briefings/{briefing_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_briefing(
    briefing_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a research briefing.
    """
    try:
        result = await db.execute(
            select(ResearchBriefing).where(ResearchBriefing.id == briefing_id)
        )
        briefing = result.scalar_one_or_none()

        if not briefing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Briefing {briefing_id} not found",
            )

        await db.delete(briefing)
        await db.commit()

        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete briefing {briefing_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete briefing: {str(e)}",
        )


@router.get("/briefings/{briefing_id}/markdown", response_model=BriefingMarkdown)
async def export_briefing_markdown(
    briefing_id: str,
    db: AsyncSession = Depends(get_db),
) -> BriefingMarkdown:
    """
    Export a briefing as markdown format.

    Useful for copying to notes, exporting to PDF, or sharing.
    """
    try:
        service = get_briefing_generator_service()

        markdown = await service.format_briefing_markdown(db, briefing_id)

        # Get briefing title
        result = await db.execute(
            select(ResearchBriefing).where(ResearchBriefing.id == briefing_id)
        )
        briefing = result.scalar_one_or_none()

        if not briefing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Briefing {briefing_id} not found",
            )

        return BriefingMarkdown(
            markdown=markdown,
            title=briefing.title,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export briefing {briefing_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export briefing: {str(e)}",
        )


@router.post("/briefings/{briefing_id}/view", response_model=ResearchBriefingResponse)
async def mark_briefing_viewed(
    briefing_id: str,
    db: AsyncSession = Depends(get_db),
) -> ResearchBriefingResponse:
    """
    Mark a briefing as viewed (sets viewed_at timestamp).

    Useful for tracking which briefings have been reviewed.
    """
    try:
        result = await db.execute(
            select(ResearchBriefing).where(ResearchBriefing.id == briefing_id)
        )
        briefing = result.scalar_one_or_none()

        if not briefing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Briefing {briefing_id} not found",
            )

        # Set viewed_at if not already set
        if not briefing.viewed_at:
            briefing.viewed_at = datetime.utcnow()
            await db.commit()
            await db.refresh(briefing)

        return ResearchBriefingResponse.model_validate(briefing)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to mark briefing {briefing_id} as viewed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark briefing as viewed: {str(e)}",
        )
