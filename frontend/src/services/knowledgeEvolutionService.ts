/**
 * API service for Knowledge Evolution operations.
 */
import { apiClient } from './api';

export interface ConceptualSnapshot {
  id: string;
  topic: string;
  understanding: string;
  key_concepts: string[];
  misconceptions: string[];
  confidence: number;
  questions_asked: string[];
  conversation_id: string;
  timestamp: string;
  created_at: string;
}

export interface SnapshotCreationRequest {
  topic: string;
  conversation_messages: Array<{ role: string; content: string }>;
  conversation_id: string;
  timestamp?: string;
  model?: string;
}

export interface EvolutionAnalysis {
  topic: string;
  earlier_snapshot: ConceptualSnapshot;
  later_snapshot: ConceptualSnapshot;
  concepts_gained: string[];
  concepts_lost: string[];
  misconceptions_corrected: string[];
  new_misconceptions: string[];
  confidence_change: number;
  learning_velocity: string;
  insights: string[];
}

export interface TimelineItem {
  topic: string;
  snapshot_count: number;
  first_snapshot_date: string;
  last_snapshot_date: string;
  current_confidence: number;
}

export interface TimelineResponse {
  topics: TimelineItem[];
  total_snapshots: number;
}

export const knowledgeEvolutionService = {
  /**
   * Create a new conceptual snapshot from a conversation.
   */
  async createSnapshot(request: SnapshotCreationRequest): Promise<ConceptualSnapshot> {
    const response = await apiClient.post<ConceptualSnapshot>('/knowledge-evolution/snapshots', request);
    return response.data;
  },

  /**
   * Get all snapshots for a specific topic.
   */
  async getSnapshotsByTopic(topic: string): Promise<ConceptualSnapshot[]> {
    const response = await apiClient.get<ConceptualSnapshot[]>(
      `/knowledge-evolution/snapshots/topic/${encodeURIComponent(topic)}`
    );
    return response.data;
  },

  /**
   * Get evolution analysis for a topic between two time periods.
   */
  async getEvolution(
    topic: string,
    startDate?: string,
    endDate?: string
  ): Promise<EvolutionAnalysis> {
    const params: Record<string, string> = {};
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;

    const response = await apiClient.get<EvolutionAnalysis>(
      `/knowledge-evolution/evolution/${encodeURIComponent(topic)}`,
      { params }
    );
    return response.data;
  },

  /**
   * Get timeline of all topics learned.
   */
  async getTimeline(): Promise<TimelineResponse> {
    const response = await apiClient.get<TimelineResponse>('/knowledge-evolution/timeline');
    return response.data;
  },
};
