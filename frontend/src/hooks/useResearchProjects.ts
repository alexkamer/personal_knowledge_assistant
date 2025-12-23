/**
 * React Query hooks for Research Autopilot
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  researchProjectsApi,
  researchBriefingsApi,
  ResearchProjectCreate,
  ResearchProjectUpdate,
  TaskGenerationRequest,
} from '@/services/research-api';

// Query keys
export const researchKeys = {
  all: ['research'] as const,
  projects: () => [...researchKeys.all, 'projects'] as const,
  project: (id: string) => [...researchKeys.projects(), id] as const,
  projectProgress: (id: string) => [...researchKeys.project(id), 'progress'] as const,
  projectTasks: (id: string) => [...researchKeys.project(id), 'tasks'] as const,
  briefings: () => [...researchKeys.all, 'briefings'] as const,
  briefing: (id: string) => [...researchKeys.briefings(), id] as const,
  projectBriefings: (projectId: string) => [...researchKeys.project(projectId), 'briefings'] as const,
};

// ============================================================================
// Research Projects Hooks
// ============================================================================

/**
 * Hook to list all research projects
 */
export const useResearchProjects = (params?: {
  status?: string;
  limit?: number;
  offset?: number;
}) => {
  return useQuery({
    queryKey: [...researchKeys.projects(), params],
    queryFn: () => researchProjectsApi.list(params),
  });
};

/**
 * Hook to get a single research project
 */
export const useResearchProject = (projectId: string) => {
  return useQuery({
    queryKey: researchKeys.project(projectId),
    queryFn: () => researchProjectsApi.get(projectId),
    enabled: !!projectId,
  });
};

/**
 * Hook to get project progress
 */
export const useProjectProgress = (projectId: string, options?: { refetchInterval?: number }) => {
  return useQuery({
    queryKey: researchKeys.projectProgress(projectId),
    queryFn: () => researchProjectsApi.getProgress(projectId),
    enabled: !!projectId,
    refetchInterval: options?.refetchInterval || false,
  });
};

/**
 * Hook to list project tasks
 */
export const useProjectTasks = (projectId: string, status?: string) => {
  return useQuery({
    queryKey: [...researchKeys.projectTasks(projectId), status],
    queryFn: () => researchProjectsApi.listTasks(projectId, status),
    enabled: !!projectId,
  });
};

/**
 * Hook to create a research project
 */
export const useCreateProject = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: ResearchProjectCreate) => researchProjectsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: researchKeys.projects() });
    },
  });
};

/**
 * Hook to update a research project
 */
export const useUpdateProject = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: ResearchProjectUpdate }) =>
      researchProjectsApi.update(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: researchKeys.project(variables.id) });
      queryClient.invalidateQueries({ queryKey: researchKeys.projects() });
    },
  });
};

/**
 * Hook to delete a research project
 */
export const useDeleteProject = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, deleteTasks }: { id: string; deleteTasks?: boolean }) =>
      researchProjectsApi.delete(id, deleteTasks),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: researchKeys.projects() });
    },
  });
};

/**
 * Hook to generate task queries
 */
export const useGenerateTasks = () => {
  return useMutation({
    mutationFn: ({ projectId, request }: { projectId: string; request: TaskGenerationRequest }) =>
      researchProjectsApi.generateTasks(projectId, request),
  });
};

/**
 * Hook to create tasks from queries
 */
export const useCreateTasks = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ projectId, queries }: { projectId: string; queries: string[] }) =>
      researchProjectsApi.createTasks(projectId, queries),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: researchKeys.projectTasks(variables.projectId) });
      queryClient.invalidateQueries({ queryKey: researchKeys.projectProgress(variables.projectId) });
    },
  });
};

/**
 * Hook to manually run a project
 */
export const useRunProject = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (projectId: string) => researchProjectsApi.runNow(projectId),
    onSuccess: (_, projectId) => {
      queryClient.invalidateQueries({ queryKey: researchKeys.project(projectId) });
      queryClient.invalidateQueries({ queryKey: researchKeys.projectProgress(projectId) });
      queryClient.invalidateQueries({ queryKey: researchKeys.projectTasks(projectId) });
    },
  });
};

/**
 * Hook to pause a project
 */
export const usePauseProject = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (projectId: string) => researchProjectsApi.pause(projectId),
    onSuccess: (_, projectId) => {
      queryClient.invalidateQueries({ queryKey: researchKeys.project(projectId) });
      queryClient.invalidateQueries({ queryKey: researchKeys.projects() });
    },
  });
};

/**
 * Hook to resume a project
 */
export const useResumeProject = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (projectId: string) => researchProjectsApi.resume(projectId),
    onSuccess: (_, projectId) => {
      queryClient.invalidateQueries({ queryKey: researchKeys.project(projectId) });
      queryClient.invalidateQueries({ queryKey: researchKeys.projects() });
    },
  });
};

/**
 * Hook to update project schedule
 */
export const useUpdateSchedule = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ projectId, schedule }: {
      projectId: string;
      schedule: { schedule_type: string; schedule_cron?: string }
    }) => researchProjectsApi.updateSchedule(projectId, schedule),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: researchKeys.project(variables.projectId) });
    },
  });
};

// ============================================================================
// Research Briefings Hooks
// ============================================================================

/**
 * Hook to list all briefings
 */
export const useResearchBriefings = (params?: { limit?: number; offset?: number }) => {
  return useQuery({
    queryKey: [...researchKeys.briefings(), params],
    queryFn: () => researchBriefingsApi.list(params),
  });
};

/**
 * Hook to get a single briefing
 */
export const useResearchBriefing = (briefingId: string) => {
  return useQuery({
    queryKey: researchKeys.briefing(briefingId),
    queryFn: () => researchBriefingsApi.get(briefingId),
    enabled: !!briefingId,
  });
};

/**
 * Hook to list briefings for a project
 */
export const useProjectBriefings = (projectId: string) => {
  return useQuery({
    queryKey: researchKeys.projectBriefings(projectId),
    queryFn: () => researchBriefingsApi.listForProject(projectId),
    enabled: !!projectId,
  });
};

/**
 * Hook to generate a briefing
 */
export const useGenerateBriefing = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ projectId, taskIds }: { projectId: string; taskIds?: string[] }) =>
      researchBriefingsApi.generate(projectId, taskIds),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: researchKeys.projectBriefings(variables.projectId) });
      queryClient.invalidateQueries({ queryKey: researchKeys.briefings() });
    },
  });
};

/**
 * Hook to delete a briefing
 */
export const useDeleteBriefing = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (briefingId: string) => researchBriefingsApi.delete(briefingId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: researchKeys.briefings() });
    },
  });
};

/**
 * Hook to export briefing as markdown
 */
export const useExportBriefingMarkdown = (briefingId: string) => {
  return useQuery({
    queryKey: [...researchKeys.briefing(briefingId), 'markdown'],
    queryFn: () => researchBriefingsApi.exportMarkdown(briefingId),
    enabled: false, // Only run when explicitly called
  });
};

/**
 * Hook to mark briefing as viewed
 */
export const useMarkBriefingViewed = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (briefingId: string) => researchBriefingsApi.markViewed(briefingId),
    onSuccess: (_, briefingId) => {
      queryClient.invalidateQueries({ queryKey: researchKeys.briefing(briefingId) });
    },
  });
};
