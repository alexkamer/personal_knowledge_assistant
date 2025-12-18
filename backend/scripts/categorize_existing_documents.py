"""
Script to categorize all existing documents in the database.
Run this after adding the categorization feature to backfill categories for existing documents.
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, func
from app.core.database import AsyncSessionLocal
from app.models.document import Document
from app.services.categorization_service import categorize_document


async def categorize_all_documents():
    """Categorize all documents that don't have a category assigned."""
    async with AsyncSessionLocal() as db:
        # Get all documents without a category
        result = await db.execute(
            select(Document).where(Document.category.is_(None))
        )
        documents = result.scalars().all()

        print(f"Found {len(documents)} documents without categories")

        if not documents:
            print("All documents already have categories!")
            return

        categorized_count = 0
        for doc in documents:
            try:
                # Read document content if available
                content = ""
                if doc.file_path and Path(doc.file_path).exists():
                    try:
                        with open(doc.file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                    except Exception as e:
                        print(f"Warning: Could not read content for {doc.filename}: {e}")

                # Categorize based on filename, content, and metadata
                category = categorize_document(
                    filename=doc.filename,
                    content=content,
                    metadata_json=doc.metadata_,
                    file_type=doc.file_type
                )

                doc.category = category
                categorized_count += 1

                if categorized_count % 10 == 0:
                    print(f"Categorized {categorized_count}/{len(documents)} documents...")

            except Exception as e:
                print(f"Error categorizing {doc.filename}: {e}")
                continue

        # Commit all changes
        await db.commit()
        print(f"\nSuccessfully categorized {categorized_count} documents!")

        # Show category distribution
        result = await db.execute(
            select(Document.category, func.count(Document.id))
            .group_by(Document.category)
            .order_by(func.count(Document.id).desc())
        )
        print("\nCategory distribution:")
        for category, count in result.all():
            print(f"  {category or 'Uncategorized'}: {count}")


if __name__ == "__main__":
    print("Starting document categorization...")
    asyncio.run(categorize_all_documents())
    print("Done!")
