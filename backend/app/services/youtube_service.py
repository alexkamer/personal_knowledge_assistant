"""
YouTube video processing service.

Handles transcript extraction, metadata fetching, and video processing.
"""
import logging
import os
import re
from typing import Dict, List, Optional
from urllib.parse import parse_qs, urlparse

import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
)

logger = logging.getLogger(__name__)

# Check if proxy credentials are configured
WEBSHARE_PROXY_USERNAME = os.getenv("WEBSHARE_PROXY_USERNAME")
WEBSHARE_PROXY_PASSWORD = os.getenv("WEBSHARE_PROXY_PASSWORD")


class YouTubeService:
    """Service for processing YouTube videos."""

    @staticmethod
    def extract_video_id(url: str) -> Optional[str]:
        """
        Extract YouTube video ID from various URL formats.

        Supports:
        - https://www.youtube.com/watch?v=VIDEO_ID
        - https://youtu.be/VIDEO_ID
        - https://www.youtube.com/embed/VIDEO_ID
        - https://m.youtube.com/watch?v=VIDEO_ID

        Args:
            url: YouTube video URL

        Returns:
            Video ID or None if invalid
        """
        # Pattern 1: youtube.com/watch?v=VIDEO_ID
        if "youtube.com/watch" in url:
            parsed = urlparse(url)
            query_params = parse_qs(parsed.query)
            video_id = query_params.get("v", [None])[0]
            if video_id:
                return video_id

        # Pattern 2: youtu.be/VIDEO_ID
        if "youtu.be/" in url:
            parsed = urlparse(url)
            video_id = parsed.path.lstrip("/")
            if video_id:
                return video_id

        # Pattern 3: youtube.com/embed/VIDEO_ID
        if "youtube.com/embed/" in url:
            parsed = urlparse(url)
            video_id = parsed.path.replace("/embed/", "")
            if video_id:
                return video_id

        # Pattern 4: Just the video ID
        if re.match(r'^[a-zA-Z0-9_-]{11}$', url):
            return url

        return None

    @staticmethod
    def get_transcript(
        video_id: str,
        languages: Optional[List[str]] = None,
    ) -> Dict:
        """
        Fetch transcript for a YouTube video.

        Args:
            video_id: YouTube video ID
            languages: Preferred languages (default: ['en'])

        Returns:
            Dict with transcript data and metadata

        Raises:
            NoTranscriptFound: If no transcript is available
            TranscriptsDisabled: If transcripts are disabled for the video
            VideoUnavailable: If the video doesn't exist
        """
        if languages is None:
            languages = ['en']

        try:
            # Configure proxy if credentials are available
            proxy_config = None
            if WEBSHARE_PROXY_USERNAME and WEBSHARE_PROXY_PASSWORD:
                try:
                    from youtube_transcript_api.proxies import WebshareProxyConfig
                    proxy_config = WebshareProxyConfig(
                        proxy_username=WEBSHARE_PROXY_USERNAME,
                        proxy_password=WEBSHARE_PROXY_PASSWORD,
                    )
                    logger.info("Using Webshare rotating proxy for YouTube transcript")
                except ImportError:
                    logger.warning("Webshare proxy config not available, proceeding without proxy")

            # Fetch transcript with or without proxy
            if proxy_config:
                api = YouTubeTranscriptApi(proxy_config=proxy_config)
            else:
                api = YouTubeTranscriptApi()

            fetched = api.fetch(video_id, languages=languages)

            # Convert snippet dataclasses to dicts
            transcript_data = [
                {
                    "text": snippet.text,
                    "start": snippet.start,
                    "duration": snippet.duration,
                }
                for snippet in fetched.snippets
            ]
            is_generated = fetched.is_generated

            # Calculate total duration
            if transcript_data:
                total_duration = transcript_data[-1]['start'] + transcript_data[-1]['duration']
            else:
                total_duration = 0

            return {
                "video_id": video_id,
                "language": fetched.language_code,
                "is_generated": is_generated,
                "is_translatable": False,  # Not available in this version
                "transcript": transcript_data,
                "total_duration": total_duration,
                "entry_count": len(transcript_data),
            }

        except NoTranscriptFound:
            logger.warning(f"No transcript found for video {video_id}")
            raise
        except TranscriptsDisabled:
            logger.warning(f"Transcripts disabled for video {video_id}")
            raise
        except VideoUnavailable:
            logger.warning(f"Video {video_id} is unavailable")
            raise
        except Exception as e:
            logger.error(f"Error fetching transcript for {video_id}: {e}")
            raise

    @staticmethod
    def format_transcript_as_text(transcript_data: List[Dict]) -> str:
        """
        Format transcript data as plain text.

        Args:
            transcript_data: List of transcript entries

        Returns:
            Formatted text with timestamps
        """
        lines = []
        for entry in transcript_data:
            timestamp = YouTubeService._format_timestamp(entry['start'])
            text = entry['text'].strip()
            lines.append(f"[{timestamp}] {text}")

        return "\n".join(lines)

    @staticmethod
    def _format_timestamp(seconds: float) -> str:
        """Format seconds as HH:MM:SS or MM:SS."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"

    @staticmethod
    def search_transcript(
        transcript_data: List[Dict],
        query: str,
        context_entries: int = 2,
    ) -> List[Dict]:
        """
        Search for a query in the transcript.

        Args:
            transcript_data: List of transcript entries
            query: Search query
            context_entries: Number of entries before/after to include

        Returns:
            List of matching entries with context
        """
        query_lower = query.lower()
        results = []

        for i, entry in enumerate(transcript_data):
            if query_lower in entry['text'].lower():
                # Include context
                start_idx = max(0, i - context_entries)
                end_idx = min(len(transcript_data), i + context_entries + 1)

                context = transcript_data[start_idx:end_idx]
                results.append({
                    "match_index": i,
                    "match_text": entry['text'],
                    "timestamp": entry['start'],
                    "context": context,
                })

        return results

    @staticmethod
    def get_video_metadata(video_id: str) -> Dict:
        """
        Fetch video metadata using yt-dlp.

        Args:
            video_id: YouTube video ID

        Returns:
            Dict with video metadata (title, channel, views, duration, etc.)

        Raises:
            Exception: If metadata cannot be fetched
        """
        try:
            # Configure yt-dlp to extract info only (no download)
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
            }

            url = f"https://www.youtube.com/watch?v={video_id}"

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

                return {
                    "video_id": video_id,
                    "title": info.get("title", "Unknown Title"),
                    "channel": info.get("uploader", "Unknown Channel"),
                    "channel_id": info.get("channel_id", ""),
                    "view_count": info.get("view_count", 0),
                    "duration": info.get("duration", 0),
                    "upload_date": info.get("upload_date", ""),
                    "thumbnail": info.get("thumbnail", ""),
                    "description": info.get("description", ""),
                }

        except Exception as e:
            logger.error(f"Error fetching metadata for {video_id}: {e}")
            raise


# Global service instance
_youtube_service: Optional[YouTubeService] = None


def get_youtube_service() -> YouTubeService:
    """Get the global YouTube service instance."""
    global _youtube_service
    if _youtube_service is None:
        _youtube_service = YouTubeService()
    return _youtube_service
