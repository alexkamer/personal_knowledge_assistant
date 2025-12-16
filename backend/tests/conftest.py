"""
Pytest configuration and shared fixtures.
"""
import asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import Mock, AsyncMock

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app


# Test database URL (in-memory SQLite)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_engine():
    """Create a test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def test_db(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session


@pytest.fixture
async def client(test_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create a test HTTP client with database override."""
    from httpx import ASGITransport

    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


# Mock fixtures for external services

@pytest.fixture
def mock_embedding_service():
    """Mock embedding service."""
    mock = Mock()
    mock.embed_text.return_value = [0.1] * 384  # 384-dim embedding
    mock.embed_batch.return_value = [[0.1] * 384, [0.2] * 384]
    mock.get_embedding_dimension.return_value = 384
    return mock


@pytest.fixture
def mock_llm_service():
    """Mock LLM service."""
    mock = Mock()
    mock.generate_answer = AsyncMock(return_value="This is a test answer.")
    mock.generate_title = AsyncMock(return_value="Test Title")
    mock.generate_summary = AsyncMock(return_value="Test summary")
    mock.generate_followup_questions = AsyncMock(return_value=["Question 1?", "Question 2?"])
    return mock


@pytest.fixture
def mock_vector_db():
    """Mock ChromaDB vector database."""
    mock = Mock()
    mock.add_chunks = Mock()
    mock.search = Mock(return_value={
        "ids": [["chunk1", "chunk2"]],
        "distances": [[0.1, 0.2]],
        "documents": [["Test content 1", "Test content 2"]],
        "metadatas": [[
            {"source_type": "note", "source_id": "note1", "chunk_index": 0},
            {"source_type": "document", "source_id": "doc1", "chunk_index": 0}
        ]]
    })
    mock.delete_chunks = Mock()
    return mock


@pytest.fixture
def sample_note_data():
    """Sample note data for testing."""
    return {
        "title": "Test Note",
        "content": "This is a test note with some content.",
        "tags": ["test", "sample"],
    }


@pytest.fixture
def sample_document_data():
    """Sample document data for testing."""
    return {
        "filename": "test_document.pdf",
        "content": "This is test document content.",
        "file_size": 1024,
        "mime_type": "application/pdf",
    }


@pytest.fixture
def sample_conversation_data():
    """Sample conversation data for testing."""
    return {
        "title": "Test Conversation",
        "summary": "A test conversation about testing",
    }


@pytest.fixture
def sample_message_data():
    """Sample message data for testing."""
    return {
        "role": "user",
        "content": "What is testing?",
    }
