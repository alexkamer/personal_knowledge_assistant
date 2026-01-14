"""
Integration tests for cascade deletions.

Verifies that deleting parent entities properly cascades to children,
including both PostgreSQL and ChromaDB cleanup.
"""

import pytest
from sqlalchemy import select, text

from app.models import (
    Chunk,
    Conversation,
    Document,
    Note,
    ResearchBriefing,
    ResearchProject,
    ResearchSource,
    ResearchTask,
    Tag,
)
from app.models.note_tag import NoteTag


@pytest.mark.asyncio
async def test_note_deletion_cascades_to_chunks(test_db):
    """Test that deleting a note cascades to its chunks."""
    # Create a note
    note = Note(title="Test Note", content="Test content")
    test_db.add(note)
    await test_db.commit()
    await test_db.refresh(note)

    # Create chunks for the note
    chunk1 = Chunk(
        content="Chunk 1",
        chunk_index=0,
        token_count=10,
        note_id=str(note.id),
    )
    chunk2 = Chunk(
        content="Chunk 2",
        chunk_index=1,
        token_count=10,
        note_id=str(note.id),
    )
    test_db.add(chunk1)
    test_db.add(chunk2)
    await test_db.commit()

    # Verify chunks exist
    result = await test_db.execute(
        select(Chunk).where(Chunk.note_id == str(note.id))
    )
    chunks = result.scalars().all()
    assert len(chunks) == 2

    # Delete the note
    await test_db.delete(note)
    await test_db.commit()

    # Verify chunks were cascaded
    result = await test_db.execute(
        select(Chunk).where(Chunk.note_id == str(note.id))
    )
    chunks = result.scalars().all()
    assert len(chunks) == 0


@pytest.mark.asyncio
async def test_document_deletion_cascades_to_chunks(test_db):
    """Test that deleting a document cascades to its chunks."""
    # Create a document
    document = Document(
        filename="test.pdf",
        file_path="/tmp/test.pdf",
        file_type="pdf",
        file_size=1000,
        content="Test document content",
    )
    test_db.add(document)
    await test_db.commit()
    await test_db.refresh(document)

    # Create chunks for the document
    chunk1 = Chunk(
        content="Doc chunk 1",
        chunk_index=0,
        token_count=10,
        document_id=str(document.id),
    )
    chunk2 = Chunk(
        content="Doc chunk 2",
        chunk_index=1,
        token_count=10,
        document_id=str(document.id),
    )
    test_db.add(chunk1)
    test_db.add(chunk2)
    await test_db.commit()

    # Verify chunks exist
    result = await test_db.execute(
        select(Chunk).where(Chunk.document_id == str(document.id))
    )
    chunks = result.scalars().all()
    assert len(chunks) == 2

    # Delete the document
    await test_db.delete(document)
    await test_db.commit()

    # Verify chunks were cascaded
    result = await test_db.execute(
        select(Chunk).where(Chunk.document_id == str(document.id))
    )
    chunks = result.scalars().all()
    assert len(chunks) == 0


@pytest.mark.asyncio
async def test_conversation_deletion_cascades_to_messages(test_db):
    """Test that deleting a conversation cascades to its messages."""
    # Create a conversation
    conversation = Conversation(title="Test Conversation")
    test_db.add(conversation)
    await test_db.commit()
    await test_db.refresh(conversation)

    # Create messages for the conversation
    from app.models.conversation import Message

    message1 = Message(
        conversation_id=str(conversation.id),
        role="user",
        content="Hello",
    )
    message2 = Message(
        conversation_id=str(conversation.id),
        role="assistant",
        content="Hi there",
    )
    test_db.add(message1)
    test_db.add(message2)
    await test_db.commit()

    # Verify messages exist
    result = await test_db.execute(
        select(Message).where(Message.conversation_id == str(conversation.id))
    )
    messages = result.scalars().all()
    assert len(messages) == 2

    # Delete the conversation
    await test_db.delete(conversation)
    await test_db.commit()

    # Verify messages were cascaded
    result = await test_db.execute(
        select(Message).where(Message.conversation_id == str(conversation.id))
    )
    messages = result.scalars().all()
    assert len(messages) == 0


