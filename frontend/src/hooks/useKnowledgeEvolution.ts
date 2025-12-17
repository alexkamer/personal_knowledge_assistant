import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  knowledgeEvolutionService,
  type SnapshotCreationRequest,
} from '@/services/knowledgeEvolutionService';

/**
 * Hook for fetching snapshots for a specific topic.
 */
export function useSnapshots(topic: string | null) {
  return useQuery({
    queryKey: ['knowledge-snapshots', topic],
    queryFn: () => knowledgeEvolutionService.getSnapshotsByTopic(topic!),
    enabled: !!topic,
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
  });
}

/**
 * Hook for fetching evolution analysis for a topic.
 */
export function useEvolution(topic: string | null, startDate?: string, endDate?: string) {
  return useQuery({
    queryKey: ['knowledge-evolution', topic, startDate, endDate],
    queryFn: () => knowledgeEvolutionService.getEvolution(topic!, startDate, endDate),
    enabled: !!topic,
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * Hook for fetching the complete learning timeline.
 */
export function useTimeline() {
  return useQuery({
    queryKey: ['knowledge-timeline'],
    queryFn: () => knowledgeEvolutionService.getTimeline(),
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * Hook for creating a new conceptual snapshot.
 */
export function useCreateSnapshot() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: SnapshotCreationRequest) =>
      knowledgeEvolutionService.createSnapshot(request),
    onSuccess: (data) => {
      // Invalidate snapshots cache for this topic
      queryClient.invalidateQueries({ queryKey: ['knowledge-snapshots', data.topic] });
      // Invalidate timeline cache
      queryClient.invalidateQueries({ queryKey: ['knowledge-timeline'] });
      // Invalidate evolution cache for this topic
      queryClient.invalidateQueries({ queryKey: ['knowledge-evolution', data.topic] });
    },
  });
}
