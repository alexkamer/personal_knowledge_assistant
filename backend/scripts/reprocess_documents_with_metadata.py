"""
Script to reprocess existing documents to add semantic chunking metadata.

This script will:
1. Fetch all existing documents
2. Re-extract their content
3. Re-chunk them using semantic chunker (which populates metadata)
4. Update both PostgreSQL chunks and ChromaDB embeddings with metadata
"""
import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.document import Document
from app.services.chunk_processing_service import ChunkProcessingService
from app.utils.file_handler import extract_text_from_file

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def reprocess_all_documents():
    """Reprocess all documents to add semantic metadata."""
    async with AsyncSessionLocal() as db:
        # Fetch all documents
        result = await db.execute(select(Document))
        documents = result.scalars().all()

        if not documents:
            logger.info("No documents found to reprocess")
            return

        logger.info(f"Found {len(documents)} documents to reprocess")

        # Initialize services
        chunk_service = ChunkProcessingService(use_semantic=True)

        # Process each document
        for doc in documents:
            try:
                logger.info(f"\nReprocessing document: {doc.filename} (ID: {doc.id})")

                # Check if file exists
                file_path = Path(doc.file_path)
                if not file_path.exists():
                    logger.error(f"File not found: {file_path}")
                    continue

                # Extract text content
                content = await extract_text_from_file(doc.file_path, doc.file_type)

                if not content or not content.strip():
                    logger.warning(f"No content extracted from {doc.filename}")
                    continue

                # Reprocess with semantic chunking
                chunks = await chunk_service.process_document(
                    db=db,
                    document_id=str(doc.id),
                    content=content,
                )

                logger.info(f"✓ Successfully reprocessed {doc.filename} - created {len(chunks)} chunks with metadata")

            except Exception as e:
                logger.error(f"✗ Failed to reprocess {doc.filename}: {e}", exc_info=True)
                continue

        logger.info("\n✓ Document reprocessing complete!")


if __name__ == "__main__":
    asyncio.run(reprocess_all_documents())
