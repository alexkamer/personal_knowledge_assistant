"""
Research project service for managing research projects and task generation.
"""
import logging
from typing import List, Optional, Dict
from datetime import datetime

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.research_project import ResearchProject
from app.models.research_task import ResearchTask
from app.schemas.research_project import (
    ResearchProjectCreate,
    ResearchProjectUpdate,
    ResearchProjectProgress,
    TaskSummary,
)
from app.services.llm_service import get_llm_service

logger = logging.getLogger(__name__)


class ResearchProjectService:
    """Service for managing research projects."""

    def __init__(self):
        """Initialize research project service."""
        self.llm_service = get_llm_service()

    async def create_project(
        self, db: AsyncSession, project_data: ResearchProjectCreate
    ) -> ResearchProject:
        """
        Create a new research project.

        Args:
            db: Database session
            project_data: Project creation data

        Returns:
            Created research project
        """
        project = ResearchProject(
            name=project_data.name,
            description=project_data.description,
            goal=project_data.goal,
            status="active",
            schedule_type=project_data.schedule_type,
            schedule_cron=project_data.schedule_cron,
            auto_generate_tasks=project_data.auto_generate_tasks,
            max_tasks_per_run=project_data.max_tasks_per_run,
            default_max_sources=project_data.default_max_sources,
            default_depth=project_data.default_depth,
            default_source_types=project_data.default_source_types,
        )

        db.add(project)
        await db.commit()
        await db.refresh(project)

        logger.info(f"Created research project {project.id}: {project.name}")

        return project

    async def get_project(
        self, db: AsyncSession, project_id: str
    ) -> Optional[ResearchProject]:
        """
        Get a research project by ID.

        Args:
            db: Database session
            project_id: Project UUID

        Returns:
            Research project or None if not found
        """
        result = await db.execute(
            select(ResearchProject).where(ResearchProject.id == project_id)
        )
        return result.scalar_one_or_none()

    async def list_projects(
        self,
        db: AsyncSession,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[List[ResearchProject], int]:
        """
        List research projects with pagination and filtering.

        Args:
            db: Database session
            status: Optional status filter (active, paused, completed, archived)
            limit: Max results to return
            offset: Number of results to skip

        Returns:
            Tuple of (projects list, total count)
        """
        # Build query
        query = select(ResearchProject)

        if status:
            query = query.where(ResearchProject.status == status)

        # Get total count
        count_query = select(func.count()).select_from(ResearchProject)
        if status:
            count_query = count_query.where(ResearchProject.status == status)

        total_result = await db.execute(count_query)
        total = total_result.scalar_one()

        # Get paginated projects
        query = (
            query.order_by(desc(ResearchProject.created_at)).offset(offset).limit(limit)
        )
        result = await db.execute(query)
        projects = result.scalars().all()

        return list(projects), total

    async def update_project(
        self,
        db: AsyncSession,
        project_id: str,
        updates: ResearchProjectUpdate,
    ) -> Optional[ResearchProject]:
        """
        Update a research project.

        Args:
            db: Database session
            project_id: Project UUID
            updates: Fields to update

        Returns:
            Updated project or None if not found
        """
        project = await self.get_project(db, project_id)
        if not project:
            return None

        # Update fields that were provided
        update_data = updates.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(project, field):
                setattr(project, field, value)

        await db.commit()
        await db.refresh(project)

        logger.info(f"Updated research project {project_id}")

        return project

    async def delete_project(
        self, db: AsyncSession, project_id: str, delete_tasks: bool = False
    ) -> bool:
        """
        Delete a research project.

        Args:
            db: Database session
            project_id: Project UUID
            delete_tasks: If True, cascade delete all related tasks

        Returns:
            True if deleted, False if not found
        """
        project = await self.get_project(db, project_id)
        if not project:
            return False

        # Tasks will cascade delete automatically due to foreign key
        await db.delete(project)
        await db.commit()

        logger.info(f"Deleted research project {project_id}")

        return True

    async def get_project_progress(
        self, db: AsyncSession, project_id: str
    ) -> Optional[ResearchProjectProgress]:
        """
        Get detailed progress information for a project.

        Args:
            db: Database session
            project_id: Project UUID

        Returns:
            Project progress summary or None if project not found
        """
        project = await self.get_project(db, project_id)
        if not project:
            return None

        # Get task counts by status
        status_counts_query = select(
            ResearchTask.status, func.count(ResearchTask.id)
        ).where(ResearchTask.project_id == project_id).group_by(ResearchTask.status)

        result = await db.execute(status_counts_query)
        status_counts = dict(result.all())

        # Get recent tasks
        recent_tasks_query = (
            select(ResearchTask)
            .where(ResearchTask.project_id == project_id)
            .order_by(desc(ResearchTask.created_at))
            .limit(10)
        )

        result = await db.execute(recent_tasks_query)
        recent_tasks = result.scalars().all()

        # Calculate source stats
        sources_added_query = select(
            func.sum(ResearchTask.sources_added)
        ).where(ResearchTask.project_id == project_id)
        sources_failed_query = select(
            func.sum(ResearchTask.sources_failed)
        ).where(ResearchTask.project_id == project_id)

        sources_added_result = await db.execute(sources_added_query)
        sources_failed_result = await db.execute(sources_failed_query)

        sources_added = sources_added_result.scalar_one() or 0
        sources_failed = sources_failed_result.scalar_one() or 0

        return ResearchProjectProgress(
            project_id=str(project.id),
            name=project.name,
            status=project.status,
            total_tasks=project.total_tasks,
            completed_tasks=status_counts.get("completed", 0),
            running_tasks=status_counts.get("running", 0),
            failed_tasks=status_counts.get("failed", 0),
            queued_tasks=status_counts.get("queued", 0),
            total_sources_added=sources_added,
            total_sources_failed=sources_failed,
            last_run_at=project.last_run_at,
            next_run_at=project.next_run_at,
            recent_tasks=[
                TaskSummary(
                    id=str(task.id),
                    query=task.query,
                    status=task.status,
                    sources_added=task.sources_added,
                    created_at=task.created_at,
                    completed_at=task.completed_at,
                )
                for task in recent_tasks
            ],
        )

    async def update_project_stats(
        self, db: AsyncSession, project_id: str
    ) -> None:
        """
        Recalculate and update project statistics from tasks.

        Args:
            db: Database session
            project_id: Project UUID
        """
        project = await self.get_project(db, project_id)
        if not project:
            return

        # Count tasks by status
        total_tasks_query = select(func.count(ResearchTask.id)).where(
            ResearchTask.project_id == project_id
        )
        completed_tasks_query = select(func.count(ResearchTask.id)).where(
            ResearchTask.project_id == project_id,
            ResearchTask.status == "completed"
        )
        failed_tasks_query = select(func.count(ResearchTask.id)).where(
            ResearchTask.project_id == project_id,
            ResearchTask.status == "failed"
        )

        # Calculate total sources added
        sources_query = select(
            func.sum(ResearchTask.sources_added)
        ).where(ResearchTask.project_id == project_id)

        total_tasks_result = await db.execute(total_tasks_query)
        completed_tasks_result = await db.execute(completed_tasks_query)
        failed_tasks_result = await db.execute(failed_tasks_query)
        sources_result = await db.execute(sources_query)

        project.total_tasks = total_tasks_result.scalar_one()
        project.completed_tasks = completed_tasks_result.scalar_one()
        project.failed_tasks = failed_tasks_result.scalar_one()
        project.total_sources_added = sources_result.scalar_one() or 0

        await db.commit()
        await db.refresh(project)

        logger.info(f"Updated stats for project {project_id}")

    async def generate_task_queries(
        self,
        db: AsyncSession,
        project_id: str,
        count: int = 5,
        consider_existing: bool = True,
    ) -> List[str]:
        """
        Generate research task queries using LLM based on project goal.

        Args:
            db: Database session
            project_id: Project UUID
            count: Number of queries to generate
            consider_existing: If True, avoid duplicating existing task queries

        Returns:
            List of generated research queries
        """
        project = await self.get_project(db, project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")

        # Get existing tasks to avoid duplicates
        existing_queries = []
        if consider_existing:
            existing_tasks_query = select(ResearchTask.query).where(
                ResearchTask.project_id == project_id
            )
            result = await db.execute(existing_tasks_query)
            existing_queries = [row[0] for row in result.all()]

        # Build LLM prompt
        prompt = self._build_task_generation_prompt(
            project_goal=project.goal,
            project_name=project.name,
            existing_queries=existing_queries,
            count=count,
        )

        # Generate queries using LLM
        try:
            response = await self.llm_service.generate_completion(
                prompt=prompt,
                temperature=0.7,  # Slightly creative
                max_tokens=500,
            )

            # Parse response - expect numbered list
            queries = self._parse_task_queries(response)

            # Limit to requested count
            queries = queries[:count]

            logger.info(
                f"Generated {len(queries)} task queries for project {project_id}"
            )

            return queries

        except Exception as e:
            logger.error(f"Failed to generate task queries: {e}")
            # Fallback: generate simple queries based on goal keywords
            return self._generate_fallback_queries(project.goal, count)

    def _build_task_generation_prompt(
        self,
        project_goal: str,
        project_name: str,
        existing_queries: List[str],
        count: int,
    ) -> str:
        """Build prompt for LLM to generate research task queries."""
        prompt = f"""You are a research assistant helping to break down a large research goal into specific, actionable research tasks.

Project: {project_name}
Research Goal: {project_goal}

Generate {count} specific research questions or topics that would help accomplish this research goal. Each question should be:
1. Specific and focused (not too broad)
2. Searchable on the web
3. Complementary to other questions (covering different aspects)
4. Clear and unambiguous

"""

        if existing_queries:
            prompt += f"""
These questions have already been researched - avoid duplicating them:
{chr(10).join(f"- {q}" for q in existing_queries[:10])}

"""

        prompt += f"""
Output Format:
Generate exactly {count} research questions, one per line, numbered 1-{count}.
Do not include any other text, explanations, or commentary.

Example output:
1. What are the current approaches to climate change mitigation in developing countries?
2. How effective are carbon pricing mechanisms in reducing emissions?
3. What role does renewable energy play in achieving net-zero goals?

Now generate {count} research questions for the project:"""

        return prompt

    def _parse_task_queries(self, llm_response: str) -> List[str]:
        """Parse numbered list of queries from LLM response."""
        queries = []
        lines = llm_response.strip().split("\n")

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Remove numbering (e.g., "1. ", "1) ", "1 - ")
            import re
            cleaned = re.sub(r"^\d+[\.\)\-]\s*", "", line)

            if cleaned:
                queries.append(cleaned)

        return queries

    def _generate_fallback_queries(self, goal: str, count: int) -> List[str]:
        """Generate simple fallback queries if LLM fails."""
        # Extract key words from goal
        import re
        words = re.findall(r'\b\w{4,}\b', goal.lower())
        unique_words = list(dict.fromkeys(words))[:5]  # Top 5 unique words

        queries = []
        for i, word in enumerate(unique_words[:count]):
            queries.append(f"Research overview of {word}")

        # If not enough words, add generic queries
        while len(queries) < count:
            queries.append(f"Background information on {goal[:50]}")

        return queries[:count]

    async def create_tasks_from_queries(
        self,
        db: AsyncSession,
        project_id: str,
        queries: List[str],
    ) -> List[ResearchTask]:
        """
        Create research tasks from a list of queries.

        Args:
            db: Database session
            project_id: Project UUID
            queries: List of research queries

        Returns:
            List of created research tasks
        """
        project = await self.get_project(db, project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")

        tasks = []
        for query in queries:
            task = ResearchTask(
                project_id=project_id,
                query=query,
                status="queued",
                auto_generated=True,
                max_sources=project.default_max_sources,
                depth=project.default_depth,
                source_types=project.default_source_types,
            )
            db.add(task)
            tasks.append(task)

        await db.commit()

        # Refresh all tasks to get IDs
        for task in tasks:
            await db.refresh(task)

        # Update project stats
        await self.update_project_stats(db, project_id)

        logger.info(f"Created {len(tasks)} tasks for project {project_id}")

        return tasks


# Global instance
_research_project_service: Optional[ResearchProjectService] = None


def get_research_project_service() -> ResearchProjectService:
    """
    Get the global research project service instance.

    Returns:
        Research project service singleton
    """
    global _research_project_service
    if _research_project_service is None:
        _research_project_service = ResearchProjectService()
    return _research_project_service
