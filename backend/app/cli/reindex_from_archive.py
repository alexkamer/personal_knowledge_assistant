"""
CLI command to re-index documents from archive.

This script allows you to rebuild embeddings for archived documents.
Useful when:
- Upgrading embedding models
- Changing chunking strategy
- Recovering from corrupted ChromaDB
- Testing different RAG configurations

Usage:
    python -m app.cli.reindex_from_archive [--document-id ID] [--all] [--dry-run]

Examples:
    # Re-index all documents
    python -m app.cli.reindex_from_archive --all

    # Re-index specific document
    python -m app.cli.reindex_from_archive --document-id abc-123-def

    # Dry run to see what would be re-indexed
    python -m app.cli.reindex_from_archive --all --dry-run
"""
import asyncio
import argparse
import logging
from pathlib import Path
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.document import Document
from app.services.archive_service import ArchiveService
from app.services.embedding_service import EmbeddingService
from app.services.chunking_service import ChunkingService
from app.core.vector_db import vector_db

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class ReindexCommand:
    """Command to re-index documents from archive."""

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.embedding_service = EmbeddingService()
        self.chunking_service = ChunkingService()

    async def reindex_document(
        self,
        db: AsyncSession,
        document: Document,
    ) -> bool:
        """
        Re-index a single document from archive.

        Args:
            db: Database session
            document: Document to re-index

        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Re-indexing document: {document.filename} (ID: {document.id})")

        if self.dry_run:
            logger.info(f"[DRY RUN] Would re-index: {document.filename}")
            logger.info(f"  Storage location: {document.storage_location}")
            logger.info(f"  Archive path: {document.archive_path}")
            return True

        try:
            # Get content from archive or use existing content
            content = document.content

            if document.storage_location == "archive" and document.archive_path:
                logger.info(f"  Retrieving from archive: {document.archive_path}")
                # For now, use existing content from DB
                # In future, could re-extract from archived file if needed
                pass

            # Delete existing chunks from ChromaDB
            logger.info(f"  Deleting existing embeddings...")
            try:
                vector_db.delete_chunks_by_document(document.id)
            except Exception as e:
                logger.warning(f"  Failed to delete existing chunks: {e}")

            # Re-chunk the content
            logger.info(f"  Chunking content...")
            chunks = self.chunking_service.chunk_text(content)
            logger.info(f"  Created {len(chunks)} chunks")

            # Generate embeddings
            logger.info(f"  Generating embeddings...")
            embeddings = await self.embedding_service.embed_chunks(chunks)
            logger.info(f"  Generated {len(embeddings)} embeddings")

            # Store in ChromaDB
            logger.info(f"  Storing in ChromaDB...")
            chunk_ids = [f"{document.id}_{i}" for i in range(len(chunks))]
            metadatas = [
                {
                    "document_id": document.id,
                    "chunk_index": i,
                    "source_type": "document",
                    "filename": document.filename,
                    "file_type": document.file_type,
                }
                for i in range(len(chunks))
            ]

            vector_db.add_chunks(
                chunk_ids=chunk_ids,
                chunks=chunks,
                embeddings=embeddings,
                metadatas=metadatas,
            )

            logger.info(f"✓ Successfully re-indexed: {document.filename}")
            return True

        except Exception as e:
            logger.error(f"✗ Failed to re-index {document.filename}: {str(e)}")
            return False

    async def reindex_all_documents(self, db: AsyncSession) -> tuple[int, int]:
        """
        Re-index all documents.

        Args:
            db: Database session

        Returns:
            Tuple of (success_count, failure_count)
        """
        # Query all documents
        result = await db.execute(select(Document))
        documents = result.scalars().all()

        logger.info(f"Found {len(documents)} documents to re-index")

        success_count = 0
        failure_count = 0

        for doc in documents:
            success = await self.reindex_document(db, doc)
            if success:
                success_count += 1
            else:
                failure_count += 1

        return success_count, failure_count

    async def reindex_by_id(
        self,
        db: AsyncSession,
        document_id: str,
    ) -> bool:
        """
        Re-index a specific document by ID.

        Args:
            db: Database session
            document_id: Document ID to re-index

        Returns:
            True if successful, False otherwise
        """
        result = await db.execute(
            select(Document).where(Document.id == document_id)
        )
        document = result.scalar_one_or_none()

        if not document:
            logger.error(f"Document not found: {document_id}")
            return False

        return await self.reindex_document(db, document)


async def main():
    """Main CLI entrypoint."""
    parser = argparse.ArgumentParser(
        description="Re-index documents from archive",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--document-id",
        type=str,
        help="Re-index a specific document by ID",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Re-index all documents",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be re-indexed without actually doing it",
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.document_id and not args.all:
        parser.error("Must specify either --document-id or --all")

    if args.document_id and args.all:
        parser.error("Cannot specify both --document-id and --all")

    # Check archive availability
    if not args.dry_run:
        if ArchiveService.is_archive_available():
            logger.info("Archive drive is available")
        else:
            logger.warning("Archive drive is not available (will use local content)")

    # Initialize command
    command = ReindexCommand(dry_run=args.dry_run)

    # Execute
    async with AsyncSessionLocal() as db:
        if args.all:
            logger.info("=" * 60)
            logger.info("Re-indexing all documents")
            logger.info("=" * 60)

            success_count, failure_count = await command.reindex_all_documents(db)

            logger.info("=" * 60)
            logger.info("Re-indexing complete")
            logger.info(f"  Success: {success_count}")
            logger.info(f"  Failures: {failure_count}")
            logger.info("=" * 60)

        elif args.document_id:
            logger.info("=" * 60)
            logger.info(f"Re-indexing document: {args.document_id}")
            logger.info("=" * 60)

            success = await command.reindex_by_id(db, args.document_id)

            logger.info("=" * 60)
            if success:
                logger.info("✓ Re-indexing successful")
            else:
                logger.error("✗ Re-indexing failed")
            logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
