"""
Simple script to clear all chunks and reprocess documents with semantic metadata.
"""
import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, delete

from app.core.database import AsyncSessionLocal
from app.models.document import Document
from app.models.chunk import Chunk
from app.services.chunk_processing_service import ChunkProcessingService
from app.utils.file_handler import extract_text_from_file
from app.core.vector_db import get_chroma_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def clear_and_reprocess():
    """Clear all chunks and reprocess all documents."""
    async with AsyncSessionLocal() as db:
        # Get chroma client
        chroma_client = get_chroma_client()

        # 1. Delete all chunks from PostgreSQL
        logger.info("Deleting all chunks from PostgreSQL...")
        await db.execute(delete(Chunk))
        await db.commit()
        logger.info("✓ Chunks deleted from PostgreSQL")

        # 2. Clear ChromaDB collection
        logger.info("Clearing ChromaDB collection...")
        try:
            chroma_client.delete_collection("knowledge_base")
            logger.info("✓ ChromaDB collection deleted")
        except Exception as e:
            logger.warning(f"Could not delete collection: {e}")

        # 3. Recreate collection
        logger.info("Recreating ChromaDB collection...")
        chroma_client.get_or_create_collection(
            name="knowledge_base",
            metadata={"hnsw:space": "cosine"}
        )
        logger.info("✓ ChromaDB collection recreated")

        # 4. Fetch all documents
        result = await db.execute(select(Document))
        documents = result.scalars().all()

        if not documents:
            logger.info("No documents found")
            return

        logger.info(f"\nFound {len(documents)} documents to reprocess")

        # 5. Reprocess each document
        chunk_service = ChunkProcessingService(use_semantic=True)

        for doc in documents:
            try:
                logger.info(f"\nReprocessing: {doc.filename}")

                # Check file exists
                file_path = Path(doc.file_path)
                if not file_path.exists():
                    logger.error(f"✗ File not found: {file_path}")
                    continue

                # Extract text
                content = await extract_text_from_file(doc.file_path, doc.file_type)

                if not content or not content.strip():
                    logger.warning(f"✗ No content extracted from {doc.filename}")
                    continue

                # Process with semantic chunking
                chunks = await chunk_service.process_document(
                    db=db,
                    document_id=str(doc.id),
                    content=content,
                )

                logger.info(f"✓ {doc.filename}: {len(chunks)} chunks with metadata")

            except Exception as e:
                logger.error(f"✗ Failed to reprocess {doc.filename}: {e}")
                continue

        logger.info("\n✓✓✓ All documents reprocessed successfully! ✓✓✓")


if __name__ == "__main__":
    asyncio.run(clear_and_reprocess())
