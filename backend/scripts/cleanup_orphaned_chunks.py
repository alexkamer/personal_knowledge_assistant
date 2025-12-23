#!/usr/bin/env python3
"""
Cleanup script to remove orphaned chunks from ChromaDB.

Orphaned chunks are chunks that exist in ChromaDB but their source documents/notes
have been deleted from PostgreSQL.
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.vector_db import get_chroma_client
from app.models import Document, Note, YouTubeVideo
from app.core.config import settings

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def cleanup_orphaned_chunks():
    """Remove chunks from ChromaDB that reference deleted sources."""

    # Get ChromaDB client and collection
    chroma_client = get_chroma_client()
    collection = chroma_client.get_or_create_collection(
        name=settings.chroma_collection_name,
        metadata={"hnsw:space": "cosine"}
    )

    # Get all chunks from ChromaDB
    all_chunks = collection.get(include=["metadatas"])
    chunk_ids = all_chunks["ids"]
    metadatas = all_chunks["metadatas"]

    logger.info(f"Found {len(chunk_ids)} total chunks in ChromaDB")

    # Track orphaned chunks
    orphaned_chunk_ids = []
    orphaned_by_type = {"document": 0, "note": 0, "youtube": 0}

    async with AsyncSessionLocal() as db:
        # Get all valid source IDs from PostgreSQL
        result = await db.execute(select(Document.id))
        valid_doc_ids = {str(doc_id) for (doc_id,) in result}
        logger.info(f"Found {len(valid_doc_ids)} valid documents in PostgreSQL")

        result = await db.execute(select(Note.id))
        valid_note_ids = {str(note_id) for (note_id,) in result}
        logger.info(f"Found {len(valid_note_ids)} valid notes in PostgreSQL")

        result = await db.execute(select(YouTubeVideo.id))
        valid_youtube_ids = {str(yt_id) for (yt_id,) in result}
        logger.info(f"Found {len(valid_youtube_ids)} valid YouTube videos in PostgreSQL")

        # Check each chunk
        for chunk_id, metadata in zip(chunk_ids, metadatas):
            source_type = metadata.get("source_type")
            source_id = metadata.get("source_id")

            if not source_id:
                logger.warning(f"Chunk {chunk_id} has no source_id, skipping")
                continue

            is_orphaned = False

            if source_type == "document" and source_id not in valid_doc_ids:
                is_orphaned = True
                orphaned_by_type["document"] += 1
            elif source_type == "note" and source_id not in valid_note_ids:
                is_orphaned = True
                orphaned_by_type["note"] += 1
            elif source_type == "youtube" and source_id not in valid_youtube_ids:
                is_orphaned = True
                orphaned_by_type["youtube"] += 1

            if is_orphaned:
                orphaned_chunk_ids.append(chunk_id)
                logger.debug(f"Found orphaned {source_type} chunk: {chunk_id} (source_id: {source_id})")

    # Report findings
    logger.info(f"\n{'='*60}")
    logger.info(f"Orphaned chunks found: {len(orphaned_chunk_ids)}")
    logger.info(f"  - Documents: {orphaned_by_type['document']}")
    logger.info(f"  - Notes: {orphaned_by_type['note']}")
    logger.info(f"  - YouTube: {orphaned_by_type['youtube']}")
    logger.info(f"{'='*60}\n")

    if not orphaned_chunk_ids:
        logger.info("No orphaned chunks found. ChromaDB is clean!")
        return

    # Ask for confirmation
    response = input(f"Delete {len(orphaned_chunk_ids)} orphaned chunks from ChromaDB? (yes/no): ")

    if response.lower() != "yes":
        logger.info("Cleanup cancelled.")
        return

    # Delete orphaned chunks
    logger.info("Deleting orphaned chunks...")
    collection.delete(ids=orphaned_chunk_ids)

    logger.info(f"✅ Successfully deleted {len(orphaned_chunk_ids)} orphaned chunks from ChromaDB")


if __name__ == "__main__":
    asyncio.run(cleanup_orphaned_chunks())
