"""
Pytest configuration and fixtures for tests.
"""
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.models.base import Base
# Import all models so SQLAlchemy knows about them
from app.models.conversation import Conversation, Message
from app.models.note import Note
from app.models.document import Document
from app.models.chunk import Chunk
from app.models.tag import Tag
from app.models.note_tag import NoteTag
from app.models.message_feedback import MessageFeedback


# Use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def db_session():
    """
    Create a fresh database session for each test.
    Uses in-memory SQLite database for fast tests.
    """
    # Create async engine with StaticPool to share connection in memory
    from sqlalchemy.pool import StaticPool

    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=StaticPool,  # Use StaticPool to share connection
        connect_args={"check_same_thread": False},
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session factory
    async_session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # Create and yield session
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()
