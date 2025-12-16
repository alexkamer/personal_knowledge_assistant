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
        content_type: Optional[str] = None,
        has_code: Optional[bool] = None,
        section_title: Optional[str] = None,
    ) -> dict:
        """
        Search for similar chunks using vector similarity with optional metadata filtering.

        Args:
            query_embedding: Query embedding vector
            n_results: Number of results to return
            source_type: Optional filter for source type ('note' or 'document')
            content_type: Optional filter for content type ('narrative', 'code', 'list', etc.)
            has_code: Optional filter for chunks containing code
            section_title: Optional filter for section title (contains match)

        Returns:
            Dictionary with ids, distances, documents, and metadatas
        """
        try:
            # Build where filter combining all specified filters
            where_filter = None
            filter_conditions = []

            if source_type:
                filter_conditions.append({"source_type": source_type})

            if content_type:
                filter_conditions.append({"content_type": content_type})

            if has_code is not None:
                filter_conditions.append({"has_code": has_code})

            # Note: ChromaDB doesn't support "contains" for strings directly in where clause
            # section_title would need to be filtered post-retrieval or use exact match
            if section_title:
                filter_conditions.append({"section_title": section_title})

            # Combine filters using $and if multiple conditions
            if len(filter_conditions) > 1:
                where_filter = {"$and": filter_conditions}
            elif len(filter_conditions) == 1:
                where_filter = filter_conditions[0]

            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where_filter,
            )

            logger.debug(f"Found {len(results['ids'][0])} similar chunks (filters: source_type={source_type}, content_type={content_type}, has_code={has_code}, section_title={section_title})")
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
