"""
Tests for chunk source constraint.

Verifies that chunks must have exactly one source (note_id, document_id, or youtube_video_id).
"""

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.models import Chunk, Note, Document


@pytest.mark.asyncio
async def test_chunk_must_have_one_source(test_db):
    """Test that chunks must have exactly one source."""
    # Test 1: Chunk with no source should fail
    chunk_no_source = Chunk(
        content="Test content",
        chunk_index=0,
        token_count=10,
        note_id=None,
        document_id=None,
        youtube_video_id=None,
    )
    test_db.add(chunk_no_source)

    with pytest.raises(IntegrityError) as exc_info:
        await test_db.flush()  # Force constraint check

    assert "chunk_has_one_source" in str(exc_info.value)
    await test_db.rollback()


@pytest.mark.asyncio
async def test_chunk_cannot_have_multiple_sources(test_db):
    """Test that chunks cannot have multiple sources."""
    # Create test note and document first
    test_note = Note(title="Test Note", content="Content")
    test_document = Document(
        filename="test.pdf",
        file_path="/tmp/test.pdf",
        file_type="pdf",
        file_size=100,
    )
    test_db.add(test_note)
    test_db.add(test_document)
    await test_db.commit()

    # Test 2: Chunk with two sources should fail
    chunk_two_sources = Chunk(
        content="Test content",
        chunk_index=0,
        token_count=10,
        note_id=str(test_note.id),
        document_id=str(test_document.id),
        youtube_video_id=None,
    )
    test_db.add(chunk_two_sources)

    with pytest.raises(IntegrityError) as exc_info:
        await test_db.flush()  # Force constraint check

    assert "chunk_has_one_source" in str(exc_info.value)
    await test_db.rollback()


@pytest.mark.asyncio
async def test_chunk_with_one_source_succeeds(test_db):
    """Test that chunks with exactly one source are allowed."""
    # Create test note first
    test_note = Note(title="Test Note", content="Content")
    test_db.add(test_note)
    await test_db.commit()

    # Test 3: Chunk with one source should succeed
    chunk_one_source = Chunk(
        content="Test content",
        chunk_index=0,
        token_count=10,
        note_id=str(test_note.id),
        document_id=None,
        youtube_video_id=None,
    )
    test_db.add(chunk_one_source)
    await test_db.commit()

    # Verify it was created
    result = await test_db.execute(text("SELECT COUNT(*) FROM chunks WHERE note_id = :note_id"), {"note_id": str(test_note.id)})
    count = result.scalar()
    assert count == 1
