"""
Unit tests for Research Project Service.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.services.research_project_service import ResearchProjectService
from app.models.research_project import ResearchProject
from app.models.research_task import ResearchTask
from app.schemas.research_project import (
    ResearchProjectCreate,
    ResearchProjectUpdate,
)


@pytest.fixture
def service():
    """Create a Research Project Service instance."""
    return ResearchProjectService()


@pytest.fixture
def sample_project_data():
    """Sample project creation data."""
    return ResearchProjectCreate(
        name="Test Project",
        description="Test description",
        goal="Test research goal for climate change",
        schedule_type="daily",
        schedule_cron=None,
        auto_generate_tasks=True,
        max_tasks_per_run=5,
        default_max_sources=10,
        default_depth="thorough",
        default_source_types=None,
    )


@pytest.fixture
def sample_project():
    """Sample project instance."""
    return ResearchProject(
        id="test-project-id",
        name="Test Project",
        description="Test description",
        goal="Test research goal",
        status="active",
        schedule_type="daily",
        auto_generate_tasks=True,
        max_tasks_per_run=5,
        default_max_sources=10,
        default_depth="thorough",
        total_tasks=0,
        completed_tasks=0,
        failed_tasks=0,
        total_sources_added=0,
    )


class TestCreateProject:
    """Tests for create_project method."""

    @pytest.mark.asyncio
    async def test_create_project_success(self, service, sample_project_data):
        """Test successful project creation."""
        # Mock database
        mock_db = AsyncMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        # Create project
        project = await service.create_project(mock_db, sample_project_data)

        # Assertions
        assert project.name == sample_project_data.name
        assert project.goal == sample_project_data.goal
        assert project.status == "active"
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_project_with_custom_schedule(self, service):
        """Test project creation with custom cron schedule."""
        mock_db = AsyncMock()
        project_data = ResearchProjectCreate(
            name="Custom Schedule Project",
            goal="Test goal",
            schedule_type="custom",
            schedule_cron="0 3 * * *",  # 3 AM daily
            auto_generate_tasks=True,
            max_tasks_per_run=5,
            default_max_sources=10,
            default_depth="thorough",
        )

        project = await service.create_project(mock_db, project_data)

        assert project.schedule_type == "custom"
        assert project.schedule_cron == "0 3 * * *"


class TestGetProject:
    """Tests for get_project method."""

    @pytest.mark.asyncio
    async def test_get_project_found(self, service, sample_project):
        """Test getting an existing project."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_project
        mock_db.execute = AsyncMock(return_value=mock_result)

        project = await service.get_project(mock_db, "test-project-id")

        assert project == sample_project
        assert project.id == "test-project-id"

    @pytest.mark.asyncio
    async def test_get_project_not_found(self, service):
        """Test getting a non-existent project."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        project = await service.get_project(mock_db, "nonexistent-id")

        assert project is None


class TestListProjects:
    """Tests for list_projects method."""

    @pytest.mark.asyncio
    async def test_list_projects_no_filter(self, service, sample_project):
        """Test listing all projects without filters."""
        mock_db = AsyncMock()

        # Mock count query
        mock_count_result = MagicMock()
        mock_count_result.scalar_one.return_value = 1

        # Mock projects query
        mock_projects_result = MagicMock()
        mock_projects_result.scalars.return_value.all.return_value = [sample_project]

        mock_db.execute = AsyncMock(side_effect=[mock_count_result, mock_projects_result])

        projects, total = await service.list_projects(mock_db, limit=20, offset=0)

        assert total == 1
        assert len(projects) == 1
        assert projects[0].id == sample_project.id

    @pytest.mark.asyncio
    async def test_list_projects_with_status_filter(self, service, sample_project):
        """Test listing projects with status filter."""
        mock_db = AsyncMock()
        mock_count_result = MagicMock()
        mock_count_result.scalar_one.return_value = 1
        mock_projects_result = MagicMock()
        mock_projects_result.scalars.return_value.all.return_value = [sample_project]
        mock_db.execute = AsyncMock(side_effect=[mock_count_result, mock_projects_result])

        projects, total = await service.list_projects(mock_db, status="active")

        assert total == 1
        assert len(projects) == 1

    @pytest.mark.asyncio
    async def test_list_projects_pagination(self, service):
        """Test project list pagination."""
        mock_db = AsyncMock()
        mock_count_result = MagicMock()
        mock_count_result.scalar_one.return_value = 100
        mock_projects_result = MagicMock()
        mock_projects_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(side_effect=[mock_count_result, mock_projects_result])

        projects, total = await service.list_projects(mock_db, limit=10, offset=20)

        assert total == 100
        assert len(projects) == 0


class TestUpdateProject:
    """Tests for update_project method."""

    @pytest.mark.asyncio
    async def test_update_project_success(self, service, sample_project):
        """Test successful project update."""
        mock_db = AsyncMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        # Mock get_project
        with patch.object(service, 'get_project', return_value=sample_project):
            updates = ResearchProjectUpdate(
                name="Updated Name",
                status="paused",
            )

            updated_project = await service.update_project(mock_db, "test-project-id", updates)

            assert updated_project.name == "Updated Name"
            assert updated_project.status == "paused"
            mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_project_not_found(self, service):
        """Test updating a non-existent project."""
        mock_db = AsyncMock()

        with patch.object(service, 'get_project', return_value=None):
            updates = ResearchProjectUpdate(name="Updated Name")
            result = await service.update_project(mock_db, "nonexistent-id", updates)

            assert result is None


class TestDeleteProject:
    """Tests for delete_project method."""

    @pytest.mark.asyncio
    async def test_delete_project_success(self, service, sample_project):
        """Test successful project deletion."""
        mock_db = AsyncMock()
        mock_db.delete = AsyncMock()
        mock_db.commit = AsyncMock()

        with patch.object(service, 'get_project', return_value=sample_project):
            result = await service.delete_project(mock_db, "test-project-id")

            assert result is True
            mock_db.delete.assert_called_once_with(sample_project)
            mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_project_not_found(self, service):
        """Test deleting a non-existent project."""
        mock_db = AsyncMock()

        with patch.object(service, 'get_project', return_value=None):
            result = await service.delete_project(mock_db, "nonexistent-id")

            assert result is False
            mock_db.delete.assert_not_called()


class TestGenerateTaskQueries:
    """Tests for generate_task_queries method."""

    @pytest.mark.asyncio
    async def test_generate_queries_success(self, service, sample_project):
        """Test successful task query generation."""
        mock_db = AsyncMock()

        # Mock get_project
        with patch.object(service, 'get_project', return_value=sample_project):
            # Mock existing queries
            mock_result = MagicMock()
            mock_result.all.return_value = [("existing query 1",), ("existing query 2",)]
            mock_db.execute = AsyncMock(return_value=mock_result)

            # Mock LLM response
            mock_llm_response = """1. What are the main causes of climate change?
