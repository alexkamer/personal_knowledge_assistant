/**
 * YouTube service for fetching video transcripts.
 */
import { apiClient } from './api';

export interface TranscriptEntry {
  text: string;
  start: number;
  duration: number;
}

export interface TranscriptData {
  video_id: string;
  language: string;
  is_generated: boolean;
  is_translatable: boolean;
  transcript: TranscriptEntry[];
  total_duration: number;
  entry_count: number;
}

export interface TranscriptSearchResult {
  match_index: number;
  match_text: string;
  timestamp: number;
  context: TranscriptEntry[];
}

export interface TranscriptSearchResponse {
  results: TranscriptSearchResult[];
  total_matches: number;
}

export interface VideoSummary {
  video_id: string;
  summary: string;
  key_points: string[];
  topics: string[];
}

export interface VideoMetadata {
  video_id: string;
  title: string;
  channel: string;
  channel_id: string;
  view_count: number;
  duration: number;
  upload_date: string;
  thumbnail: string;
  description: string;
}

export const youtubeService = {
  /**
   * Fetch transcript for a YouTube video.
   */
  async getTranscript(url: string, languages?: string[]): Promise<TranscriptData> {
    const response = await apiClient.post<TranscriptData>('/youtube/transcript', {
      url,
      languages,
    });
    return response.data;
  },

  /**
   * Search within a video transcript.
   */
  async searchTranscript(
    videoId: string,
    query: string,
    contextEntries = 2
  ): Promise<TranscriptSearchResponse> {
    const response = await apiClient.post<TranscriptSearchResponse>(
      '/youtube/transcript/search',
      {
        video_id: videoId,
        query,
        context_entries: contextEntries,
      }
    );
    return response.data;
  },

  /**
   * Extract video ID from YouTube URL.
   */
  async extractVideoId(url: string): Promise<{ video_id: string; url: string }> {
    const response = await apiClient.get(`/youtube/extract-id/${encodeURIComponent(url)}`);
    return response.data;
  },

  /**
   * Format seconds as MM:SS or HH:MM:SS.
   */
  formatTimestamp(seconds: number): string {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);

    if (hours > 0) {
      return `${hours.toString().padStart(2, '0')}:${minutes
        .toString()
        .padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    } else {
      return `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
  },

  /**
   * Get YouTube embed URL from video ID.
   */
  getEmbedUrl(videoId: string, startTime?: number): string {
    const baseUrl = `https://www.youtube.com/embed/${videoId}`;
    const params = new URLSearchParams({
      autoplay: '0',
      rel: '0',
      modestbranding: '1',
    });

    if (startTime !== undefined) {
      params.set('start', Math.floor(startTime).toString());
    }

    return `${baseUrl}?${params.toString()}`;
  },

  /**
   * Get YouTube watch URL from video ID.
   */
  getWatchUrl(videoId: string, startTime?: number): string {
    const baseUrl = `https://www.youtube.com/watch?v=${videoId}`;
    if (startTime !== undefined) {
      return `${baseUrl}&t=${Math.floor(startTime)}s`;
    }
    return baseUrl;
  },

  /**
   * Generate AI summary of a YouTube video.
   */
  async summarizeVideo(videoId: string, languages?: string[]): Promise<VideoSummary> {
    const response = await apiClient.post<VideoSummary>('/youtube/summarize', {
      video_id: videoId,
      languages,
    });
    return response.data;
  },

  /**
   * Fetch metadata for a YouTube video.
   */
  async getVideoMetadata(videoId: string): Promise<VideoMetadata> {
    const response = await apiClient.get<VideoMetadata>(`/youtube/metadata/${videoId}`);
    return response.data;
  },

  /**
   * Format view count as human-readable string (e.g., "1.2M views").
   */
  formatViewCount(viewCount: number): string {
    if (viewCount >= 1000000) {
      return `${(viewCount / 1000000).toFixed(1)}M views`;
    } else if (viewCount >= 1000) {
      return `${(viewCount / 1000).toFixed(1)}K views`;
    } else {
      return `${viewCount} views`;
    }
  },

  /**
   * Format upload date from YYYYMMDD to human-readable format.
   */
  formatUploadDate(uploadDate: string): string {
    if (!uploadDate || uploadDate.length !== 8) return '';
    const year = uploadDate.substring(0, 4);
    const month = uploadDate.substring(4, 6);
    const day = uploadDate.substring(6, 8);
    const date = new Date(`${year}-${month}-${day}`);
    return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
  },
};
