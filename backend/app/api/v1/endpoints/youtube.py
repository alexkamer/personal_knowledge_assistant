"""
YouTube video processing endpoints.
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from app.services.youtube_service import get_youtube_service
from app.services.llm_service import LLMService, get_llm_service
from app.services.agent_service import get_agent_service
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
        prompt = f"""Analyze this YouTube video transcript and provide:

1. A comprehensive summary (2-3 paragraphs)
2. Key points and takeaways (list the most important points)
3. Main topics covered (categorize the content)

Transcript ({transcript_data['entry_count']} entries, {transcript_data['total_duration']:.1f}s):
{transcript_text}

Please structure your response as:
SUMMARY:
[Your summary here]

KEY POINTS:
- [Point 1]
- [Point 2]
...

TOPICS:
- [Topic 1]
- [Topic 2]
..."""

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
    sections = {
        "summary": "",
        "key_points": [],
        "topics": [],
    }

    current_section = None
    lines = response.strip().split("\n")

    for line in lines:
        line = line.strip()

        # Detect section headers
        if "SUMMARY:" in line.upper():
            current_section = "summary"
            continue
        elif "KEY POINTS:" in line.upper() or "KEY TAKEAWAYS:" in line.upper():
            current_section = "key_points"
            continue
        elif "TOPICS:" in line.upper() or "MAIN TOPICS:" in line.upper():
            current_section = "topics"
            continue

        # Skip empty lines
        if not line:
            continue

        # Add content to appropriate section
        if current_section == "summary":
            sections["summary"] += line + " "
        elif current_section == "key_points" and line.startswith(("-", "•", "*")):
            sections["key_points"].append(line.lstrip("-•* ").strip())
        elif current_section == "topics" and line.startswith(("-", "•", "*")):
            sections["topics"].append(line.lstrip("-•* ").strip())

    # Clean up summary
    sections["summary"] = sections["summary"].strip()

    # If parsing failed, return basic fallback
    if not sections["summary"]:
        sections["summary"] = response[:500] + "..." if len(response) > 500 else response

    return sections
