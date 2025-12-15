"""
Chunk processing service that orchestrates text chunking and embedding.
"""
import logging
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.chunk import Chunk
from app.services.embedding_service import get_embedding_service
from app.services.vector_service import get_vector_service
from app.utils.text_chunker import TextChunker

logger = logging.getLogger(__name__)


class ChunkProcessingService:
    """Service for processing text into chunks and embeddings."""

    def __init__(self):
        """Initialize the chunk processing service."""
        self.chunker = TextChunker(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )
        self.embedding_service = get_embedding_service()
        self.vector_service = get_vector_service()

    async def process_note(
        self,
        db: AsyncSession,
        note_id: str,
        content: str,
    ) -> List[Chunk]:
        """
        Process a note: chunk the content, generate embeddings, and store.

        Args:
            db: Database session
            note_id: ID of the note
            content: Note content to process

        Returns:
            List of created chunk objects
        """
        logger.info(f"Processing note {note_id}")

        # Delete existing chunks for this note
        await self._delete_existing_chunks(db, note_id, "note")

        # Chunk the text
        chunk_texts = self.chunker.split_text(content)
        if not chunk_texts:
            logger.warning(f"No chunks generated for note {note_id}")
            return []

        logger.info(f"Generated {len(chunk_texts)} chunks for note {note_id}")

        # Generate embeddings
        embeddings = self.embedding_service.embed_batch(chunk_texts)

        # Create chunk records in database
        chunks = []
        for idx, (chunk_text, embedding) in enumerate(zip(chunk_texts, embeddings)):
            chunk = Chunk(
                note_id=note_id,
                document_id=None,
                content=chunk_text,
                chunk_index=idx,
                token_count=self.chunker.count_tokens(chunk_text),
            )
            db.add(chunk)
            chunks.append(chunk)

        await db.commit()

        # Refresh to get IDs
        for chunk in chunks:
            await db.refresh(chunk)

        # Store embeddings in vector database
        chunk_ids = [str(chunk.id) for chunk in chunks]
        metadatas = [
            {
                "source_id": note_id,
                "source_type": "note",
                "chunk_index": chunk.chunk_index,
                "token_count": chunk.token_count,
            }
            for chunk in chunks
        ]

        await self.vector_service.add_batch_embeddings(
            chunk_ids=chunk_ids,
            embeddings=embeddings,
            chunk_texts=chunk_texts,
            metadatas=metadatas,
        )

        logger.info(f"Successfully processed note {note_id} with {len(chunks)} chunks")
        return chunks

    async def process_document(
        self,
        db: AsyncSession,
        document_id: str,
        content: str,
    ) -> List[Chunk]:
        """
        Process a document: chunk the content, generate embeddings, and store.

        Args:
            db: Database session
            document_id: ID of the document
            content: Document content to process

        Returns:
            List of created chunk objects
        """
        logger.info(f"Processing document {document_id}")

        # Delete existing chunks for this document
        await self._delete_existing_chunks(db, document_id, "document")

        # Chunk the text
        chunk_texts = self.chunker.split_text(content)
        if not chunk_texts:
            logger.warning(f"No chunks generated for document {document_id}")
            return []

        logger.info(f"Generated {len(chunk_texts)} chunks for document {document_id}")

        # Generate embeddings
        embeddings = self.embedding_service.embed_batch(chunk_texts)

        # Create chunk records in database
        chunks = []
        for idx, (chunk_text, embedding) in enumerate(zip(chunk_texts, embeddings)):
            chunk = Chunk(
                note_id=None,
                document_id=document_id,
                content=chunk_text,
                chunk_index=idx,
                token_count=self.chunker.count_tokens(chunk_text),
            )
            db.add(chunk)
            chunks.append(chunk)

        await db.commit()

        # Refresh to get IDs
        for chunk in chunks:
            await db.refresh(chunk)

        # Store embeddings in vector database
        chunk_ids = [str(chunk.id) for chunk in chunks]
        metadatas = [
            {
                "source_id": document_id,
                "source_type": "document",
                "chunk_index": chunk.chunk_index,
                "token_count": chunk.token_count,
            }
            for chunk in chunks
        ]

        await self.vector_service.add_batch_embeddings(
            chunk_ids=chunk_ids,
            embeddings=embeddings,
            chunk_texts=chunk_texts,
            metadatas=metadatas,
        )

        logger.info(f"Successfully processed document {document_id} with {len(chunks)} chunks")
        return chunks

    async def _delete_existing_chunks(
        self,
        db: AsyncSession,
        source_id: str,
        source_type: str,
    ) -> None:
        """
        Delete existing chunks for a source from both database and vector store.

        Args:
            db: Database session
            source_id: ID of the source
            source_type: Type of source ('note' or 'document')
        """
        # Find existing chunks in database
        if source_type == "note":
            result = await db.execute(
                select(Chunk).where(Chunk.note_id == source_id)
            )
        else:
            result = await db.execute(
                select(Chunk).where(Chunk.document_id == source_id)
            )

        existing_chunks = list(result.scalars().all())

        if not existing_chunks:
            return

        logger.info(f"Deleting {len(existing_chunks)} existing chunks for {source_type} {source_id}")

        # Delete from vector database
        await self.vector_service.delete_chunks_by_source(source_id, source_type)

        # Delete from PostgreSQL
        for chunk in existing_chunks:
            await db.delete(chunk)

        await db.commit()


# Global instance
def get_chunk_processing_service() -> ChunkProcessingService:
    """
    Get a chunk processing service instance.

    Returns:
        ChunkProcessingService instance
    """
    return ChunkProcessingService()
