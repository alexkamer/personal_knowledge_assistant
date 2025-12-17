"""
YouTube video processing endpoints.
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.youtube_service import get_youtube_service
from app.services.llm_service import LLMService, get_llm_service
from app.services.agent_service import get_agent_service
from app.services.youtube_ingestion_service import get_youtube_ingestion_service
from youtube_transcript_api._errors import (
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["youtube"])


# Request/Response models
class YouTubeURLRequest(BaseModel):
    """Request to process a YouTube URL."""

    url: str = Field(..., description="YouTube video URL or ID")
    languages: Optional[List[str]] = Field(
        default=None,
        description="Preferred languages (default: ['en'])",
    )


class TranscriptEntry(BaseModel):
    """Single transcript entry."""

    text: str
    start: float
    duration: float


class TranscriptResponse(BaseModel):
    """YouTube transcript response."""

    video_id: str
    language: str
    is_generated: bool
    is_translatable: bool
    transcript: List[TranscriptEntry]
    total_duration: float
    entry_count: int


class TranscriptSearchRequest(BaseModel):
    """Request to search transcript."""

    video_id: str
    query: str
    context_entries: int = Field(default=2, ge=0, le=10)


class TranscriptSearchResult(BaseModel):
    """Search result in transcript."""

    match_index: int
    match_text: str
    timestamp: float
    context: List[TranscriptEntry]


class TranscriptSearchResponse(BaseModel):
    """Transcript search response."""

    results: List[TranscriptSearchResult]
    total_matches: int


@router.post("/transcript", response_model=TranscriptResponse)
async def get_transcript(request: YouTubeURLRequest):
    """
    Get transcript for a YouTube video.

    Extracts the transcript/subtitles from a YouTube video. Supports:
    - Manually created transcripts (more accurate)
    - Auto-generated transcripts
    - Translation to preferred language

    Args:
        request: YouTube URL or video ID with optional language preferences

    Returns:
        Transcript data with metadata

    Raises:
        HTTPException: If video not found, transcript unavailable, or invalid URL
    """
    youtube_service = get_youtube_service()

    try:
        # Extract video ID
        video_id = youtube_service.extract_video_id(request.url)
        if not video_id:
            raise HTTPException(
                status_code=400,
                detail="Invalid YouTube URL or video ID",
            )

        # Fetch transcript
        transcript_data = youtube_service.get_transcript(
            video_id=video_id,
            languages=request.languages,
        )

        return transcript_data

    except NoTranscriptFound:
        raise HTTPException(
            status_code=404,
            detail=f"No transcript found for video {video_id}",
        )
    except TranscriptsDisabled:
        raise HTTPException(
            status_code=403,
            detail=f"Transcripts are disabled for video {video_id}",
        )
    except VideoUnavailable:
        raise HTTPException(
            status_code=404,
            detail=f"Video {video_id} is unavailable or doesn't exist",
        )
    except Exception as e:
        logger.error(f"Error fetching transcript: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch transcript: {str(e)}",
        )


@router.post("/transcript/search", response_model=TranscriptSearchResponse)
async def search_transcript(request: TranscriptSearchRequest):
    """
    Search for text within a video's transcript.

    Args:
        request: Video ID, search query, and context settings

    Returns:
        Matching transcript entries with surrounding context

    Raises:
        HTTPException: If transcript cannot be fetched
    """
    youtube_service = get_youtube_service()

    try:
        # First, fetch the transcript
        transcript_data = youtube_service.get_transcript(video_id=request.video_id)

        # Search within the transcript
        search_results = youtube_service.search_transcript(
            transcript_data=transcript_data["transcript"],
            query=request.query,
            context_entries=request.context_entries,
        )

        return {
            "results": search_results,
            "total_matches": len(search_results),
        }

    except (NoTranscriptFound, TranscriptsDisabled, VideoUnavailable) as e:
        raise HTTPException(
            status_code=404,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error searching transcript: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to search transcript: {str(e)}",
        )


@router.get("/extract-id/{url:path}")
async def extract_video_id(url: str):
    """
    Extract video ID from a YouTube URL.

    Args:
        url: YouTube URL

    Returns:
        Extracted video ID

    Raises:
        HTTPException: If URL is invalid
    """
    youtube_service = get_youtube_service()

    video_id = youtube_service.extract_video_id(url)
    if not video_id:
        raise HTTPException(
            status_code=400,
            detail="Invalid YouTube URL",
        )

    return {"video_id": video_id, "url": url}


class VideoMetadataResponse(BaseModel):
    """Video metadata response."""

    video_id: str
    title: str
    channel: str
    channel_id: str
    view_count: int
    duration: int
    upload_date: str
    thumbnail: str
    description: str


class VideoIngestRequest(BaseModel):
    """Request to ingest a YouTube video into the knowledge base."""

    url: str = Field(..., description="YouTube video URL or ID")
    languages: Optional[List[str]] = Field(
        default=None,
        description="Preferred languages (default: ['en'])",
    )


class VideoIngestResponse(BaseModel):
    """Response after ingesting a YouTube video."""

    id: str
    video_id: str
    title: str
    channel: Optional[str]
    duration: Optional[int]
    transcript_language: Optional[str]
    is_generated: bool
    chunk_count: int


@router.post("/ingest", response_model=VideoIngestResponse)
async def ingest_video(
    request: VideoIngestRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Ingest a YouTube video into the knowledge base.

    This endpoint:
    1. Fetches video metadata and transcript
    2. Creates a YouTubeVideo record in the database
    3. Chunks the transcript (with timestamps preserved)
    4. Generates embeddings for each chunk
    5. Stores chunks in both PostgreSQL and ChromaDB

    Once ingested, the video becomes searchable via the RAG pipeline
    alongside notes and documents.

    Args:
        request: YouTube URL or video ID with optional language preferences
        db: Database session

    Returns:
        Ingested video metadata and chunk count

    Raises:
        HTTPException: If video is invalid, transcript unavailable, or ingestion fails
    """
    ingestion_service = get_youtube_ingestion_service()

    try:
        youtube_video = await ingestion_service.ingest_video(
            db=db,
            video_url=request.url,
            languages=request.languages,
        )

        # Count chunks for the response
        from sqlalchemy import select, func
        from app.models.chunk import Chunk

        result = await db.execute(
            select(func.count(Chunk.id)).where(
                Chunk.youtube_video_id == youtube_video.id
            )
        )
        chunk_count = result.scalar_one()

        return VideoIngestResponse(
            id=str(youtube_video.id),
            video_id=youtube_video.video_id,
            title=youtube_video.title,
            channel=youtube_video.channel,
            duration=youtube_video.duration,
            transcript_language=youtube_video.transcript_language,
            is_generated=youtube_video.is_generated,
            chunk_count=chunk_count,
        )

    except ValueError as e:
        # Invalid URL
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )
    except NoTranscriptFound:
        raise HTTPException(
            status_code=404,
            detail="No transcript found for this video",
        )
    except TranscriptsDisabled:
        raise HTTPException(
            status_code=403,
            detail="Transcripts are disabled for this video",
        )
    except VideoUnavailable:
        raise HTTPException(
            status_code=404,
            detail="Video is unavailable or doesn't exist",
        )
    except Exception as e:
        logger.error(f"Error ingesting video: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to ingest video: {str(e)}",
        )


