"""
Vector database service for storing and retrieving embeddings.
"""
import logging
from typing import List, Optional
from uuid import UUID

import chromadb

from app.core.vector_db import get_or_create_collection
from app.models.chunk import Chunk

logger = logging.getLogger(__name__)


class VectorService:
    """Service for managing vectors in ChromaDB."""

    def __init__(self):
        """Initialize the vector service."""
        self.collection = get_or_create_collection()

    async def add_chunk_embedding(
        self,
        chunk_id: str,
        embedding: List[float],
        chunk_text: str,
        metadata: dict,
    ) -> None:
        """
        Add a chunk embedding to the vector database.

        Args:
            chunk_id: Unique ID for the chunk
            embedding: Embedding vector
            chunk_text: Original chunk text
            metadata: Metadata about the chunk (source_id, source_type, etc.)
        """
        try:
            self.collection.add(
                ids=[chunk_id],
                embeddings=[embedding],
                documents=[chunk_text],
                metadatas=[metadata],
            )
            logger.debug(f"Added embedding for chunk {chunk_id}")
        except Exception as e:
            logger.error(f"Failed to add embedding for chunk {chunk_id}: {e}")
            raise

    async def add_batch_embeddings(
        self,
        chunk_ids: List[str],
        embeddings: List[List[float]],
        chunk_texts: List[str],
        metadatas: List[dict],
    ) -> None:
        """
        Add multiple chunk embeddings to the vector database efficiently.

        Args:
            chunk_ids: List of chunk IDs
            embeddings: List of embedding vectors
            chunk_texts: List of chunk texts
            metadatas: List of metadata dictionaries
        """
        if not chunk_ids:
            return

        if len(chunk_ids) != len(embeddings) != len(chunk_texts) != len(metadatas):
            raise ValueError("All input lists must have the same length")

        try:
            self.collection.add(
                ids=chunk_ids,
                embeddings=embeddings,
                documents=chunk_texts,
                metadatas=metadatas,
            )
            logger.info(f"Added {len(chunk_ids)} embeddings to vector database")
        except Exception as e:
            logger.error(f"Failed to add batch embeddings: {e}")
            raise

    async def search_similar_chunks(
        self,
        query_embedding: List[float],
        n_results: int = 10,
        source_type: Optional[str] = None,
    ) -> dict:
        """
        Search for similar chunks using vector similarity.

        Args:
            query_embedding: Query embedding vector
            n_results: Number of results to return
            source_type: Optional filter for source type ('note' or 'document')

        Returns:
            Dictionary with ids, distances, documents, and metadatas
        """
        try:
            where_filter = {"source_type": source_type} if source_type else None

            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where_filter,
            )

            logger.debug(f"Found {len(results['ids'][0])} similar chunks")
            return results
        except Exception as e:
            logger.error(f"Failed to search similar chunks: {e}")
            raise

    async def delete_chunks_by_source(
        self,
        source_id: str,
        source_type: str,
    ) -> None:
        """
        Delete all chunks for a specific source (note or document).

        Args:
            source_id: ID of the source (note_id or document_id)
            source_type: Type of source ('note' or 'document')
        """
        try:
            # ChromaDB delete by metadata filter
            self.collection.delete(
                where={
                    "source_id": source_id,
                    "source_type": source_type,
                }
            )
            logger.info(f"Deleted chunks for {source_type} {source_id}")
        except Exception as e:
            logger.error(f"Failed to delete chunks for {source_type} {source_id}: {e}")
            raise

    async def delete_chunk(self, chunk_id: str) -> None:
        """
        Delete a specific chunk from the vector database.

        Args:
            chunk_id: ID of the chunk to delete
        """
        try:
            self.collection.delete(ids=[chunk_id])
            logger.debug(f"Deleted chunk {chunk_id}")
        except Exception as e:
            logger.error(f"Failed to delete chunk {chunk_id}: {e}")
            raise

    def get_collection_stats(self) -> dict:
        """
        Get statistics about the vector collection.

        Returns:
            Dictionary with collection statistics
        """
        try:
            count = self.collection.count()
            return {
                "total_chunks": count,
                "collection_name": self.collection.name,
            }
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            raise


# Global instance
_vector_service: VectorService | None = None


def get_vector_service() -> VectorService:
    """
    Get the global vector service instance.

    Returns:
        Vector service singleton
    """
    global _vector_service
    if _vector_service is None:
        _vector_service = VectorService()
    return _vector_service
