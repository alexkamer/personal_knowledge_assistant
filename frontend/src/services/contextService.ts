/**
 * Context Intelligence Service
 *
 * API client for the Cross-Feature Intelligence system.
 * Fetches related content, synthesis, and suggested questions.
 */

import apiClient from './api';
import { ContextResponse, ContextParams, SourceType } from '@/types/context';

/**
 * Get contextual intelligence for a piece of content
 *
 * Analyzes the given content (note, document, or YouTube video) and returns:
 * - Related content items from across all source types
 * - Optional AI-generated synthesis of connections
 * - Optional suggested questions for further exploration
 *
 * @param sourceType - Type of source ('note', 'document', or 'youtube')
 * @param sourceId - ID of the source to analyze
 * @param params - Optional parameters (synthesis, questions, top_k)
 * @returns Promise resolving to context intelligence data
 */
export async function getContext(
  sourceType: SourceType,
  sourceId: string,
  params: ContextParams = {}
): Promise<ContextResponse> {
  const {
    include_synthesis = true,
    include_questions = true,
    top_k = 5,
  } = params;

  const response = await apiClient.get<ContextResponse>(
    `/context/${sourceType}/${sourceId}`,
    {
      params: {
        include_synthesis,
        include_questions,
        top_k,
      },
    }
  );

  return response.data;
}

/**
 * Context service object with all context-related API methods
 */
export const contextService = {
  getContext,
};

export default contextService;
