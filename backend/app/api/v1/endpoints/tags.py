"""
API endpoints for tag operations.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.tag import TagWithUsage
from app.services.tag_service import TagService

router = APIRouter()


@router.get("/", response_model=list[TagWithUsage])
async def list_tags(db: AsyncSession = Depends(get_db)):
    """
    Get all tags with usage counts.

    Returns:
        List of tags with note_count
    """
    tags_with_usage = await TagService.list_tags(db)
    return [
        TagWithUsage(
            id=tag.id,
            name=tag.name,
            created_at=tag.created_at,
            note_count=count,
        )
        for tag, count in tags_with_usage
    ]


@router.get("/popular", response_model=list[TagWithUsage])
async def get_popular_tags(
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
):
    """
    Get most used tags.

    Args:
        limit: Maximum number of tags to return (default: 10)

    Returns:
        List of most used tags with note_count
    """
    tags_with_usage = await TagService.get_popular_tags(db, limit=limit)
    return [
        TagWithUsage(
            id=tag.id,
            name=tag.name,
            created_at=tag.created_at,
            note_count=count,
        )
        for tag, count in tags_with_usage
    ]
