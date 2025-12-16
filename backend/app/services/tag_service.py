"""
Service layer for tag operations.
"""
import logging
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tag import Tag
from app.models.note_tag import NoteTag

logger = logging.getLogger(__name__)


class TagService:
    """Service for managing tags."""

    @staticmethod
    async def get_or_create_tags(
        db: AsyncSession, tag_names: list[str]
    ) -> list[Tag]:
        """
        Get existing tags or create new ones for given tag names.

        Args:
            db: Database session
            tag_names: List of tag names

        Returns:
            List of Tag objects
        """
        if not tag_names:
            return []

        # Normalize tag names: lowercase, strip whitespace, remove duplicates
        normalized_names = list(set(name.strip().lower() for name in tag_names if name.strip()))

        if not normalized_names:
            return []

        # Find existing tags
        result = await db.execute(
            select(Tag).where(Tag.name.in_(normalized_names))
        )
        existing_tags = list(result.scalars().all())
        existing_tag_names = {tag.name for tag in existing_tags}

        # Create missing tags
        missing_names = [name for name in normalized_names if name not in existing_tag_names]
        new_tags = []

        for name in missing_names:
            tag = Tag(name=name)
            db.add(tag)
            new_tags.append(tag)

        if new_tags:
            await db.flush()  # Flush to get IDs without committing
            logger.info(f"Created {len(new_tags)} new tags: {[t.name for t in new_tags]}")

        # Return all tags sorted by name
        all_tags = existing_tags + new_tags
        all_tags.sort(key=lambda t: t.name)
        return all_tags

    @staticmethod
    async def list_tags(db: AsyncSession) -> list[tuple[Tag, int]]:
        """
        Get all tags with their usage counts.

        Args:
            db: Database session

        Returns:
            List of tuples (Tag, note_count)
        """
        result = await db.execute(
            select(Tag, func.count(NoteTag.note_id).label("note_count"))
            .outerjoin(NoteTag, Tag.id == NoteTag.tag_id)
            .group_by(Tag.id)
            .order_by(Tag.name)
        )

        return [(row[0], row[1]) for row in result.all()]

    @staticmethod
    async def get_popular_tags(
        db: AsyncSession, limit: int = 10
    ) -> list[tuple[Tag, int]]:
        """
        Get most used tags.

        Args:
            db: Database session
            limit: Maximum number of tags to return

        Returns:
            List of tuples (Tag, note_count)
        """
        result = await db.execute(
            select(Tag, func.count(NoteTag.note_id).label("note_count"))
            .join(NoteTag, Tag.id == NoteTag.tag_id)
            .group_by(Tag.id)
            .order_by(func.count(NoteTag.note_id).desc())
            .limit(limit)
        )

        return [(row[0], row[1]) for row in result.all()]
