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
from app.utils.semantic_chunker import SemanticChunker

logger = logging.getLogger(__name__)


class ChunkProcessingService:
    """Service for processing text into chunks and embeddings."""

    def __init__(self, use_semantic: bool = True):
        """
        Initialize the chunk processing service.

        Args:
            use_semantic: Whether to use semantic chunker (default True)
        """
        self.use_semantic = use_semantic

        if use_semantic:
            self.semantic_chunker = SemanticChunker(
                min_chunk_size=256,
                max_chunk_size=768,
            )
        else:
            # Fallback to basic chunker
            self.basic_chunker = TextChunker(
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

        # Chunk the text using appropriate chunker
        if self.use_semantic:
            semantic_chunks = self.semantic_chunker.split_text(content)
            if not semantic_chunks:
                logger.warning(f"No chunks generated for note {note_id}")
                return []
        else:
            chunk_texts = self.basic_chunker.split_text(content)
            if not chunk_texts:
                logger.warning(f"No chunks generated for note {note_id}")
                return []
            # Convert to semantic chunks format for consistency
            semantic_chunks = [
                type('obj', (object,), {
                    'content': text,
                    'metadata': type('obj', (object,), {
                        'content_type': 'narrative',
                        'heading_hierarchy': [],
                        'section_title': None,
                        'has_code': False,
                        'token_count': self.basic_chunker.count_tokens(text),
                        'semantic_density': 0.5,
                    })()
                })()
                for text in chunk_texts
            ]

        logger.info(f"Generated {len(semantic_chunks)} chunks for note {note_id}")

        # Extract texts for embedding
        chunk_texts = [sc.content for sc in semantic_chunks]

        # Generate embeddings
        embeddings = self.embedding_service.embed_batch(chunk_texts)

        # Create chunk records in database
        chunks = []
        for idx, (semantic_chunk, embedding) in enumerate(zip(semantic_chunks, embeddings)):
            chunk = Chunk(
                note_id=note_id,
                document_id=None,
                content=semantic_chunk.content,
                chunk_index=idx,
                token_count=semantic_chunk.metadata.token_count,
                content_type=semantic_chunk.metadata.content_type,
                heading_hierarchy={"hierarchy": semantic_chunk.metadata.heading_hierarchy},
                section_title=semantic_chunk.metadata.section_title,
                has_code=semantic_chunk.metadata.has_code,
                semantic_density=semantic_chunk.metadata.semantic_density,
            )
            db.add(chunk)
            chunks.append(chunk)

        await db.commit()

        # Refresh to get IDs
        for chunk in chunks:
            await db.refresh(chunk)

        # Store embeddings in vector database
        chunk_ids = [str(chunk.id) for chunk in chunks]
        metadatas = []
        for chunk in chunks:
            metadata = {
                "source_id": note_id,
                "source_type": "note",
                "chunk_index": chunk.chunk_index,
                "token_count": chunk.token_count,
            }
            # Only add optional fields if they have non-None values
            if chunk.content_type is not None:
                metadata["content_type"] = chunk.content_type
            if chunk.section_title is not None:
                metadata["section_title"] = chunk.section_title
            if chunk.has_code is not None:
                metadata["has_code"] = chunk.has_code
            if chunk.semantic_density is not None:
                metadata["semantic_density"] = chunk.semantic_density
            metadatas.append(metadata)

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

        # Chunk the text using appropriate chunker
        if self.use_semantic:
            semantic_chunks = self.semantic_chunker.split_text(content)
            if not semantic_chunks:
                logger.warning(f"No chunks generated for document {document_id}")
                return []
        else:
            chunk_texts = self.basic_chunker.split_text(content)
            if not chunk_texts:
                logger.warning(f"No chunks generated for document {document_id}")
                return []
            # Convert to semantic chunks format for consistency
            semantic_chunks = [
                type('obj', (object,), {
                    'content': text,
                    'metadata': type('obj', (object,), {
                        'content_type': 'narrative',
                        'heading_hierarchy': [],
                        'section_title': None,
                        'has_code': False,
                        'token_count': self.basic_chunker.count_tokens(text),
                        'semantic_density': 0.5,
                    })()
                })()
                for text in chunk_texts
            ]

        logger.info(f"Generated {len(semantic_chunks)} chunks for document {document_id}")

        # Extract texts for embedding
        chunk_texts = [sc.content for sc in semantic_chunks]

        # Generate embeddings
        embeddings = self.embedding_service.embed_batch(chunk_texts)

        # Create chunk records in database
        chunks = []
        for idx, (semantic_chunk, embedding) in enumerate(zip(semantic_chunks, embeddings)):
            chunk = Chunk(
                note_id=None,
                document_id=document_id,
                content=semantic_chunk.content,
                chunk_index=idx,
                token_count=semantic_chunk.metadata.token_count,
                content_type=semantic_chunk.metadata.content_type,
                heading_hierarchy={"hierarchy": semantic_chunk.metadata.heading_hierarchy},
                section_title=semantic_chunk.metadata.section_title,
                has_code=semantic_chunk.metadata.has_code,
                semantic_density=semantic_chunk.metadata.semantic_density,
            )
            db.add(chunk)
            chunks.append(chunk)

        await db.commit()

        # Refresh to get IDs
        for chunk in chunks:
            await db.refresh(chunk)

        # Store embeddings in vector database
        chunk_ids = [str(chunk.id) for chunk in chunks]
        metadatas = []
        for chunk in chunks:
            metadata = {
                "source_id": document_id,
                "source_type": "document",
                "chunk_index": chunk.chunk_index,
                "token_count": chunk.token_count,
            }
            # Only add optional fields if they have non-None values
            if chunk.content_type is not None:
                metadata["content_type"] = chunk.content_type
            if chunk.section_title is not None:
                metadata["section_title"] = chunk.section_title
            if chunk.has_code is not None:
                metadata["has_code"] = chunk.has_code
            if chunk.semantic_density is not None:
                metadata["semantic_density"] = chunk.semantic_density
            metadatas.append(metadata)

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
