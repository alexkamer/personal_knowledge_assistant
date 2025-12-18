/**
 * React Query hooks for research operations.
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  startResearch,
  getResearchTasks,
  getResearchTask,
  getResearchResults,
  cancelResearchTask,
  deleteResearchTask,
} from '@/services/researchService';

/**
 * Hook to start a new research task.
 */
export const useStartResearch = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: startResearch,
    onSuccess: () => {
      // Invalidate tasks list to show new task
      queryClient.invalidateQueries({ queryKey: ['research-tasks'] });
    },
  });
};

/**
 * Hook to get list of research tasks.
 */
export const useResearchTasks = (limit = 20, offset = 0, status?: string) => {
  return useQuery({
    queryKey: ['research-tasks', limit, offset, status],
    queryFn: () => getResearchTasks(limit, offset, status),
  });
};

/**
 * Hook to get a single research task with polling.
 */
export const useResearchTask = (taskId: string | null, pollingInterval = 5000) => {
  return useQuery({
    queryKey: ['research-task', taskId],
    queryFn: () => getResearchTask(taskId!),
    enabled: !!taskId,
    refetchInterval: (query) => {
      const task = query.state.data;
      // Stop polling when task is complete, failed, or cancelled
      if (!task || ['completed', 'failed', 'cancelled'].includes(task.status)) {
        return false;
      }
      return pollingInterval;
    },
  });
};

/**
 * Hook to get research results.
 */
export const useResearchResults = (taskId: string | null) => {
  return useQuery({
    queryKey: ['research-results', taskId],
    queryFn: () => getResearchResults(taskId!),
    enabled: !!taskId,
  });
};

/**
 * Hook to cancel a research task.
 */
export const useCancelResearch = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: cancelResearchTask,
    onSuccess: (_, taskId) => {
      // Invalidate specific task to update status
      queryClient.invalidateQueries({ queryKey: ['research-task', taskId] });
      queryClient.invalidateQueries({ queryKey: ['research-tasks'] });
    },
  });
};

/**
 * Hook to delete a research task.
 */
export const useDeleteResearch = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ taskId, deleteSources }: { taskId: string; deleteSources: boolean }) =>
      deleteResearchTask(taskId, deleteSources),
    onSuccess: () => {
      // Invalidate tasks list
      queryClient.invalidateQueries({ queryKey: ['research-tasks'] });
    },
  });
};
