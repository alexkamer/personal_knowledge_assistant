"""
Vector database (ChromaDB) initialization and management.
"""
import logging
from typing import Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.core.config import settings

logger = logging.getLogger(__name__)

# Global ChromaDB client
_chroma_client: Optional[chromadb.ClientAPI] = None


def get_chroma_client() -> chromadb.ClientAPI:
    """
    Get or create ChromaDB client instance.

    Returns:
        chromadb.ClientAPI: ChromaDB client
    """
    global _chroma_client

    if _chroma_client is None:
        logger.info(f"Initializing ChromaDB at {settings.chroma_persist_directory}")
        _chroma_client = chromadb.PersistentClient(
            path=settings.chroma_persist_directory,
        )
        logger.info("ChromaDB initialized successfully")

    return _chroma_client


def get_or_create_collection(
    collection_name: Optional[str] = None,
) -> chromadb.Collection:
    """
    Get or create a ChromaDB collection.

    Args:
        collection_name: Name of the collection. Defaults to settings.chroma_collection_name

    Returns:
        chromadb.Collection: ChromaDB collection
    """
    client = get_chroma_client()
    collection_name = collection_name or settings.chroma_collection_name

    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={
            "description": "Knowledge base embeddings for RAG",
            "embedding_dimension": settings.embedding_dimension,
        },
    )

    logger.info(f"Using ChromaDB collection: {collection_name}")
    return collection


async def close_chroma() -> None:
    """
    Close ChromaDB connections and persist data.
    """
    global _chroma_client

    if _chroma_client is not None:
        logger.info("Closing ChromaDB connections")
        # ChromaDB automatically persists on client deletion
        _chroma_client = None
        logger.info("ChromaDB connections closed")
