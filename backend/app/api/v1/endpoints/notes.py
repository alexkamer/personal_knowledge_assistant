"""
API endpoints for notes.
"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.note import NoteCreate, NoteUpdate, NoteResponse, NoteListResponse
from app.services.note_service import NoteService

router = APIRouter()


@router.post("/", response_model=NoteResponse, status_code=201)
async def create_note(
    note_data: NoteCreate,
    db: AsyncSession = Depends(get_db),
) -> NoteResponse:
    """
    Create a new note.
    """
    note = await NoteService.create_note(db, note_data)
    return NoteResponse.model_validate(note)


@router.get("/", response_model=NoteListResponse)
async def list_notes(
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
    tags: Annotated[str | None, Query(description="Comma-separated tag names to filter by")] = None,
    db: AsyncSession = Depends(get_db),
) -> NoteListResponse:
    """
    List all notes with pagination and optional tag filtering.

    Args:
        skip: Number of notes to skip
        limit: Maximum number of notes to return
        tags: Comma-separated tag names for filtering (AND logic)
        db: Database session

    Returns:
        List of notes matching criteria
    """
    # Parse comma-separated tags
    tag_names = None
    if tags:
        tag_names = [tag.strip() for tag in tags.split(",") if tag.strip()]

    notes, total = await NoteService.list_notes(
        db, skip=skip, limit=limit, tag_names=tag_names
    )
    return NoteListResponse(
        notes=[NoteResponse.model_validate(note) for note in notes],
        total=total,
    )


@router.get("/{note_id}", response_model=NoteResponse)
async def get_note(
    note_id: str,
    db: AsyncSession = Depends(get_db),
) -> NoteResponse:
    """
    Get a specific note by ID.
    """
    note = await NoteService.get_note(db, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return NoteResponse.model_validate(note)


@router.put("/{note_id}", response_model=NoteResponse)
async def update_note(
    note_id: str,
    note_data: NoteUpdate,
    db: AsyncSession = Depends(get_db),
) -> NoteResponse:
    """
    Update an existing note.
    """
    note = await NoteService.update_note(db, note_id, note_data)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return NoteResponse.model_validate(note)


@router.delete("/{note_id}", status_code=204)
async def delete_note(
    note_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete a note.
    """
    deleted = await NoteService.delete_note(db, note_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Note not found")