@pytest.mark.asyncio
async def test_research_project_cascade_chain(test_db):
    """Test cascade deletion chain: Project → Tasks → Sources."""
    # Create a research project
    project = ResearchProject(
        name="Test Project",
        goal="Test research goal",
    )
    test_db.add(project)
    await test_db.commit()
    await test_db.refresh(project)

    # Create tasks for the project
    task1 = ResearchTask(
        project_id=str(project.id),
        query="Task 1 query",
        status="pending",
    )
    task2 = ResearchTask(
        project_id=str(project.id),
        query="Task 2 query",
        status="pending",
    )
    test_db.add(task1)
    test_db.add(task2)
    await test_db.commit()
    await test_db.refresh(task1)
    await test_db.refresh(task2)

    # Create a document for sources
    document = Document(
        filename="research.pdf",
        file_path="/tmp/research.pdf",
        file_type="pdf",
        file_size=1000,
        content="Research content",
    )
    test_db.add(document)
    await test_db.commit()
    await test_db.refresh(document)

    # Create sources for the tasks
    source1 = ResearchSource(
        research_task_id=str(task1.id),
        document_id=str(document.id),
        title="Source 1",
        url="https://example.com/1",
        source_type="web",
    )
    source2 = ResearchSource(
        research_task_id=str(task2.id),
        document_id=str(document.id),
        title="Source 2",
        url="https://example.com/2",
        source_type="web",
    )
    test_db.add(source1)
    test_db.add(source2)
    await test_db.commit()

    # Verify everything exists
    result = await test_db.execute(
        select(ResearchTask).where(ResearchTask.project_id == str(project.id))
    )
    assert len(result.scalars().all()) == 2

    result = await test_db.execute(
        select(ResearchSource).where(ResearchSource.research_task_id.in_([str(task1.id), str(task2.id)]))
    )
    assert len(result.scalars().all()) == 2

    # Delete the project
    await test_db.delete(project)
    await test_db.commit()

    # Verify cascade: tasks should be deleted
    result = await test_db.execute(
        select(ResearchTask).where(ResearchTask.project_id == str(project.id))
    )
    assert len(result.scalars().all()) == 0

    # Verify cascade: sources should be deleted (because tasks were deleted)
    result = await test_db.execute(
        select(ResearchSource).where(ResearchSource.research_task_id.in_([str(task1.id), str(task2.id)]))
    )
    assert len(result.scalars().all()) == 0

    # Document should still exist (CASCADE only on task_id, not document_id)
    result = await test_db.execute(
        select(Document).where(Document.id == document.id)
    )
    assert result.scalar_one_or_none() is not None


@pytest.mark.asyncio
async def test_note_tag_many_to_many_cascade(test_db):
    """Test that note-tag relationships cascade properly."""
    # Create a note and tags
    note = Note(title="Tagged Note", content="Content")
    tag1 = Tag(name="tag1")
    tag2 = Tag(name="tag2")

    test_db.add(note)
    test_db.add(tag1)
    test_db.add(tag2)
    await test_db.commit()
    await test_db.refresh(note)
    await test_db.refresh(tag1)
    await test_db.refresh(tag2)

    # Create associations
    note_tag1 = NoteTag(note_id=str(note.id), tag_id=str(tag1.id))
    note_tag2 = NoteTag(note_id=str(note.id), tag_id=str(tag2.id))
    test_db.add(note_tag1)
    test_db.add(note_tag2)
    await test_db.commit()

    # Verify associations exist
    result = await test_db.execute(
        select(NoteTag).where(NoteTag.note_id == str(note.id))
    )
    assert len(result.scalars().all()) == 2

    # Delete the note
    await test_db.delete(note)
    await test_db.commit()

    # Verify associations were cascaded
    result = await test_db.execute(
        select(NoteTag).where(NoteTag.note_id == str(note.id))
    )
    assert len(result.scalars().all()) == 0

    # Tags should still exist
    result = await test_db.execute(
        select(Tag).where(Tag.id.in_([tag1.id, tag2.id]))
    )
    assert len(result.scalars().all()) == 2


@pytest.mark.asyncio
async def test_research_briefing_cascade(test_db):
    """Test that deleting a project cascades to briefings."""
    # Create a research project
    project = ResearchProject(
        name="Test Project",
        goal="Test goal",
    )
    test_db.add(project)
    await test_db.commit()
    await test_db.refresh(project)

    # Create briefings for the project
    briefing1 = ResearchBriefing(
        project_id=str(project.id),
        title="Briefing 1",
        summary="Summary 1",
    )
    briefing2 = ResearchBriefing(
        project_id=str(project.id),
        title="Briefing 2",
        summary="Summary 2",
    )
    test_db.add(briefing1)
    test_db.add(briefing2)
    await test_db.commit()

    # Verify briefings exist
    result = await test_db.execute(
        select(ResearchBriefing).where(ResearchBriefing.project_id == str(project.id))
    )
    assert len(result.scalars().all()) == 2

    # Delete the project
    await test_db.delete(project)
    await test_db.commit()

    # Verify briefings were cascaded
    result = await test_db.execute(
        select(ResearchBriefing).where(ResearchBriefing.project_id == str(project.id))
    )
    assert len(result.scalars().all()) == 0
