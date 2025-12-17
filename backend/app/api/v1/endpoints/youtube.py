"""
YouTube video processing endpoints.
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.youtube_service import get_youtube_service
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
