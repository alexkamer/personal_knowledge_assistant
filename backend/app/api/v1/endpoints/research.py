"""
Research task management endpoints.
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.research_task import ResearchTask
from app.models.research_source import ResearchSource
from app.schemas.research import (
    ResearchTaskCreate,
    ResearchTaskResponse,
    ResearchTaskList,
    ResearchTaskListItem,
    ResearchResultsResponse,
    ResearchSourceResponse,
    ResearchTaskStart,
)
from app.services.research_orchestrator import get_research_orchestrator

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/start", response_model=ResearchTaskStart, status_code=status.HTTP_201_CREATED)
async def start_research(
    research_data: ResearchTaskCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> ResearchTaskStart:
    """
    Start a new research task.

    The research runs in the background and processes:
    1. Web search for sources
    2. Credibility filtering
    3. Content scraping
    4. Document creation and RAG processing

    Poll GET /tasks/{task_id} for progress updates.
    """
    try:
        # Create task record
        task = ResearchTask(
            query=research_data.query,
            max_sources=research_data.max_sources,
            depth=research_data.depth,
            source_types=research_data.source_types,
            status="queued",
        )

        db.add(task)
        await db.commit()
        await db.refresh(task)

        logger.info(f"Created research task {task.id} for query: {research_data.query}")

        # Run research in background
        # MVP: Run synchronously (Phase 2: Use RQ for true background processing)
        background_tasks.add_task(
            run_research_task,
            task_id=str(task.id),
            query=research_data.query,
            max_sources=research_data.max_sources,
            depth=research_data.depth,
            source_types=research_data.source_types,
        )

        return ResearchTaskStart(
            task_id=str(task.id),
            status="queued",
            message="Research task started. Check progress at /api/v1/research/tasks/{task_id}",
        )

    except Exception as e:
        logger.error(f"Failed to start research: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start research: {str(e)}",
        )


async def run_research_task(
    task_id: str,
    query: str,
    max_sources: int,
    depth: str,
    source_types: Optional[list],
):
    """
    Background task to run research.

    Note: This creates a new DB session since it runs in background.
    """
    from app.core.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        try:
            orchestrator = get_research_orchestrator()
            await orchestrator.deep_research(
                db=db,
                task_id=task_id,
                query=query,
                max_sources=max_sources,
                depth=depth,
                source_types=source_types,
            )
        except Exception as e:
            logger.error(f"Research task {task_id} failed: {e}")
            # Task status already updated by orchestrator


@router.get("/tasks", response_model=ResearchTaskList)
async def list_research_tasks(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status_filter: Optional[str] = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
) -> ResearchTaskList:
    """
    List all research tasks with pagination.

    Optionally filter by status: queued, running, completed, failed, cancelled
    """
    # Build query
    query = select(ResearchTask)

    if status_filter:
        query = query.where(ResearchTask.status == status_filter)

    # Get total count
    count_query = select(func.count()).select_from(ResearchTask)
    if status_filter:
        count_query = count_query.where(ResearchTask.status == status_filter)

    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Get paginated tasks
    query = query.order_by(desc(ResearchTask.created_at)).offset(offset).limit(limit)
    result = await db.execute(query)
    tasks = result.scalars().all()

    return ResearchTaskList(
        tasks=[
            ResearchTaskListItem(
                id=str(task.id),
                query=task.query,
                status=task.status,
                sources_added=task.sources_added,
                sources_failed=task.sources_failed,
                created_at=task.created_at,
                completed_at=task.completed_at,
            )
            for task in tasks
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/tasks/{task_id}", response_model=ResearchTaskResponse)
async def get_research_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
) -> ResearchTaskResponse:
    """
    Get detailed status and progress for a research task.

    Use this endpoint to poll for progress updates during research.
    """
    result = await db.execute(select(ResearchTask).where(ResearchTask.id == task_id))
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Research task {task_id} not found",
        )

    return ResearchTaskResponse(
        id=str(task.id),
        query=task.query,
        status=task.status,
        max_sources=task.max_sources,
        depth=task.depth,
        source_types=task.source_types,
        sources_found=task.sources_found,
        sources_scraped=task.sources_scraped,
        sources_added=task.sources_added,
        sources_failed=task.sources_failed,
        sources_skipped=task.sources_skipped,
        current_step=task.current_step,
        progress_percentage=task.progress_percentage,
        estimated_time_remaining=task.estimated_time_remaining,
        summary=task.summary,
        contradictions_found=task.contradictions_found,
        suggested_followups=task.suggested_followups,
        job_id=task.job_id,
        error_message=task.error_message,
        started_at=task.started_at,
        completed_at=task.completed_at,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


@router.get("/tasks/{task_id}/results", response_model=ResearchResultsResponse)
async def get_research_results(
    task_id: str,
    db: AsyncSession = Depends(get_db),
) -> ResearchResultsResponse:
    """
    Get research results summary including all sources.

    Only available for completed tasks.
    """
    # Get task
    result = await db.execute(select(ResearchTask).where(ResearchTask.id == task_id))
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Research task {task_id} not found",
        )

    if task.status not in ["completed", "failed"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Research task is not yet complete (status: {task.status})",
        )

    # Get sources with documents
    from sqlalchemy.orm import selectinload
    from app.models.document import Document

    sources_result = await db.execute(
        select(ResearchSource)
        .where(ResearchSource.research_task_id == task_id)
        .options(selectinload(ResearchSource.document))
        .order_by(desc(ResearchSource.credibility_score))
    )
    sources = sources_result.scalars().all()

    return ResearchResultsResponse(
        task_id=str(task.id),
        query=task.query,
        status=task.status,
        summary=task.summary,
        key_findings=task.key_findings,
        sources=[
            ResearchSourceResponse(
                id=str(source.id),
                url=source.url,
                title=source.title,
                domain=source.domain,
                source_type=source.source_type,
                credibility_score=source.credibility_score,
                credibility_reasons=source.credibility_reasons,
                status=source.status,
                failure_reason=source.failure_reason,
                document_id=str(source.document_id) if source.document_id else None,
                content=source.document.content if source.document else None,
                created_at=source.created_at,
            )
            for source in sources
        ],
        contradictions_found=task.contradictions_found,
        suggested_followups=task.suggested_followups,
        sources_added=task.sources_added,
        sources_failed=task.sources_failed,
        sources_skipped=task.sources_skipped,
        completed_at=task.completed_at,
    )


@router.post("/tasks/{task_id}/cancel")
async def cancel_research_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Cancel a running research task.

    Note: MVP implementation - cancellation may not be immediate.
    """
    result = await db.execute(select(ResearchTask).where(ResearchTask.id == task_id))
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Research task {task_id} not found",
        )

    if task.status not in ["queued", "running"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel task with status: {task.status}",
        )

    task.status = "cancelled"
    await db.commit()

    return {"message": "Research task cancelled"}


@router.delete("/tasks/{task_id}")
async def delete_research_task(
    task_id: str,
    delete_sources: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a research task.

    If delete_sources=true, also deletes the documents created during research.
    """
    result = await db.execute(select(ResearchTask).where(ResearchTask.id == task_id))
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Research task {task_id} not found",
        )

    # Optionally delete documents
    if delete_sources:
        # Documents will be cascade deleted when task is deleted
        # due to the foreign key relationship
        pass

    await db.delete(task)
    await db.commit()

    return {"message": "Research task deleted"}
