/**
 * API client for Research Autopilot endpoints
 */
import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

// Types
export interface ResearchProject {
  id: string;
  name: string;
  description?: string;
  goal: string;
  status: 'active' | 'paused' | 'completed' | 'archived';
  schedule_type: 'manual' | 'daily' | 'weekly' | 'monthly' | 'custom';
  schedule_cron?: string;
  next_run_at?: string;
  last_run_at?: string;
  auto_generate_tasks: boolean;
  max_tasks_per_run: number;
  default_max_sources: number;
  default_depth: 'quick' | 'thorough' | 'deep';
  default_source_types?: string[];
  total_tasks: number;
  completed_tasks: number;
  failed_tasks: number;
  total_sources_added: number;
  created_at: string;
  updated_at: string;
}

export interface ResearchProjectCreate {
  name: string;
  description?: string;
  goal: string;
  schedule_type: 'manual' | 'daily' | 'weekly' | 'monthly' | 'custom';
  schedule_cron?: string;
  auto_generate_tasks?: boolean;
  max_tasks_per_run?: number;
  default_max_sources?: number;
  default_depth?: 'quick' | 'thorough' | 'deep';
  default_source_types?: string[];
}

export interface ResearchProjectUpdate {
  name?: string;
  description?: string;
  goal?: string;
  status?: 'active' | 'paused' | 'completed' | 'archived';
  schedule_type?: 'manual' | 'daily' | 'weekly' | 'monthly' | 'custom';
  schedule_cron?: string;
  auto_generate_tasks?: boolean;
  max_tasks_per_run?: number;
  default_max_sources?: number;
  default_depth?: 'quick' | 'thorough' | 'deep';
  default_source_types?: string[];
}

export interface ResearchTask {
  id: string;
  query: string;
  status: 'queued' | 'running' | 'completed' | 'failed' | 'cancelled';
  max_sources: number;
  depth: string;
  source_types?: string[];
  sources_found: number;
  sources_scraped: number;
  sources_added: number;
  sources_failed: number;
  sources_skipped: number;
  current_step?: string;
  progress_percentage: number;
  estimated_time_remaining?: number;
  summary?: string;
  contradictions_found: number;
  suggested_followups?: string[];
  error_message?: string;
  started_at?: string;
  completed_at?: string;
  created_at: string;
  updated_at: string;
}

export interface ResearchProgress {
  project_id: string;
  name: string;
  status: string;
  total_tasks: number;
  completed_tasks: number;
  running_tasks: number;
  failed_tasks: number;
  queued_tasks: number;
  total_sources_added: number;
  total_sources_failed: number;
  last_run_at?: string;
  next_run_at?: string;
  recent_tasks: Array<{
    id: string;
    query: string;
    status: string;
    sources_added: number;
    created_at: string;
    completed_at?: string;
  }>;
}

export interface TaskGenerationRequest {
  count: number;
  consider_existing?: boolean;
}

export interface TaskGenerationResponse {
  project_id: string;
  generated_queries: string[];
  message: string;
}

export interface ResearchBriefing {
  id: string;
  project_id: string;
  title: string;
  summary: string;
  key_findings?: Record<string, any>;
  contradictions?: Array<{
    topic: string;
    position_a: string;
    sources_a: number[];
    position_b: string;
    sources_b: number[];
    analysis?: string;
  }>;
  knowledge_gaps?: string[];
  suggested_tasks?: string[];
  task_ids?: string[];
  sources_count: number;
  generated_at: string;
  viewed_at?: string;
  created_at: string;
  updated_at: string;
}

export interface BriefingMarkdown {
  markdown: string;
  title: string;
}

