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
    DocumentFromURLRequest,
    DocumentFromURLResponse,
)
from app.services.document_service import DocumentService
from app.schemas.document import DocumentCreate
from app.utils.file_handler import (
    delete_file,
    extract_text_from_file,
    save_upload_file,
)
from app.utils.url_extractor import extract_text_from_url
from app.services.categorization_service import categorize_document, get_all_categories
import json

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

    # Save the uploaded file (and optionally archive it)
    try:
        file_path, file_size, archive_path, storage_location = await save_upload_file(file)
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

    # Auto-categorize the document
    category = categorize_document(
        filename=file.filename,
        content=content,
        file_type=file_type,
    )

    # Create document record in database
    document_data = DocumentCreate(
        filename=file.filename,
        file_path=file_path,
        file_type=file_type,
        file_size=file_size,
        content=content,
        metadata_=None,
        category=category,
        archive_path=archive_path,
        storage_location=storage_location,
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


@router.post("/from-url", response_model=DocumentFromURLResponse, status_code=status.HTTP_201_CREATED)
async def create_document_from_url(
    request: DocumentFromURLRequest,
    db: AsyncSession = Depends(get_db),
) -> DocumentFromURLResponse:
    """
    Create a document by fetching content from a URL.

    Fetches the webpage, extracts main content, and stores it as a document.
    Supports most web pages including articles, blog posts, and documentation.
    """
    # Extract content from URL
    try:
        content, metadata = await extract_text_from_url(request.url)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch URL: {str(e)}",
        )

    # Generate filename from URL or title
    filename = metadata.get('title', metadata.get('source_url', 'unknown'))
    # Clean filename (remove invalid chars)
    filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_')).strip()
    if not filename:
        filename = "web_document"
    filename = f"{filename[:100]}.html"  # Truncate if too long

    # Auto-categorize the document
    category = categorize_document(
        filename=filename,
        content=content,
        metadata_json=json.dumps(metadata),
        file_type="html",
    )

    # Create document record in database
    document_data = DocumentCreate(
        filename=filename,
        file_path=request.url,  # Store URL as file_path for web documents
        file_type="html",
        file_size=len(content.encode('utf-8')),
        content=content,
        metadata_=json.dumps(metadata),
        category=category,
    )

    try:
        document = await DocumentService.create_document(db, document_data)
        return DocumentFromURLResponse.model_validate(document)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create document record: {str(e)}",
        )


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
    category: Annotated[str | None, Query()] = None,
    sort_by: Annotated[str, Query()] = "created_at",
    sort_order: Annotated[str, Query()] = "desc",
    db: AsyncSession = Depends(get_db),
) -> DocumentListResponse:
    """
    List all documents with pagination, filtering, and sorting.

    Args:
        skip: Number of documents to skip
        limit: Maximum number of documents to return
        category: Filter by category (optional)
        sort_by: Field to sort by (created_at, filename, file_size, category)
        sort_order: Sort order (asc or desc)

    Returns documents based on filters and sorting.
    """
    documents, total = await DocumentService.list_documents(
        db,
        skip=skip,
        limit=limit,
        category=category,
        sort_by=sort_by,
        sort_order=sort_order,
    )

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


@router.get("/categories/list", response_model=list[str])
async def list_categories() -> list[str]:
    """
    Get list of all available document categories.
    """
    return get_all_categories()


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
