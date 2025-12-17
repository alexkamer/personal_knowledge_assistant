/**
 * useContext Hook
 *
 * React Query hook for fetching context intelligence data.
 * Manages loading, error, and success states with automatic caching.
 */

import { useQuery, UseQueryResult } from '@tanstack/react-query';
import { ContextResponse, ContextParams, SourceType } from '@/types/context';
import { contextService } from '@/services/contextService';

/**
 * Fetch context intelligence for a piece of content
 *
 * @param sourceType - Type of source ('note', 'document', or 'youtube')
 * @param sourceId - ID of the source to analyze
 * @param params - Optional parameters (synthesis, questions, top_k)
 * @returns React Query result with context data
 *
 * @example
 * ```tsx
 * const { data: context, isLoading, error } = useContext('note', noteId);
 *
 * if (isLoading) return <Spinner />;
 * if (error) return <Error message={error.message} />;
 *
 * return <ContextPanel context={context} />;
 * ```
 */
export function useContext(
  sourceType: SourceType | null,
  sourceId: string | null,
  params?: ContextParams
): UseQueryResult<ContextResponse, Error> {
  return useQuery({
    queryKey: ['context', sourceType, sourceId, params],
    queryFn: () => {
      if (!sourceType || !sourceId) {
        throw new Error('sourceType and sourceId are required');
      }
      return contextService.getContext(sourceType, sourceId, params);
    },
    enabled: !!sourceType && !!sourceId,
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
    retry: 1, // Retry once on failure
  });
}

export default useContext;
