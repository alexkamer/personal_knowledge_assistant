"""
YouTube video ingestion service.

Handles ingesting YouTube videos into the knowledge base by:
1. Fetching video metadata and transcripts
2. Creating YouTubeVideo records
3. Chunking transcripts with timestamps
4. Generating embeddings
5. Storing in both PostgreSQL and ChromaDB
"""
import logging
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chunk import Chunk
from app.models.youtube_video import YouTubeVideo
from app.services.embedding_service import get_embedding_service
from app.services.vector_service import get_vector_service
from app.services.youtube_service import YouTubeService, get_youtube_service
from app.utils.semantic_chunker import SemanticChunker
from youtube_transcript_api._errors import (
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
)

logger = logging.getLogger(__name__)


class YouTubeIngestionService:
    """Service for ingesting YouTube videos into the knowledge base."""

    def __init__(self):
        """Initialize the ingestion service."""
        self.youtube_service = get_youtube_service()
        self.embedding_service = get_embedding_service()
        self.vector_service = get_vector_service()
        self.semantic_chunker = SemanticChunker(
            min_chunk_size=256,
            max_chunk_size=768,
        )

    async def ingest_video(
        self,
        db: AsyncSession,
        video_url: str,
        languages: Optional[List[str]] = None,
    ) -> YouTubeVideo:
        """
        Ingest a YouTube video into the knowledge base.

        Steps:
        1. Extract video ID from URL
        2. Check if video already exists
        3. Fetch video metadata
        4. Fetch transcript
        5. Create YouTubeVideo record
        6. Chunk transcript with timestamps
        7. Generate embeddings
        8. Store chunks in DB and ChromaDB

        Args:
            db: Database session
            video_url: YouTube video URL
            languages: Preferred transcript languages (default: ['en'])

        Returns:
            YouTubeVideo object

        Raises:
            ValueError: If video ID cannot be extracted
            NoTranscriptFound: If no transcript is available
            TranscriptsDisabled: If transcripts are disabled
            VideoUnavailable: If video doesn't exist
        """
        # Extract video ID
        video_id = self.youtube_service.extract_video_id(video_url)
        if not video_id:
            raise ValueError(f"Could not extract video ID from URL: {video_url}")

        logger.info(f"Starting ingestion for video {video_id}")

        # Check if video already exists
        result = await db.execute(
            select(YouTubeVideo).where(YouTubeVideo.video_id == video_id)
        )
        existing_video = result.scalar_one_or_none()

        if existing_video:
            logger.info(f"Video {video_id} already exists, re-processing")
            # Delete existing chunks
            await self._delete_existing_chunks(db, str(existing_video.id))
            youtube_video = existing_video
        else:
            # Fetch video metadata
            try:
                metadata = self.youtube_service.get_video_metadata(video_id)
            except Exception as e:
                logger.error(f"Failed to fetch metadata for {video_id}: {e}")
                raise

            # Create YouTubeVideo record (without transcript metadata yet)
            youtube_video = YouTubeVideo(
                video_id=video_id,
                title=metadata["title"],
                channel=metadata["channel"],
                channel_id=metadata["channel_id"],
                duration=metadata["duration"],
                upload_date=metadata["upload_date"],
                thumbnail=metadata["thumbnail"],
                description=metadata["description"],
                view_count=metadata["view_count"],
                transcript_language=None,  # Will update after fetching transcript
                is_generated=False,
            )
            db.add(youtube_video)
            await db.commit()
            await db.refresh(youtube_video)

        # Fetch transcript
        try:
            transcript_data = self.youtube_service.get_transcript(
                video_id, languages=languages
            )
        except (NoTranscriptFound, TranscriptsDisabled, VideoUnavailable) as e:
            # If video record was just created, delete it
            if not existing_video:
                await db.delete(youtube_video)
                await db.commit()
            logger.error(f"Failed to fetch transcript for {video_id}: {e}")
            raise

        # Update transcript metadata
        youtube_video.transcript_language = transcript_data["language"]
        youtube_video.is_generated = transcript_data["is_generated"]
        await db.commit()

        # Chunk transcript with timestamps
        transcript_entries = transcript_data["transcript"]
        chunks = await self._chunk_and_embed_transcript(
            db, str(youtube_video.id), video_id, transcript_entries
        )

        logger.info(
            f"Successfully ingested video {video_id} with {len(chunks)} chunks"
        )
        return youtube_video

    async def _chunk_and_embed_transcript(
        self,
        db: AsyncSession,
        youtube_video_id: str,
        video_id: str,
        transcript_entries: List[dict],
    ) -> List[Chunk]:
        """
        Chunk transcript and generate embeddings.

        Strategy:
        - Combine transcript entries into full text
        - Use semantic chunker to create chunks
        - Track timestamps: each chunk gets start timestamp of first entry it contains
        - Generate embeddings for all chunks
        - Store in PostgreSQL and ChromaDB

        Args:
            db: Database session
            youtube_video_id: UUID of the YouTubeVideo record
            video_id: YouTube video ID (for logging)
            transcript_entries: List of transcript entries with text, start, duration

        Returns:
            List of created Chunk objects
        """
        if not transcript_entries:
            logger.warning(f"No transcript entries for video {video_id}")
            return []

        # Format transcript as text with timestamp markers
        # We'll use a special marker format that the chunker will preserve
        full_text_with_markers = []
        timestamp_map = {}  # Maps character position to timestamp

        current_pos = 0
        for entry in transcript_entries:
            text = entry["text"].strip()
            timestamp = entry["start"]

            # Add timestamp marker
            marker = f"[TS:{timestamp:.2f}]"
            full_text_with_markers.append(marker)
            timestamp_map[current_pos] = timestamp
            current_pos += len(marker)

            # Add text
            full_text_with_markers.append(text)
            full_text_with_markers.append("\n")
            current_pos += len(text) + 1

        full_text = "".join(full_text_with_markers)

        # Chunk the text using semantic chunker
        semantic_chunks = self.semantic_chunker.split_text(full_text)

        if not semantic_chunks:
            logger.warning(f"No chunks generated for video {video_id}")
            return []

        logger.info(f"Generated {len(semantic_chunks)} chunks for video {video_id}")

        # Process each chunk: extract text, find timestamp, embed
        chunk_texts = []
        chunk_timestamps = []

        for semantic_chunk in semantic_chunks:
            content = semantic_chunk.content

            # Extract timestamp from chunk (find first [TS:X.XX] marker)
            import re

            timestamp_match = re.search(r"\[TS:([\d.]+)\]", content)
            if timestamp_match:
                timestamp = float(timestamp_match.group(1))
                chunk_timestamps.append(timestamp)
            else:
                # If no timestamp found, use 0.0 (shouldn't happen)
                chunk_timestamps.append(0.0)

            # Remove timestamp markers from content
            clean_content = re.sub(r"\[TS:[\d.]+\]", "", content).strip()
            chunk_texts.append(clean_content)

        # Generate embeddings for all chunks
        embeddings = self.embedding_service.embed_batch(chunk_texts)

        # Create chunk records in database
        chunks = []
        for idx, (semantic_chunk, clean_text, timestamp, embedding) in enumerate(
            zip(semantic_chunks, chunk_texts, chunk_timestamps, embeddings)
        ):
            chunk = Chunk(
                note_id=None,
                document_id=None,
                youtube_video_id=youtube_video_id,
                content=clean_text,
                chunk_index=idx,
                token_count=semantic_chunk.metadata.token_count,
                content_type=semantic_chunk.metadata.content_type,
                heading_hierarchy={
                    "hierarchy": semantic_chunk.metadata.heading_hierarchy,
                    "timestamp": timestamp,  # Store timestamp in heading_hierarchy
                },
                section_title=semantic_chunk.metadata.section_title,
                has_code=semantic_chunk.metadata.has_code,
                semantic_density=semantic_chunk.metadata.semantic_density,
            )
            db.add(chunk)
            chunks.append(chunk)

        await db.commit()

        # Refresh to get IDs
        for chunk in chunks:
            await db.refresh(chunk)

        # Store embeddings in vector database
        chunk_ids = [str(chunk.id) for chunk in chunks]
        metadatas = []
        for chunk, timestamp in zip(chunks, chunk_timestamps):
            metadata = {
                "source_id": youtube_video_id,
                "source_type": "youtube",
                "chunk_index": chunk.chunk_index,
                "token_count": chunk.token_count,
                "timestamp": timestamp,  # Add timestamp to ChromaDB metadata
            }
            # Only add optional fields if they have non-None values
            if chunk.content_type is not None:
                metadata["content_type"] = chunk.content_type
            if chunk.section_title is not None:
                metadata["section_title"] = chunk.section_title
            if chunk.has_code is not None:
                metadata["has_code"] = chunk.has_code
            if chunk.semantic_density is not None:
                metadata["semantic_density"] = chunk.semantic_density
            metadatas.append(metadata)

        await self.vector_service.add_batch_embeddings(
            chunk_ids=chunk_ids,
            embeddings=embeddings,
            chunk_texts=chunk_texts,
            metadatas=metadatas,
        )

        logger.info(
            f"Successfully created {len(chunks)} chunks for video {video_id}"
        )
        return chunks

    async def _delete_existing_chunks(
        self,
        db: AsyncSession,
        youtube_video_id: str,
    ) -> None:
        """
        Delete existing chunks for a YouTube video from both database and vector store.

        Args:
            db: Database session
            youtube_video_id: UUID of the YouTubeVideo record
        """
        # Find existing chunks in database
        result = await db.execute(
            select(Chunk).where(Chunk.youtube_video_id == youtube_video_id)
        )
        existing_chunks = list(result.scalars().all())

        if not existing_chunks:
            return

        logger.info(
            f"Deleting {len(existing_chunks)} existing chunks for video {youtube_video_id}"
        )

        # Delete from vector database
        await self.vector_service.delete_chunks_by_source(
            youtube_video_id, "youtube"
        )

        # Delete from PostgreSQL
        for chunk in existing_chunks:
            await db.delete(chunk)

        await db.commit()


# Global instance
_youtube_ingestion_service: Optional[YouTubeIngestionService] = None


def get_youtube_ingestion_service() -> YouTubeIngestionService:
    """
    Get the global YouTube ingestion service instance.

    Returns:
        YouTubeIngestionService singleton
    """
    global _youtube_ingestion_service
    if _youtube_ingestion_service is None:
        _youtube_ingestion_service = YouTubeIngestionService()
    return _youtube_ingestion_service
