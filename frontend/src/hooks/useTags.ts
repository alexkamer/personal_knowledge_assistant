/**
 * React Query hooks for tag operations.
 */

import { useQuery } from '@tanstack/react-query';
import { tagService } from '../services/tagService';

export const TAGS_QUERY_KEY = ['tags'];

/**
 * Hook to fetch all tags with usage counts.
 */
export function useTags() {
  return useQuery({
    queryKey: TAGS_QUERY_KEY,
    queryFn: () => tagService.getTags(),
  });
}

/**
 * Hook to fetch popular tags.
 */
export function usePopularTags(limit = 10) {
  return useQuery({
    queryKey: [...TAGS_QUERY_KEY, 'popular', limit],
    queryFn: () => tagService.getPopularTags(limit),
  });
}