// Research Projects API
export const researchProjectsApi = {
  /**
   * List all research projects
   */
  list: async (params?: {
    status?: string;
    limit?: number;
    offset?: number;
  }) => {
    const response = await axios.get<{
      projects: ResearchProject[];
      total: number;
      limit: number;
      offset: number;
    }>(`${API_BASE}/research/projects`, { params });
    return response.data;
  },

  /**
   * Get a specific project
   */
  get: async (projectId: string) => {
    const response = await axios.get<ResearchProject>(
      `${API_BASE}/research/projects/${projectId}`
    );
    return response.data;
  },

  /**
   * Create a new project
   */
  create: async (data: ResearchProjectCreate) => {
    const response = await axios.post<ResearchProject>(
      `${API_BASE}/research/projects`,
      data
    );
    return response.data;
  },

  /**
   * Update a project
   */
  update: async (projectId: string, data: ResearchProjectUpdate) => {
    const response = await axios.put<ResearchProject>(
      `${API_BASE}/research/projects/${projectId}`,
      data
    );
    return response.data;
  },

  /**
   * Delete a project
   */
  delete: async (projectId: string, deleteTasks = false) => {
    await axios.delete(`${API_BASE}/research/projects/${projectId}`, {
      params: { delete_tasks: deleteTasks },
    });
  },

  /**
   * Get project progress
   */
  getProgress: async (projectId: string) => {
    const response = await axios.get<ResearchProgress>(
      `${API_BASE}/research/projects/${projectId}/progress`
    );
    return response.data;
  },

  /**
   * Generate task queries using LLM
   */
  generateTasks: async (projectId: string, request: TaskGenerationRequest) => {
    const response = await axios.post<TaskGenerationResponse>(
      `${API_BASE}/research/projects/${projectId}/tasks/generate`,
      request
    );
    return response.data;
  },

  /**
   * Create tasks from queries
   */
  createTasks: async (projectId: string, queries: string[]) => {
    const response = await axios.post<ResearchTask[]>(
      `${API_BASE}/research/projects/${projectId}/tasks`,
      queries
    );
    return response.data;
  },

  /**
   * List project tasks
   */
  listTasks: async (projectId: string, status?: string) => {
    const response = await axios.get<ResearchTask[]>(
      `${API_BASE}/research/projects/${projectId}/tasks`,
      { params: { status } }
    );
    return response.data;
  },

  /**
   * Update project schedule
   */
  updateSchedule: async (
    projectId: string,
    schedule: {
      schedule_type: string;
      schedule_cron?: string;
    }
  ) => {
    const response = await axios.post<ResearchProject>(
      `${API_BASE}/research/projects/${projectId}/schedule`,
      schedule
    );
    return response.data;
  },

  /**
   * Remove project schedule
   */
  removeSchedule: async (projectId: string) => {
    const response = await axios.delete<ResearchProject>(
      `${API_BASE}/research/projects/${projectId}/schedule`
    );
    return response.data;
  },

  /**
   * Manually run a project now
   */
  runNow: async (projectId: string) => {
    const response = await axios.post<{
      project_id: string;
      task_ids: string[];
      message: string;
    }>(`${API_BASE}/research/projects/${projectId}/run`);
    return response.data;
  },

  /**
   * Pause a project
   */
  pause: async (projectId: string) => {
    const response = await axios.post<ResearchProject>(
      `${API_BASE}/research/projects/${projectId}/pause`
    );
    return response.data;
  },

  /**
   * Resume a project
   */
  resume: async (projectId: string) => {
    const response = await axios.post<ResearchProject>(
      `${API_BASE}/research/projects/${projectId}/resume`
    );
    return response.data;
  },
};

// Research Briefings API
export const researchBriefingsApi = {
  /**
   * List all briefings
   */
  list: async (params?: { limit?: number; offset?: number }) => {
    const response = await axios.get<{
      briefings: ResearchBriefing[];
      total: number;
      limit: number;
      offset: number;
    }>(`${API_BASE}/research/briefings`, { params });
    return response.data;
  },

  /**
   * Get a specific briefing
   */
  get: async (briefingId: string) => {
    const response = await axios.get<ResearchBriefing>(
      `${API_BASE}/research/briefings/${briefingId}`
    );
    return response.data;
  },

  /**
   * List briefings for a project
   */
  listForProject: async (projectId: string) => {
    const response = await axios.get<{
      briefings: ResearchBriefing[];
      total: number;
    }>(`${API_BASE}/research/projects/${projectId}/briefings`);
    return response.data;
  },

  /**
   * Generate a new briefing
   */
  generate: async (projectId: string, taskIds?: string[]) => {
    const response = await axios.post<ResearchBriefing>(
      `${API_BASE}/research/projects/${projectId}/briefings`,
      { project_id: projectId, task_ids: taskIds }
    );
    return response.data;
  },

  /**
   * Delete a briefing
   */
  delete: async (briefingId: string) => {
    await axios.delete(`${API_BASE}/research/briefings/${briefingId}`);
  },

  /**
   * Export briefing as markdown
   */
  exportMarkdown: async (briefingId: string) => {
    const response = await axios.get<BriefingMarkdown>(
      `${API_BASE}/research/briefings/${briefingId}/markdown`
    );
    return response.data;
  },

  /**
   * Mark briefing as viewed
   */
  markViewed: async (briefingId: string) => {
    const response = await axios.post<ResearchBriefing>(
      `${API_BASE}/research/briefings/${briefingId}/view`
    );
    return response.data;
  },
};
