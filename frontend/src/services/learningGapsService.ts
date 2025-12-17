/**
 * API service for Learning Gaps Detection operations.
 */
import { apiClient } from './api';

export interface LearningGap {
  topic: string;
  description: string;
  prerequisite_for: string;
  importance: 'critical' | 'important' | 'helpful';
  learning_resources: string[];
  estimated_time: string;
}

export interface LearningGapsResponse {
  user_question: string;
  gaps: LearningGap[];
  total_gaps: number;
}

export interface LearningPathResponse {
  target_topic: string;
  learning_sequence: string[];
  total_estimated_time: string;
  gaps: LearningGap[];
}

export const learningGapsService = {
  /**
   * Detect foundational knowledge gaps for a question.
   */
  async detectGaps(
    userQuestion: string,
    conversationHistory?: Array<{ role: string; content: string }>,
    context?: string,
    model?: string
  ): Promise<LearningGapsResponse> {
    const response = await apiClient.post<LearningGapsResponse>(
      '/learning-gaps/detect',
      {
        user_question: userQuestion,
        conversation_history: conversationHistory,
        context,
        model,
      },
      {
        timeout: 120000, // 2 minutes for LLM processing
      }
    );
    return response.data;
  },

  /**
   * Generate a personalized learning path from detected gaps.
   */
  async generateLearningPath(
    userQuestion: string,
    gaps: LearningGap[],
    model?: string
  ): Promise<LearningPathResponse> {
    const response = await apiClient.post<LearningPathResponse>(
      '/learning-gaps/path',
      {
        user_question: userQuestion,
        gaps: gaps.map((gap) => ({
          topic: gap.topic,
          description: gap.description,
          prerequisite_for: gap.prerequisite_for,
          importance: gap.importance,
          learning_resources: gap.learning_resources,
          estimated_time: gap.estimated_time,
        })),
        model,
      },
      {
        timeout: 120000, // 2 minutes for LLM processing
      }
    );
    return response.data;
  },
};
