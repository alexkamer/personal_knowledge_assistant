"""
Script to reformat existing document content through the LLM formatter.
"""
import asyncio
import logging
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.document import Document
from app.services.content_formatter_service import get_content_formatter_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def reformat_documents(limit: int = None):
    """
    Reformat existing documents that don't have markdown formatting.

    Args:
        limit: Maximum number of documents to process (None for all)
    """
    formatter = get_content_formatter_service()

    async with AsyncSessionLocal() as db:
        # Get documents from web sources that need reformatting
        query = select(Document).where(
            Document.source_url.isnot(None),
            ~Document.content.contains("```")  # Doesn't have code blocks
        ).order_by(Document.created_at.desc())

        if limit:
            query = query.limit(limit)

        result = await db.execute(query)
        documents = result.scalars().all()

        logger.info(f"Found {len(documents)} documents to reformat")

        for i, doc in enumerate(documents, 1):
            try:
                logger.info(f"[{i}/{len(documents)}] Reformatting: {doc.source_url}")

                # Format content
                formatted_content = await formatter.format_content(
                    raw_content=doc.content,
                    url=doc.source_url,
                    title=doc.filename,
                )

                # Update document
                doc.content = formatted_content
                await db.commit()

                logger.info(f"✓ Reformatted {doc.source_url}")

            except Exception as e:
                logger.error(f"✗ Failed to reformat {doc.source_url}: {e}")
                await db.rollback()

        logger.info(f"Completed reformatting {len(documents)} documents")


if __name__ == "__main__":
    import sys

    # Get limit from command line args
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 5

    logger.info(f"Reformatting up to {limit} documents...")
    asyncio.run(reformat_documents(limit=limit))