@router.get("/metadata/{video_id}", response_model=VideoMetadataResponse)
async def get_video_metadata(video_id: str):
    """
    Get metadata for a YouTube video.

    Args:
        video_id: YouTube video ID

    Returns:
        Video metadata including title, channel, views, etc.

    Raises:
        HTTPException: If metadata cannot be fetched
    """
    youtube_service = get_youtube_service()

    try:
        metadata = youtube_service.get_video_metadata(video_id)
        return metadata

    except Exception as e:
        logger.error(f"Error fetching video metadata: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch video metadata: {str(e)}",
        )


class VideoSummarizeRequest(BaseModel):
    """Request to summarize a YouTube video."""

    video_id: str = Field(..., description="YouTube video ID")
    languages: Optional[List[str]] = Field(
        default=None,
        description="Preferred languages (default: ['en'])",
    )


class VideoSummarizeResponse(BaseModel):
    """Video summary response."""

    video_id: str
    summary: str
    key_points: List[str]
    topics: List[str]


@router.post("/summarize", response_model=VideoSummarizeResponse)
async def summarize_video(
    request: VideoSummarizeRequest,
    llm_service: LLMService = Depends(get_llm_service),
):
    """
    Generate an AI summary of a YouTube video.

    Uses the @summarize agent to analyze the video transcript and extract:
    - Overall summary
    - Key points and takeaways
    - Main topics covered

    Args:
        request: Video ID and language preferences
        llm_service: LLM service dependency

    Returns:
        Structured summary with key points and topics

    Raises:
        HTTPException: If video not found or transcript unavailable
    """
    youtube_service = get_youtube_service()
    agent_service = get_agent_service()

    try:
        # Fetch transcript
        transcript_data = youtube_service.get_transcript(
            video_id=request.video_id,
            languages=request.languages,
        )

        # Format transcript as text for the LLM
        transcript_text = youtube_service.format_transcript_as_text(
            transcript_data["transcript"]
        )

        # Get @summarize agent config
        summarize_agent = agent_service.get_agent("summarize")

        # Build summarization prompt
        prompt = f"""Analyze this YouTube video transcript and provide a structured summary.

Transcript ({transcript_data['entry_count']} entries, {transcript_data['total_duration']:.1f}s):
{transcript_text}

Please provide your response in exactly this format (without markdown formatting):

SUMMARY:
Write a clear 2-3 paragraph summary of the video content.

KEY POINTS:
- First key point or takeaway
- Second key point or takeaway
- Third key point or takeaway
(list 3-6 most important points)

TOPICS:
- First main topic
- Second main topic
- Third main topic
(list 2-5 main topics covered)

Important: Do not use markdown bold (**) or other formatting. Keep it plain text."""

        # Generate summary using @summarize agent
        summary_response = await llm_service.generate_answer(
            query=prompt,
            context="",  # No RAG context needed - transcript is in prompt
            conversation_history=[],
            model=summarize_agent.model,
            temperature=summarize_agent.temperature,
            system_prompt=summarize_agent.system_prompt,
        )

        # Parse the structured response
        parsed = _parse_summary_response(summary_response)

        return {
            "video_id": request.video_id,
            "summary": parsed["summary"],
            "key_points": parsed["key_points"],
            "topics": parsed["topics"],
        }

    except (NoTranscriptFound, TranscriptsDisabled, VideoUnavailable) as e:
        raise HTTPException(
            status_code=404,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error summarizing video: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to summarize video: {str(e)}",
        )