2. How effective are renewable energy sources?
3. What role does policy play in emission reduction?
4. How can individuals reduce their carbon footprint?
5. What are the economic impacts of climate action?"""

            service.llm_service.generate_completion = AsyncMock(return_value=mock_llm_response)

            queries = await service.generate_task_queries(mock_db, "test-project-id", count=5)

            assert len(queries) == 5
            assert "What are the main causes of climate change?" in queries
            assert "How effective are renewable energy sources?" in queries
            service.llm_service.generate_completion.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_queries_llm_failure_fallback(self, service, sample_project):
        """Test fallback when LLM fails."""
        mock_db = AsyncMock()

        with patch.object(service, 'get_project', return_value=sample_project):
            mock_result = MagicMock()
            mock_result.all.return_value = []
            mock_db.execute = AsyncMock(return_value=mock_result)

            # Mock LLM failure
            service.llm_service.generate_completion = AsyncMock(side_effect=Exception("LLM error"))

            queries = await service.generate_task_queries(mock_db, "test-project-id", count=3)

            # Should get fallback queries
            assert len(queries) > 0
            assert len(queries) <= 3

    @pytest.mark.asyncio
    async def test_generate_queries_project_not_found(self, service):
        """Test query generation for non-existent project."""
        mock_db = AsyncMock()

        with patch.object(service, 'get_project', return_value=None):
            with pytest.raises(ValueError, match="not found"):
                await service.generate_task_queries(mock_db, "nonexistent-id")

    @pytest.mark.asyncio
    async def test_generate_queries_considers_existing(self, service, sample_project):
        """Test that generation considers existing queries."""
        mock_db = AsyncMock()

        with patch.object(service, 'get_project', return_value=sample_project):
            # Mock existing queries
            existing_queries = [
                ("What are the causes of climate change?",),
                ("How do carbon taxes work?",),
            ]
            mock_result = MagicMock()
            mock_result.all.return_value = existing_queries
            mock_db.execute = AsyncMock(return_value=mock_result)

            mock_llm_response = "1. New query 1\n2. New query 2"
            service.llm_service.generate_completion = AsyncMock(return_value=mock_llm_response)

            queries = await service.generate_task_queries(
                mock_db, "test-project-id", count=2, consider_existing=True
            )

            # Check that LLM prompt includes existing queries
            call_args = service.llm_service.generate_completion.call_args
            prompt = call_args.kwargs['prompt']
            assert "already been researched" in prompt


class TestCreateTasksFromQueries:
    """Tests for create_tasks_from_queries method."""

    @pytest.mark.asyncio
    async def test_create_tasks_success(self, service, sample_project):
        """Test successful task creation from queries."""
        mock_db = AsyncMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        queries = [
            "Query 1",
            "Query 2",
            "Query 3",
        ]

        with patch.object(service, 'get_project', return_value=sample_project):
            with patch.object(service, 'update_project_stats', return_value=None):
                tasks = await service.create_tasks_from_queries(mock_db, "test-project-id", queries)

                assert len(tasks) == 3
                assert tasks[0].query == "Query 1"
                assert tasks[0].auto_generated is True
                assert tasks[0].status == "queued"
                assert mock_db.add.call_count == 3
                mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tasks_inherits_project_defaults(self, service, sample_project):
        """Test that tasks inherit project default settings."""
        mock_db = AsyncMock()

        queries = ["Test query"]

        with patch.object(service, 'get_project', return_value=sample_project):
            with patch.object(service, 'update_project_stats', return_value=None):
                tasks = await service.create_tasks_from_queries(mock_db, "test-project-id", queries)

                assert tasks[0].max_sources == sample_project.default_max_sources
                assert tasks[0].depth == sample_project.default_depth
                assert tasks[0].source_types == sample_project.default_source_types

    @pytest.mark.asyncio
    async def test_create_tasks_project_not_found(self, service):
        """Test task creation for non-existent project."""
        mock_db = AsyncMock()

        with patch.object(service, 'get_project', return_value=None):
            with pytest.raises(ValueError, match="not found"):
                await service.create_tasks_from_queries(mock_db, "nonexistent-id", ["Query"])


class TestGetProjectProgress:
    """Tests for get_project_progress method."""

    @pytest.mark.asyncio
    async def test_get_progress_success(self, service, sample_project):
        """Test getting project progress."""
        mock_db = AsyncMock()

        # Mock get_project
        with patch.object(service, 'get_project', return_value=sample_project):
            # Mock status counts
            mock_status_result = MagicMock()
            mock_status_result.all.return_value = [
                ("completed", 5),
                ("running", 2),
                ("queued", 3),
            ]

            # Mock recent tasks
            mock_tasks_result = MagicMock()
            mock_task = MagicMock()
            mock_task.id = "task-1"
            mock_task.query = "Test query"
            mock_task.status = "completed"
            mock_task.sources_added = 10
            mock_task.created_at = datetime.utcnow()
            mock_task.completed_at = datetime.utcnow()
            mock_tasks_result.scalars.return_value.all.return_value = [mock_task]

            # Mock sources stats
            mock_sources_added = MagicMock()
            mock_sources_added.scalar_one.return_value = 50
            mock_sources_failed = MagicMock()
            mock_sources_failed.scalar_one.return_value = 5

            mock_db.execute = AsyncMock(side_effect=[
                mock_status_result,
                mock_tasks_result,
                mock_sources_added,
                mock_sources_failed,
            ])

            progress = await service.get_project_progress(mock_db, "test-project-id")

            assert progress.project_id == str(sample_project.id)
            assert progress.completed_tasks == 5
            assert progress.running_tasks == 2
            assert progress.queued_tasks == 3
            assert progress.total_sources_added == 50
            assert progress.total_sources_failed == 5
            assert len(progress.recent_tasks) == 1

    @pytest.mark.asyncio
    async def test_get_progress_project_not_found(self, service):
        """Test progress for non-existent project."""
        mock_db = AsyncMock()

        with patch.object(service, 'get_project', return_value=None):
            progress = await service.get_project_progress(mock_db, "nonexistent-id")

            assert progress is None


class TestUpdateProjectStats:
    """Tests for update_project_stats method."""

    @pytest.mark.asyncio
    async def test_update_stats_success(self, service, sample_project):
        """Test updating project statistics."""
        mock_db = AsyncMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        with patch.object(service, 'get_project', return_value=sample_project):
            # Mock count queries
            mock_total = MagicMock()
            mock_total.scalar_one.return_value = 10
            mock_completed = MagicMock()
            mock_completed.scalar_one.return_value = 7
            mock_failed = MagicMock()
            mock_failed.scalar_one.return_value = 1
            mock_sources = MagicMock()
            mock_sources.scalar_one.return_value = 70

            mock_db.execute = AsyncMock(side_effect=[
                mock_total,
                mock_completed,
                mock_failed,
                mock_sources,
            ])

            await service.update_project_stats(mock_db, "test-project-id")

            assert sample_project.total_tasks == 10
            assert sample_project.completed_tasks == 7
            assert sample_project.failed_tasks == 1
            assert sample_project.total_sources_added == 70
            mock_db.commit.assert_called_once()


class TestParseTaskQueries:
    """Tests for _parse_task_queries method."""

    def test_parse_numbered_list(self, service):
        """Test parsing numbered list format."""
        llm_response = """1. First query
2. Second query
3. Third query"""

        queries = service._parse_task_queries(llm_response)

        assert len(queries) == 3
        assert queries[0] == "First query"
        assert queries[1] == "Second query"
        assert queries[2] == "Third query"

    def test_parse_with_parentheses(self, service):
        """Test parsing with parentheses numbering."""
        llm_response = """1) First query
2) Second query"""

        queries = service._parse_task_queries(llm_response)

        assert len(queries) == 2

    def test_parse_with_dashes(self, service):
        """Test parsing with dash numbering."""
        llm_response = """1 - First query
2 - Second query"""

        queries = service._parse_task_queries(llm_response)

        assert len(queries) == 2

    def test_parse_ignores_empty_lines(self, service):
        """Test that empty lines are ignored."""
        llm_response = """1. First query

2. Second query

"""

        queries = service._parse_task_queries(llm_response)

        assert len(queries) == 2
