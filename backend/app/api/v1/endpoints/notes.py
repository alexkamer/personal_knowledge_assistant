"""
API endpoints for notes.
"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.note import (
    NoteCreate,
    NoteUpdate,
    NoteResponse,
    NoteListResponse,
    BacklinkResponse,
    BacklinksListResponse,
    RelatedNoteResponse,
    RelatedNotesListResponse,
)
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


@router.get("/{note_id}/backlinks", response_model=BacklinksListResponse)
async def get_note_backlinks(
    note_id: str,
    db: AsyncSession = Depends(get_db),
) -> BacklinksListResponse:
    """
    Get all notes that link to this note (backlinks).

    Args:
        note_id: Target note ID
        db: Database session

    Returns:
        List of notes that contain wiki links to the target note
    """
    backlinks = await NoteService.get_backlinks(db, note_id)
    return BacklinksListResponse(
        backlinks=[BacklinkResponse.model_validate(note) for note in backlinks],
        total=len(backlinks),
    )


@router.get("/{note_id}/related", response_model=RelatedNotesListResponse)
async def get_related_notes(
    note_id: str,
    limit: int = 5,
    db: AsyncSession = Depends(get_db),
) -> RelatedNotesListResponse:
    """
    Get semantically related notes using vector similarity.

    Finds notes with similar content based on embedding similarity,
    helping users discover relevant connections beyond explicit wiki links.

    Args:
        note_id: Target note ID
        limit: Maximum number of related notes to return (default: 5)
        db: Database session

    Returns:
        List of related notes with similarity scores
    """
    related_notes_with_scores = await NoteService.get_related_notes(
        db, note_id, limit=limit
    )

    # Convert to response format
    related_notes = [
        RelatedNoteResponse(
            id=note.id,
            title=note.title,
            created_at=note.created_at,
            updated_at=note.updated_at,
            similarity_score=score,
        )
        for note, score in related_notes_with_scores
    ]

    return RelatedNotesListResponse(
        related_notes=related_notes,
        total=len(related_notes),
    )
