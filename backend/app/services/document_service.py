"""
Service layer for document CRUD operations.
"""
import logging
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.schemas.document import DocumentCreate
from app.services.chunk_processing_service import get_chunk_processing_service

logger = logging.getLogger(__name__)


class DocumentService:
    """Service for managing documents."""

    @staticmethod
    async def create_document(db: AsyncSession, document_data: DocumentCreate) -> Document:
        """
        Create a new document record and process it for embeddings.

        Args:
            db: Database session
            document_data: Document creation data

        Returns:
            Created document
        """
        document = Document(
            filename=document_data.filename,
            file_path=document_data.file_path,
            file_type=document_data.file_type,
            file_size=document_data.file_size,
            content=document_data.content,
            metadata_=document_data.metadata_,
        )
        db.add(document)
        await db.commit()
        await db.refresh(document)

        # Process document for chunking and embeddings
        try:
            chunk_service = get_chunk_processing_service()
            await chunk_service.process_document(db, str(document.id), document.content)
            logger.info(f"Processed chunks for new document {document.id}")
        except Exception as e:
            logger.error(f"Failed to process chunks for document {document.id}: {e}")
            # Don't fail the document creation if chunking fails

        return document

    @staticmethod
    async def get_document(db: AsyncSession, document_id: str) -> Optional[Document]:
        """
        Get a document by ID.

        Args:
            db: Database session
            document_id: Document ID

        Returns:
            Document if found, None otherwise
        """
        result = await db.execute(select(Document).where(Document.id == document_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def list_documents(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[Document], int]:
        """
        List documents with pagination.

        Args:
            db: Database session
            skip: Number of documents to skip
            limit: Maximum number of documents to return

        Returns:
            Tuple of (documents list, total count)
        """
        # Get total count
        count_result = await db.execute(select(func.count(Document.id)))
        total = count_result.scalar_one()

        # Get documents
        result = await db.execute(
            select(Document)
            .order_by(Document.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        documents = list(result.scalars().all())

        return documents, total

    @staticmethod
    async def delete_document(db: AsyncSession, document_id: str) -> bool:
        """
        Delete a document.

        Args:
            db: Database session
            document_id: Document ID

        Returns:
            True if deleted, False if not found
        """
        result = await db.execute(select(Document).where(Document.id == document_id))
        document = result.scalar_one_or_none()

        if not document:
            return False

        await db.delete(document)
        await db.commit()
        return True