def _parse_summary_response(response: str) -> dict:
    """
    Parse the structured summary response from the LLM.

    Args:
        response: Raw LLM response

    Returns:
        Dict with summary, key_points, and topics
    """
    # Remove markdown formatting
    response = response.replace("**", "")

    sections = {
        "summary": "",
        "key_points": [],
        "topics": [],
    }

    current_section = None
    lines = response.strip().split("\n")

    for line in lines:
        line = line.strip()

        # Skip empty lines
        if not line:
            continue

        # Detect section headers (case insensitive)
        line_upper = line.upper()
        if "SUMMARY" in line_upper and ":" in line:
            current_section = "summary"
            # Check if there's content after the colon on the same line
            if ":" in line:
                content_after = line.split(":", 1)[1].strip()
                if content_after:
                    sections["summary"] += content_after + " "
            continue
        elif ("KEY POINTS" in line_upper or "KEY TAKEAWAYS" in line_upper) and ":" in line:
            current_section = "key_points"
            continue
        elif ("TOPICS" in line_upper or "MAIN TOPICS" in line_upper) and ":" in line:
            current_section = "topics"
            continue

        # Skip instructional text in parentheses
        if line.startswith("(") and line.endswith(")"):
            continue

        # Add content to appropriate section
        if current_section == "summary":
            sections["summary"] += line + " "
        elif current_section == "key_points":
            # Handle both bulleted and numbered points
            if line.startswith(("-", "•", "*", "1.", "2.", "3.", "4.", "5.", "6.")):
                # Remove bullet prefix first
                clean_line = line.lstrip("-•* ")
                # Remove numbered list prefix (e.g., "1. " or "1) ") only at the start
                # Match pattern: digit(s) followed by . or ) at the beginning
                if clean_line and clean_line[0].isdigit():
                    # Find the first non-digit character
                    i = 0
                    while i < len(clean_line) and clean_line[i].isdigit():
                        i += 1
                    # Check if it's followed by ". " or ") "
                    if i < len(clean_line) and clean_line[i] in ".)" and i + 1 < len(clean_line) and clean_line[i + 1] == " ":
                        clean_line = clean_line[i + 2:].strip()
                if clean_line:
                    sections["key_points"].append(clean_line)
        elif current_section == "topics":
            # Handle both bulleted and numbered topics
            if line.startswith(("-", "•", "*", "1.", "2.", "3.", "4.", "5.", "6.")):
                # Remove bullet prefix first
                clean_line = line.lstrip("-•* ")
                # Remove numbered list prefix (e.g., "1. " or "1) ") only at the start
                # Match pattern: digit(s) followed by . or ) at the beginning
                if clean_line and clean_line[0].isdigit():
                    # Find the first non-digit character
                    i = 0
                    while i < len(clean_line) and clean_line[i].isdigit():
                        i += 1
                    # Check if it's followed by ". " or ") "
                    if i < len(clean_line) and clean_line[i] in ".)" and i + 1 < len(clean_line) and clean_line[i + 1] == " ":
                        clean_line = clean_line[i + 2:].strip()
                if clean_line:
                    sections["topics"].append(clean_line)

    # Clean up summary (remove extra spaces)
    sections["summary"] = " ".join(sections["summary"].split())

    # If parsing failed, return basic fallback
    if not sections["summary"]:
        # Try to extract first few paragraphs
        paragraphs = [p.strip() for p in response.split("\n\n") if p.strip()]
        if paragraphs:
            sections["summary"] = paragraphs[0][:1000]
        else:
            sections["summary"] = response[:500] + "..." if len(response) > 500 else response

    return sections
