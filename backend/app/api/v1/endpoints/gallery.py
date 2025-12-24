"""
Gallery endpoints for managing generated images.
"""
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.core.database import get_db
from app.models.generated_image import GeneratedImage
from app.schemas.generated_image import (
    GeneratedImageResponse,
    GalleryListResponse,
    UpdateImageRequest,
    DeleteImageResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/list", response_model=GalleryListResponse)
async def list_images(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(20, ge=1, le=100, description="Number of images per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    favorites_only: bool = Query(False, description="Show only favorited images"),
    tags: Optional[str] = Query(None, description="Filter by tags (comma-separated)"),
    include_thumbnails_only: bool = Query(
        True, description="Return only thumbnails (faster, smaller response)"
    ),
) -> GalleryListResponse:
    """
    List generated images with pagination and filters.

    By default, returns thumbnails only for performance.
    Set include_thumbnails_only=false to get full image data.
    """
    try:
        # Build query
        query = select(GeneratedImage)

        # Apply filters
        if favorites_only:
            query = query.where(GeneratedImage.is_favorite == True)

        if tags:
            tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
            if tag_list:
                # Filter images that have ANY of the specified tags
                query = query.where(GeneratedImage.tags.overlap(tag_list))

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        result = await db.execute(count_query)
        total = result.scalar() or 0

        # Apply pagination and ordering (most recent first)
        query = query.order_by(desc(GeneratedImage.created_at))
        query = query.limit(limit).offset(offset)

        # Execute query
        result = await db.execute(query)
        images = result.scalars().all()

        # Convert to response models
        image_responses = []
        for img in images:
            img_dict = {
                "id": img.id,
                "prompt": img.prompt,
                "negative_prompt": img.negative_prompt,
                "image_format": img.image_format,
                "metadata_": img.metadata_,
                "width": img.width,
                "height": img.height,
                "is_favorite": img.is_favorite,
                "tags": img.tags or [],
                "created_at": img.created_at,
                "updated_at": img.updated_at,
            }

            # Include full image or just thumbnail based on parameter
            if include_thumbnails_only:
                img_dict["thumbnail_data"] = img.thumbnail_data
                img_dict["image_data"] = None
            else:
                img_dict["thumbnail_data"] = img.thumbnail_data
                img_dict["image_data"] = img.image_data

            image_responses.append(GeneratedImageResponse(**img_dict))

        has_more = (offset + limit) < total

        return GalleryListResponse(
            images=image_responses,
            total=total,
            limit=limit,
            offset=offset,
            has_more=has_more,
        )

    except Exception as e:
        logger.error(f"Failed to list images: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve images: {str(e)}",
        )


@router.get("/{image_id}", response_model=GeneratedImageResponse)
async def get_image(
    image_id: str,
    db: AsyncSession = Depends(get_db),
    include_full_image: bool = Query(True, description="Include full image data"),
) -> GeneratedImageResponse:
    """
    Get a single image by ID.

    By default, includes full image data. Set include_full_image=false for thumbnail only.
    """
    try:
        query = select(GeneratedImage).where(GeneratedImage.id == image_id)
        result = await db.execute(query)
        img = result.scalar_one_or_none()

        if not img:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Image with ID {image_id} not found",
            )

        img_dict = {
            "id": img.id,
            "prompt": img.prompt,
            "negative_prompt": img.negative_prompt,
            "image_format": img.image_format,
            "metadata_": img.metadata_,
            "width": img.width,
            "height": img.height,
            "is_favorite": img.is_favorite,
            "tags": img.tags or [],
            "created_at": img.created_at,
            "updated_at": img.updated_at,
            "thumbnail_data": img.thumbnail_data,
        }

        if include_full_image:
            img_dict["image_data"] = img.image_data
        else:
            img_dict["image_data"] = None

        return GeneratedImageResponse(**img_dict)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get image {image_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve image: {str(e)}",
        )


@router.patch("/{image_id}", response_model=GeneratedImageResponse)
async def update_image(
    image_id: str,
    update_data: UpdateImageRequest,
    db: AsyncSession = Depends(get_db),
) -> GeneratedImageResponse:
    """
    Update image metadata (favorite status, tags).
    """
    try:
        # Fetch image
        query = select(GeneratedImage).where(GeneratedImage.id == image_id)
        result = await db.execute(query)
        img = result.scalar_one_or_none()

        if not img:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Image with ID {image_id} not found",
            )

        # Update fields
        if update_data.is_favorite is not None:
            img.is_favorite = update_data.is_favorite

        if update_data.tags is not None:
            img.tags = update_data.tags

        # Save changes
        await db.commit()
        await db.refresh(img)

        # Return updated image (thumbnail only for performance)
        img_dict = {
            "id": img.id,
            "prompt": img.prompt,
            "negative_prompt": img.negative_prompt,
            "image_format": img.image_format,
            "metadata_": img.metadata_,
            "width": img.width,
            "height": img.height,
            "is_favorite": img.is_favorite,
            "tags": img.tags or [],
            "created_at": img.created_at,
            "updated_at": img.updated_at,
            "thumbnail_data": img.thumbnail_data,
            "image_data": None,
        }

        return GeneratedImageResponse(**img_dict)

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to update image {image_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update image: {str(e)}",
        )


@router.delete("/{image_id}", response_model=DeleteImageResponse)
async def delete_image(
    image_id: str,
    db: AsyncSession = Depends(get_db),
) -> DeleteImageResponse:
    """
    Delete a generated image by ID.
    """
    try:
        # Fetch image
        query = select(GeneratedImage).where(GeneratedImage.id == image_id)
        result = await db.execute(query)
        img = result.scalar_one_or_none()

        if not img:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Image with ID {image_id} not found",
            )

        # Delete image
        await db.delete(img)
        await db.commit()

        logger.info(f"Deleted image {image_id}")

        return DeleteImageResponse(
            success=True,
            message=f"Image {image_id} successfully deleted",
        )

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to delete image {image_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete image: {str(e)}",
        )
