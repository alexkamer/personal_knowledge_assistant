"""
Research scheduler service for managing scheduled research tasks.

Uses APScheduler to run research projects on a schedule (daily, weekly, monthly, custom cron).
"""
import logging
from typing import Optional, List
from datetime import datetime, time as dt_time

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.research_project import ResearchProject
from app.models.research_task import ResearchTask

logger = logging.getLogger(__name__)


class ResearchSchedulerService:
    """
    Service for scheduling and executing research projects.

    Uses APScheduler to run projects on a schedule.
    """

    def __init__(self):
        """Initialize the scheduler service."""
        # Configure job stores and executors
        jobstores = {
            'default': MemoryJobStore()
        }
        executors = {
            'default': AsyncIOExecutor()
        }
        job_defaults = {
            'coalesce': False,  # Don't combine multiple missed runs
            'max_instances': 1,  # Only one instance of each job at a time
            'misfire_grace_time': 3600,  # 1 hour grace period for missed jobs
        }

        self.scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone='UTC',
        )
        self._started = False

    async def start(self) -> None:
        """Start the scheduler."""
        if not self._started:
            self.scheduler.start()
            self._started = True
            logger.info("Research scheduler started")

            # Load all active scheduled projects
            await self._load_active_projects()

    async def shutdown(self) -> None:
        """Shutdown the scheduler gracefully."""
        if self._started:
            self.scheduler.shutdown(wait=True)
            self._started = False
            logger.info("Research scheduler shutdown")

    async def _load_active_projects(self) -> None:
        """
        Load all active scheduled projects and register them with the scheduler.

        Called on startup to restore scheduled jobs.
        """
        from app.core.database import AsyncSessionLocal

        async with AsyncSessionLocal() as db:
            # Get all active projects with non-manual schedules
            result = await db.execute(
                select(ResearchProject).where(
                    ResearchProject.status == "active",
                    ResearchProject.schedule_type != "manual"
                )
            )
            projects = result.scalars().all()

            for project in projects:
                try:
                    await self.schedule_project(db, str(project.id))
                    logger.info(f"Loaded scheduled project: {project.name}")
                except Exception as e:
                    logger.error(f"Failed to load project {project.id}: {e}")

    async def schedule_project(
        self, db: AsyncSession, project_id: str
    ) -> str:
        """
        Schedule a research project based on its schedule settings.

        Args:
            db: Database session
            project_id: Project UUID

        Returns:
            Job ID from scheduler

        Raises:
            ValueError: If project not found or has manual schedule
        """
        # Get project
        result = await db.execute(
            select(ResearchProject).where(ResearchProject.id == project_id)
        )
        project = result.scalar_one_or_none()

        if not project:
            raise ValueError(f"Project {project_id} not found")

        if project.schedule_type == "manual":
            raise ValueError("Cannot schedule project with manual schedule type")

        # Remove existing job if any
        job_id = f"project_{project_id}"
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)

        # Create cron trigger based on schedule type
        trigger = self._create_trigger(project)

        # Schedule the job
        self.scheduler.add_job(
            self._execute_project_run,
            trigger=trigger,
            args=[project_id],
            id=job_id,
            name=f"Research: {project.name}",
            replace_existing=True,
        )

        # Update next_run_at in database
        job = self.scheduler.get_job(job_id)
        if job and job.next_run_time:
            project.next_run_at = job.next_run_time
            await db.commit()

        logger.info(f"Scheduled project {project_id} with trigger: {trigger}")

        return job_id

    def _create_trigger(self, project: ResearchProject) -> CronTrigger:
        """
        Create a cron trigger based on project schedule settings.

        Args:
            project: Research project

        Returns:
            CronTrigger instance
        """
        schedule_type = project.schedule_type

        if schedule_type == "daily":
            # Daily at 2:00 AM UTC
            return CronTrigger(hour=2, minute=0)

        elif schedule_type == "weekly":
            # Weekly on Sunday at 2:00 AM UTC
            return CronTrigger(day_of_week='sun', hour=2, minute=0)

        elif schedule_type == "monthly":
            # Monthly on the 1st at 2:00 AM UTC
            return CronTrigger(day=1, hour=2, minute=0)

        elif schedule_type == "custom":
            if not project.schedule_cron:
                raise ValueError("Custom schedule requires schedule_cron to be set")

            # Parse custom cron expression
            # Format: minute hour day month day_of_week
            # Example: "0 2 * * *" = daily at 2:00 AM
            return CronTrigger.from_crontab(project.schedule_cron)

        else:
            raise ValueError(f"Invalid schedule type: {schedule_type}")

    async def unschedule_project(self, project_id: str) -> None:
        """
        Remove a project from the scheduler.

        Args:
            project_id: Project UUID
        """
        job_id = f"project_{project_id}"

        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
            logger.info(f"Unscheduled project {project_id}")

            # Update next_run_at to None
            from app.core.database import AsyncSessionLocal
            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    select(ResearchProject).where(ResearchProject.id == project_id)
                )
                project = result.scalar_one_or_none()

                if project:
                    project.next_run_at = None
                    await db.commit()

    async def reschedule_project(
        self, db: AsyncSession, project_id: str
    ) -> str:
        """
        Reschedule a project (useful after schedule settings change).

        Args:
            db: Database session
            project_id: Project UUID

        Returns:
            Job ID from scheduler
        """
        # Unschedule first
        await self.unschedule_project(project_id)

        # Schedule again with new settings
        return await self.schedule_project(db, project_id)

    async def run_project_now(
        self, db: AsyncSession, project_id: str
    ) -> List[str]:
        """
        Manually trigger a project run immediately.

        Args:
            db: Database session
            project_id: Project UUID

        Returns:
            List of task IDs that were created/started
        """
        logger.info(f"Manual run triggered for project {project_id}")

        # Execute the project run
        task_ids = await self._execute_project_run(project_id)

        return task_ids

    async def _execute_project_run(self, project_id: str) -> List[str]:
        """
        Execute a scheduled project run.

        This is called by the scheduler at the scheduled time, or manually.

        Args:
            project_id: Project UUID

        Returns:
            List of task IDs that were executed
        """
        from app.core.database import AsyncSessionLocal
        from app.services.research_project_service import get_research_project_service
        from app.api.v1.endpoints.research import run_research_task

        async with AsyncSessionLocal() as db:
            try:
                logger.info(f"Executing scheduled run for project {project_id}")

                # Get project
                result = await db.execute(
                    select(ResearchProject).where(ResearchProject.id == project_id)
                )
                project = result.scalar_one_or_none()

                if not project:
                    logger.error(f"Project {project_id} not found")
                    return []

                # Update last_run_at
                project.last_run_at = datetime.utcnow()
                await db.commit()

                # Get or generate tasks
                task_ids = []

                if project.auto_generate_tasks:
                    # Generate new tasks
                    project_service = get_research_project_service()
                    queries = await project_service.generate_task_queries(
                        db, project_id, count=project.max_tasks_per_run
                    )

                    if queries:
                        tasks = await project_service.create_tasks_from_queries(
                            db, project_id, queries
                        )
                        task_ids = [str(task.id) for task in tasks]
                else:
                    # Get queued tasks
                    queued_tasks_query = (
                        select(ResearchTask)
                        .where(
                            ResearchTask.project_id == project_id,
                            ResearchTask.status == "queued"
                        )
                        .limit(project.max_tasks_per_run)
                    )

                    result = await db.execute(queued_tasks_query)
                    queued_tasks = result.scalars().all()
                    task_ids = [str(task.id) for task in queued_tasks]

                # Execute tasks in background
                for task_id in task_ids:
                    # Get task details
                    task_result = await db.execute(
                        select(ResearchTask).where(ResearchTask.id == task_id)
                    )
                    task = task_result.scalar_one_or_none()

                    if task:
                        # Run task in background (non-blocking)
                        # Note: In production, consider using a proper task queue (Celery, RQ)
                        import asyncio
                        asyncio.create_task(
                            run_research_task(
                                task_id=task_id,
                                query=task.query,
                                max_sources=task.max_sources,
                                depth=task.depth,
                                source_types=task.source_types,
                            )
                        )

                logger.info(
                    f"Scheduled run complete for project {project_id}: {len(task_ids)} tasks started"
                )

                return task_ids

            except Exception as e:
                logger.error(f"Failed to execute project run {project_id}: {e}")
                return []

    def get_scheduled_projects(self) -> List[dict]:
        """
        Get list of all scheduled projects with their next run times.

        Returns:
            List of dicts with project_id and next_run_time
        """
        jobs = self.scheduler.get_jobs()

        scheduled = []
        for job in jobs:
            # Extract project_id from job id (format: "project_{uuid}")
            if job.id.startswith("project_"):
                project_id = job.id.replace("project_", "")
                scheduled.append({
                    "project_id": project_id,
                    "next_run_time": job.next_run_time,
                    "job_name": job.name,
                })

        return scheduled


# Global instance
_research_scheduler: Optional[ResearchSchedulerService] = None


def get_research_scheduler() -> ResearchSchedulerService:
    """
    Get the global research scheduler service instance.

    Returns:
        Research scheduler service singleton
    """
    global _research_scheduler
    if _research_scheduler is None:
        _research_scheduler = ResearchSchedulerService()
    return _research_scheduler
