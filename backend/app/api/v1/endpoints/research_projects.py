"""
Research project management endpoints.
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.research_task import ResearchTask
from app.schemas.research_project import (
    ResearchProjectCreate,
    ResearchProjectUpdate,
    ResearchProjectResponse,
    ResearchProjectList,
    ResearchProjectListItem,
    ResearchProjectProgress,
    TaskGenerationRequest,
    TaskGenerationResponse,
    ScheduleUpdateRequest,
    RunProjectResponse,
)
from app.schemas.research import ResearchTaskResponse
from app.services.research_project_service import get_research_project_service
from app.services.research_scheduler_service import get_research_scheduler

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/projects", response_model=ResearchProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ResearchProjectCreate,
    db: AsyncSession = Depends(get_db),
) -> ResearchProjectResponse:
    """
    Create a new research project.

    The project can be configured to run on a schedule (daily, weekly, monthly, custom cron)
    or manually triggered.
    """
    try:
        service = get_research_project_service()
        project = await service.create_project(db, project_data)

        # Convert to dict while still in session context
        project_dict = {
            "id": str(project.id),
            "name": project.name,
            "description": project.description,
            "goal": project.goal,
            "status": project.status,
            "schedule_type": project.schedule_type,
            "schedule_cron": project.schedule_cron,
            "next_run_at": project.next_run_at,
            "last_run_at": project.last_run_at,
            "auto_generate_tasks": project.auto_generate_tasks,
            "max_tasks_per_run": project.max_tasks_per_run,
            "default_max_sources": project.default_max_sources,
            "default_depth": project.default_depth,
            "default_source_types": project.default_source_types,
            "total_tasks": project.total_tasks,
            "completed_tasks": project.completed_tasks,
            "failed_tasks": project.failed_tasks,
            "total_sources_added": project.total_sources_added,
            "created_at": project.created_at,
            "updated_at": project.updated_at,
        }

        # Schedule if not manual
        if project.schedule_type != "manual":
            try:
                scheduler = get_research_scheduler()
                await scheduler.schedule_project(db, str(project.id))
                logger.info(f"Scheduled project {project.id}")
                # Update next_run_at in response
                await db.refresh(project)
                project_dict["next_run_at"] = project.next_run_at
            except Exception as e:
                logger.error(f"Failed to schedule project {project.id}: {e}")
                # Don't fail the request, project is still created

        return ResearchProjectResponse(**project_dict)

    except Exception as e:
        logger.error(f"Failed to create project: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create project: {str(e)}",
        )


@router.get("/projects", response_model=ResearchProjectList)
async def list_projects(
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> ResearchProjectList:
    """
    List all research projects with pagination and filtering.

    Optionally filter by status: active, paused, completed, archived
    """
    try:
        service = get_research_project_service()
        projects, total = await service.list_projects(
            db, status=status_filter, limit=limit, offset=offset
        )

        return ResearchProjectList(
            projects=[
                ResearchProjectListItem.model_validate(project)
                for project in projects
            ],
            total=total,
            limit=limit,
            offset=offset,
        )

    except Exception as e:
        logger.error(f"Failed to list projects: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list projects: {str(e)}",
        )


@router.get("/projects/{project_id}", response_model=ResearchProjectResponse)
async def get_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> ResearchProjectResponse:
    """
    Get detailed information about a specific research project.
    """
    service = get_research_project_service()
    project = await service.get_project(db, project_id)

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    return ResearchProjectResponse.model_validate(project)


@router.put("/projects/{project_id}", response_model=ResearchProjectResponse)
async def update_project(
    project_id: str,
    updates: ResearchProjectUpdate,
    db: AsyncSession = Depends(get_db),
) -> ResearchProjectResponse:
    """
    Update a research project.

    Can update name, description, goal, status, schedule settings, etc.
    """
    try:
        service = get_research_project_service()
        project = await service.update_project(db, project_id, updates)

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found",
            )

        # If schedule changed, reschedule
        update_data = updates.model_dump(exclude_unset=True)
        if "schedule_type" in update_data or "schedule_cron" in update_data:
            scheduler = get_research_scheduler()

            if project.schedule_type == "manual":
                # Unschedule if changed to manual
                await scheduler.unschedule_project(project_id)
            else:
                # Reschedule with new settings
                await scheduler.reschedule_project(db, project_id)

        return ResearchProjectResponse.model_validate(project)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update project: {str(e)}",
        )


@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    delete_tasks: bool = Query(False, description="Also delete all related tasks"),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a research project.

    If delete_tasks=true, also deletes all tasks and sources created by this project.
    Otherwise, tasks become standalone.
    """
    try:
        # Unschedule first
        scheduler = get_research_scheduler()
        await scheduler.unschedule_project(project_id)

        service = get_research_project_service()
        deleted = await service.delete_project(db, project_id, delete_tasks)

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found",
            )

        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete project: {str(e)}",
        )


# Task Generation


@router.post("/projects/{project_id}/tasks/generate", response_model=TaskGenerationResponse)
async def generate_tasks(
    project_id: str,
    request: TaskGenerationRequest,
    db: AsyncSession = Depends(get_db),
) -> TaskGenerationResponse:
    """
    Generate research task queries using LLM based on project goal.

    Returns suggested queries without creating tasks yet.
    Use POST /projects/{project_id}/tasks to actually create tasks from queries.
    """
    try:
        service = get_research_project_service()

        queries = await service.generate_task_queries(
            db,
            project_id,
            count=request.count,
            consider_existing=request.consider_existing,
        )

        return TaskGenerationResponse(
            project_id=project_id,
            generated_queries=queries,
            message=f"Generated {len(queries)} research task queries",
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Failed to generate tasks for project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate tasks: {str(e)}",
        )


