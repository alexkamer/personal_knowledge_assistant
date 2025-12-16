"""
Document upload and management endpoints.
"""
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.config import settings
from app.schemas.document import (
    DocumentContentResponse,
    DocumentListResponse,
    DocumentResponse,
)
from app.services.document_service import DocumentService
from app.schemas.document import DocumentCreate
from app.utils.file_handler import (
    delete_file,
    extract_text_from_file,
    save_upload_file,
)

router = APIRouter()


@router.post("/", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> DocumentResponse:
    """
    Upload a document and extract its text content.

    Supports: TXT, MD, PDF, DOCX file types.
    Maximum file size: 50MB (configurable via settings).
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must have a filename",
        )

    # Validate file type
    file_extension = file.filename.split(".")[-1].lower() if "." in file.filename else ""
    if file_extension not in settings.allowed_file_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type '{file_extension}' not supported. Allowed types: {', '.join(settings.allowed_file_types)}",
        )

    # Check file size (read first to get actual size)
    file_content = await file.read()
    file_size_mb = len(file_content) / (1024 * 1024)

    if file_size_mb > settings.max_upload_size_mb:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size ({file_size_mb:.1f}MB) exceeds maximum allowed size ({settings.max_upload_size_mb}MB)",
        )

    # Reset file pointer for save_upload_file
    await file.seek(0)

    # Save the uploaded file
    try:
        file_path, file_size = await save_upload_file(file)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}",
        )

    # Extract file type
    file_type = file.filename.split(".")[-1] if "." in file.filename else "txt"

    # Extract text content
    try:
        content = await extract_text_from_file(file_path, file_type)
    except Exception as e:
        # Clean up the file if extraction fails
        await delete_file(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract text: {str(e)}",
        )

    # Create document record in database
    document_data = DocumentCreate(
        filename=file.filename,
        file_path=file_path,
        file_type=file_type,
        file_size=file_size,
        content=content,
        metadata_=None,
    )

    try:
        document = await DocumentService.create_document(db, document_data)
        return DocumentResponse.model_validate(document)
    except Exception as e:
        # Clean up the file if database operation fails
        await delete_file(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create document record: {str(e)}",
        )


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
    db: AsyncSession = Depends(get_db),
) -> DocumentListResponse:
    """
    List all documents with pagination.

    Returns documents ordered by creation date (newest first).
    """
    documents, total = await DocumentService.list_documents(db, skip=skip, limit=limit)

    return DocumentListResponse(
        documents=[DocumentResponse.model_validate(doc) for doc in documents],
        total=total,
    )


@router.get("/{document_id}", response_model=DocumentContentResponse)
async def get_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
) -> DocumentContentResponse:
    """
    Get a specific document with its full extracted content.
    """
    document = await DocumentService.get_document(db, document_id)

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    return DocumentContentResponse.model_validate(document)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete a document and its associated file.
    """
    # Get document first to access file path
    document = await DocumentService.get_document(db, document_id)

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    # Delete from database
    deleted = await DocumentService.delete_document(db, document_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document from database",
        )

    # Delete file from disk (best effort, don't fail if file is already gone)
    await delete_file(document.file_path)
