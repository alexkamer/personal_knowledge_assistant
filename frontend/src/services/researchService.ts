/**
 * Research service for web research operations.
 */
import api from './api';

export interface ResearchTaskCreate {
  query: string;
  max_sources?: number;
  depth?: 'quick' | 'thorough' | 'deep';
  source_types?: string[];
}

export interface ResearchTaskStart {
  task_id: string;
  status: string;
  message: string;
}

export interface ResearchTask {
  id: string;
  query: string;
  status: string;
  max_sources: number;
  depth: string;
  source_types: string[] | null;
  sources_found: number;
  sources_scraped: number;
  sources_added: number;
  sources_failed: number;
  sources_skipped: number;
  current_step: string | null;
  progress_percentage: number;
  estimated_time_remaining: number | null;
  summary: string | null;
  contradictions_found: number;
  suggested_followups: string[] | null;
  job_id: string | null;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ResearchTaskListItem {
  id: string;
  query: string;
  status: string;
  sources_added: number;
  sources_failed: number;
  created_at: string;
  completed_at: string | null;
}

export interface ResearchTaskList {
  tasks: ResearchTaskListItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface ResearchSource {
  id: string;
  url: string;
  title: string | null;
  domain: string | null;
  source_type: string | null;
  credibility_score: number | null;
  credibility_reasons: string[] | null;
  status: string;
  failure_reason: string | null;
  document_id: string | null;
  created_at: string;
}

export interface ResearchResults {
  task_id: string;
  query: string;
  status: string;
  summary: string | null;
  key_findings: Record<string, any> | null;
  sources: ResearchSource[];
  contradictions_found: number;
  suggested_followups: string[] | null;
  sources_added: number;
  sources_failed: number;
  sources_skipped: number;
  completed_at: string | null;
}

/**
 * Start a new research task.
 */
export const startResearch = async (data: ResearchTaskCreate): Promise<ResearchTaskStart> => {
  const response = await api.post('/research/start', data);
  return response.data;
};

/**
 * Get list of research tasks.
 */
export const getResearchTasks = async (
  limit = 20,
  offset = 0,
  status?: string
): Promise<ResearchTaskList> => {
  const params: Record<string, any> = { limit, offset };
  if (status) params.status = status;

  const response = await api.get('/research/tasks', { params });
  return response.data;
};

/**
 * Get research task by ID.
 */
export const getResearchTask = async (taskId: string): Promise<ResearchTask> => {
  const response = await api.get(`/research/tasks/${taskId}`);
  return response.data;
};

/**
 * Get research results.
 */
export const getResearchResults = async (taskId: string): Promise<ResearchResults> => {
  const response = await api.get(`/research/tasks/${taskId}/results`);
  return response.data;
};

/**
 * Cancel a research task.
 */
export const cancelResearchTask = async (taskId: string): Promise<void> => {
  await api.post(`/research/tasks/${taskId}/cancel`);
};

/**
 * Delete a research task.
 */
export const deleteResearchTask = async (
  taskId: string,
  deleteSources = false
): Promise<void> => {
  await api.delete(`/research/tasks/${taskId}`, {
    params: { delete_sources: deleteSources },
  });
};