@router.post("/projects/{project_id}/tasks", response_model=list[ResearchTaskResponse])
async def create_tasks(
    project_id: str,
    queries: list[str],
    db: AsyncSession = Depends(get_db),
) -> list[ResearchTaskResponse]:
    """
    Create research tasks from a list of queries.

    Tasks will be created with status="queued" and project defaults.
    """
    try:
        service = get_research_project_service()

        tasks = await service.create_tasks_from_queries(db, project_id, queries)

        return [ResearchTaskResponse.model_validate(task) for task in tasks]

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Failed to create tasks for project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create tasks: {str(e)}",
        )


@router.get("/projects/{project_id}/tasks", response_model=list[ResearchTaskResponse])
async def list_project_tasks(
    project_id: str,
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> list[ResearchTaskResponse]:
    """
    List all tasks for a specific project.

    Optionally filter by status: queued, running, completed, failed, cancelled
    """
    try:
        query = select(ResearchTask).where(ResearchTask.project_id == project_id)

        if status_filter:
            query = query.where(ResearchTask.status == status_filter)

        query = query.order_by(desc(ResearchTask.created_at)).limit(limit)

        result = await db.execute(query)
        tasks = result.scalars().all()

        return [ResearchTaskResponse.model_validate(task) for task in tasks]

    except Exception as e:
        logger.error(f"Failed to list tasks for project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list tasks: {str(e)}",
        )


# Progress


@router.get("/projects/{project_id}/progress", response_model=ResearchProjectProgress)
async def get_project_progress(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> ResearchProjectProgress:
    """
    Get detailed progress information for a project.

    Includes task counts by status, source stats, and recent tasks.
    """
    try:
        service = get_research_project_service()
        progress = await service.get_project_progress(db, project_id)

        if not progress:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found",
            )

        return progress

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get progress for project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get progress: {str(e)}",
        )


# Scheduling


@router.post("/projects/{project_id}/schedule", response_model=ResearchProjectResponse)
async def update_schedule(
    project_id: str,
    schedule: ScheduleUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> ResearchProjectResponse:
    """
    Update the schedule for a project.

    Can change from manual to scheduled or update existing schedule.
    """
    try:
        service = get_research_project_service()

        # Update project schedule settings
        from app.schemas.research_project import ResearchProjectUpdate
        updates = ResearchProjectUpdate(
            schedule_type=schedule.schedule_type,
            schedule_cron=schedule.schedule_cron,
        )

        project = await service.update_project(db, project_id, updates)

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found",
            )

        # Apply scheduling
        scheduler = get_research_scheduler()

        if project.schedule_type == "manual":
            await scheduler.unschedule_project(project_id)
        else:
            await scheduler.reschedule_project(db, project_id)

        return ResearchProjectResponse.model_validate(project)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update schedule for project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update schedule: {str(e)}",
        )


@router.delete("/projects/{project_id}/schedule", response_model=ResearchProjectResponse)
async def remove_schedule(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> ResearchProjectResponse:
    """
    Remove scheduling from a project (set to manual).
    """
    try:
        service = get_research_project_service()

        # Set to manual
        from app.schemas.research_project import ResearchProjectUpdate
        updates = ResearchProjectUpdate(schedule_type="manual")

        project = await service.update_project(db, project_id, updates)

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found",
            )

        # Unschedule
        scheduler = get_research_scheduler()
        await scheduler.unschedule_project(project_id)

        return ResearchProjectResponse.model_validate(project)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove schedule for project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove schedule: {str(e)}",
        )


@router.post("/projects/{project_id}/run", response_model=RunProjectResponse)
async def run_project_now(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> RunProjectResponse:
    """
    Manually trigger a project run immediately.

    Generates new tasks (if auto_generate_tasks=true) or runs queued tasks,
    limited by max_tasks_per_run.
    """
    try:
        scheduler = get_research_scheduler()
        task_ids = await scheduler.run_project_now(db, project_id)

        return RunProjectResponse(
            project_id=project_id,
            task_ids=task_ids,
            message=f"Started {len(task_ids)} research tasks",
        )

    except Exception as e:
        logger.error(f"Failed to run project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to run project: {str(e)}",
        )


@router.post("/projects/{project_id}/pause", response_model=ResearchProjectResponse)
async def pause_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> ResearchProjectResponse:
    """
    Pause a project (stops scheduled runs).
    """
    try:
        service = get_research_project_service()

        # Update status to paused
        from app.schemas.research_project import ResearchProjectUpdate
        updates = ResearchProjectUpdate(status="paused")

        project = await service.update_project(db, project_id, updates)

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found",
            )

        # Unschedule
        scheduler = get_research_scheduler()
        await scheduler.unschedule_project(project_id)

        return ResearchProjectResponse.model_validate(project)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to pause project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to pause project: {str(e)}",
        )


@router.post("/projects/{project_id}/resume", response_model=ResearchProjectResponse)
async def resume_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> ResearchProjectResponse:
    """
    Resume a paused project (restarts scheduled runs).
    """
    try:
        service = get_research_project_service()

        # Update status to active
        from app.schemas.research_project import ResearchProjectUpdate
        updates = ResearchProjectUpdate(status="active")

        project = await service.update_project(db, project_id, updates)

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found",
            )

        # Reschedule if not manual
        if project.schedule_type != "manual":
            scheduler = get_research_scheduler()
            await scheduler.schedule_project(db, project_id)

        return ResearchProjectResponse.model_validate(project)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to resume project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resume project: {str(e)}",
        )
