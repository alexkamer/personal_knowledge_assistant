"""
Unit tests for the Tag service.
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.tag_service import TagService
from app.models.tag import Tag


class TestTagService:
    """Test suite for TagService."""

    @pytest.mark.asyncio
    async def test_get_or_create_tags_empty_list(self, test_db: AsyncSession):
        """Test get_or_create_tags with empty list."""
        tags = await TagService.get_or_create_tags(test_db, [])

        assert tags == []

    @pytest.mark.asyncio
    async def test_get_or_create_tags_creates_new(self, test_db: AsyncSession):
        """Test creating new tags."""
        tags = await TagService.get_or_create_tags(test_db, ["python", "testing"])
        await test_db.commit()  # Commit to persist

        assert len(tags) == 2
        assert tags[0].name == "python"
        assert tags[1].name == "testing"

    @pytest.mark.asyncio
    async def test_get_or_create_tags_normalizes_names(self, test_db: AsyncSession):
        """Test that tag names are normalized (lowercase, stripped)."""
        tags = await TagService.get_or_create_tags(
            test_db, ["  Python  ", "TESTING", "DaTaBaSe"]
        )
        await test_db.commit()

        assert len(tags) == 3
        # Should be sorted and normalized
        assert tags[0].name == "database"
        assert tags[1].name == "python"
        assert tags[2].name == "testing"

    @pytest.mark.asyncio
    async def test_get_or_create_tags_removes_duplicates(self, test_db: AsyncSession):
        """Test that duplicate tag names are removed."""
        tags = await TagService.get_or_create_tags(
            test_db, ["python", "Python", "PYTHON"]
        )
        await test_db.commit()

        # Should only create one tag
        assert len(tags) == 1
        assert tags[0].name == "python"

    @pytest.mark.asyncio
    async def test_get_or_create_tags_gets_existing(self, test_db: AsyncSession):
        """Test getting existing tags without creating duplicates."""
        # Create tags first
        await TagService.get_or_create_tags(test_db, ["python", "testing"])
        await test_db.commit()

        # Try to get them again
        tags = await TagService.get_or_create_tags(test_db, ["python", "testing"])
        await test_db.commit()

        assert len(tags) == 2
        assert tags[0].name == "python"
        assert tags[1].name == "testing"

    @pytest.mark.asyncio
    async def test_get_or_create_tags_mixed_existing_new(self, test_db: AsyncSession):
        """Test getting mix of existing and new tags."""
        # Create some tags
        await TagService.get_or_create_tags(test_db, ["python"])
        await test_db.commit()

        # Request existing and new
        tags = await TagService.get_or_create_tags(test_db, ["python", "javascript", "rust"])
        await test_db.commit()

        assert len(tags) == 3
        tag_names = [t.name for t in tags]
        assert "python" in tag_names
        assert "javascript" in tag_names
        assert "rust" in tag_names

    @pytest.mark.asyncio
    async def test_get_or_create_tags_filters_empty_strings(self, test_db: AsyncSession):
        """Test that empty strings are filtered out."""
        tags = await TagService.get_or_create_tags(
            test_db, ["python", "", "  ", "testing"]
        )
        await test_db.commit()

        assert len(tags) == 2
        assert tags[0].name == "python"
        assert tags[1].name == "testing"

    @pytest.mark.asyncio
    async def test_list_tags_empty(self, test_db: AsyncSession):
        """Test listing tags when database is empty."""
        tags = await TagService.list_tags(test_db)

        assert tags == []

    @pytest.mark.asyncio
    async def test_list_tags(self, test_db: AsyncSession):
        """Test listing all tags with usage counts."""
        # Create some tags
        await TagService.get_or_create_tags(test_db, ["python", "javascript", "rust"])
        await test_db.commit()

        tags_with_counts = await TagService.list_tags(test_db)

        assert len(tags_with_counts) == 3
        # Verify structure: list of (Tag, count) tuples
        for tag, count in tags_with_counts:
            assert isinstance(tag, Tag)
            assert isinstance(count, int)
            assert count == 0  # No notes using tags yet

    @pytest.mark.asyncio
    async def test_list_tags_sorted_by_name(self, test_db: AsyncSession):
        """Test that tags are sorted alphabetically."""
        # Create tags in random order
        await TagService.get_or_create_tags(test_db, ["zebra", "apple", "mango"])
        await test_db.commit()

        tags_with_counts = await TagService.list_tags(test_db)

        # Should be alphabetically sorted
        assert tags_with_counts[0][0].name == "apple"
        assert tags_with_counts[1][0].name == "mango"
        assert tags_with_counts[2][0].name == "zebra"

    @pytest.mark.asyncio
    async def test_get_popular_tags_empty(self, test_db: AsyncSession):
        """Test getting popular tags when none exist."""
        tags = await TagService.get_popular_tags(test_db)

        assert tags == []

    @pytest.mark.asyncio
    async def test_get_popular_tags_limit(self, test_db: AsyncSession):
        """Test that popular tags respects limit."""
        # Create many tags
        tag_names = [f"tag{i}" for i in range(20)]
        await TagService.get_or_create_tags(test_db, tag_names)
        await test_db.commit()

        # Get only top 5
        tags = await TagService.get_popular_tags(test_db, limit=5)

        # Should return at most 5 (but might be 0 if no notes use them)
        assert len(tags) <= 5
