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
};
