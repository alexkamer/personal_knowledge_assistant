/**
 * Project Detail Page - Detailed view of a research project
 *
 * Tabs:
 * - Overview: Project details, progress, stats
 * - Tasks: List of research tasks with status
 * - Briefings: Generated research briefings
 * - Settings: Edit project configuration
 */
import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { formatDistanceToNow } from 'date-fns';
import {
  useResearchProject,
  useProjectProgress,
  useProjectTasks,
  useProjectBriefings,
  useRunProject,
  usePauseProject,
  useResumeProject,
  useUpdateProject,
  useGenerateTasks,
  useCreateTasks,
  useGenerateBriefing,
} from '@/hooks/useResearchProjects';

type Tab = 'overview' | 'tasks' | 'briefings' | 'settings';

const ProjectDetail: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();

  const [activeTab, setActiveTab] = useState<Tab>('overview');
  const [taskCount, setTaskCount] = useState(5);
  const [isGeneratingTasks, setIsGeneratingTasks] = useState(false);

  const { data: project, isLoading, error } = useResearchProject(projectId!);
  const { data: progress } = useProjectProgress(projectId!, { refetchInterval: 5000 });
  const { data: tasks } = useProjectTasks(projectId!);
  const { data: briefingsData } = useProjectBriefings(projectId!);

  const runProject = useRunProject();
  const pauseProject = usePauseProject();
  const resumeProject = useResumeProject();
  const generateTasks = useGenerateTasks();
  const createTasks = useCreateTasks();
  const generateBriefing = useGenerateBriefing();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error || !project) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
            <p className="text-red-800 dark:text-red-200">
              Failed to load project. Please try again.
            </p>
          </div>
        </div>
      </div>
    );
  }

  const handleGenerateTasks = async () => {
    setIsGeneratingTasks(true);
    try {
      const result = await generateTasks.mutateAsync({
        projectId: projectId!,
        request: { count: taskCount, consider_existing: true },
      });
      await createTasks.mutateAsync({
        projectId: projectId!,
        queries: result.generated_queries,
      });
    } catch (error) {
      console.error('Failed to generate tasks:', error);
    } finally {
      setIsGeneratingTasks(false);
    }
  };

  const handleGenerateBriefing = async () => {
    try {
      await generateBriefing.mutateAsync({ projectId: projectId! });
    } catch (error) {
      console.error('Failed to generate briefing:', error);
    }
  };

  const progressPercent =
    progress && progress.total_tasks > 0
      ? Math.round((progress.completed_tasks / progress.total_tasks) * 100)
      : 0;

  const briefings = briefingsData?.briefings || [];

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <button
                onClick={() => navigate('/research')}
                className="mr-4 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300"
              >
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M15 19l-7-7 7-7"
                  />
                </svg>
              </button>
              <div>
                <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                  {project.name}
                </h1>
                {project.description && (
                  <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                    {project.description}
                  </p>
                )}
              </div>
            </div>

            <div className="flex items-center gap-2">
              {project.status === 'active' && (
                <>
                  <button
                    onClick={() => runProject.mutate(projectId!)}
                    disabled={runProject.isPending}
                    className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
                  >
                    <svg className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"
                      />
                    </svg>
                    Run Now
                  </button>
                  <button
                    onClick={() => pauseProject.mutate(projectId!)}
                    disabled={pauseProject.isPending}
                    className="inline-flex items-center px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
                  >
                    Pause
                  </button>
                </>
              )}
              {project.status === 'paused' && (
                <button
                  onClick={() => resumeProject.mutate(projectId!)}
                  disabled={resumeProject.isPending}
                  className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700"
                >
                  Resume
                </button>
              )}
            </div>
          </div>

          {/* Tabs */}
          <div className="mt-6">
            <nav className="flex space-x-4" aria-label="Tabs">
              {[
                { id: 'overview', label: 'Overview' },
                { id: 'tasks', label: 'Tasks', count: tasks?.length || 0 },
                { id: 'briefings', label: 'Briefings', count: briefings.length },
                { id: 'settings', label: 'Settings' },
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as Tab)}
                  className={`${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                      : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
                  } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
                >
                  {tab.label}
                  {tab.count !== undefined && (
                    <span
                      className={`ml-2 py-0.5 px-2 rounded-full text-xs ${
                        activeTab === tab.id
                          ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400'
                          : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
                      }`}
                    >
                      {tab.count}
                    </span>
                  )}
                </button>
              ))}
            </nav>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Overview Tab */}
        {activeTab === 'overview' && progress && (
          <div className="space-y-6">
            {/* Progress Section */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Progress
              </h2>
              <div className="space-y-4">
                <div>
                  <div className="flex items-center justify-between text-sm mb-2">
                    <span className="text-gray-500 dark:text-gray-400">Overall Progress</span>
                    <span className="font-medium text-gray-900 dark:text-white">
                      {progress.completed_tasks} of {progress.total_tasks} completed ({progressPercent}%)
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
                    <div
                      className="bg-blue-600 h-3 rounded-full transition-all"
                      style={{ width: `${progressPercent}%` }}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-4 gap-4 pt-4">
                  <div>
                    <p className="text-sm text-gray-500 dark:text-gray-400">Queued</p>
                    <p className="mt-1 text-2xl font-semibold text-gray-900 dark:text-white">
                      {progress.queued_tasks}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500 dark:text-gray-400">Running</p>
                    <p className="mt-1 text-2xl font-semibold text-yellow-600 dark:text-yellow-400">
                      {progress.running_tasks}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500 dark:text-gray-400">Completed</p>
                    <p className="mt-1 text-2xl font-semibold text-green-600 dark:text-green-400">
                      {progress.completed_tasks}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500 dark:text-gray-400">Failed</p>
                    <p className="mt-1 text-2xl font-semibold text-red-600 dark:text-red-400">
                      {progress.failed_tasks}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
                <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">
                  Total Sources
                </h3>
                <p className="mt-2 text-3xl font-semibold text-gray-900 dark:text-white">
                  {progress.total_sources_added}
                </p>
                <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                  {progress.total_sources_failed} failed
                </p>
              </div>

              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
                <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">
                  Schedule
                </h3>
                <p className="mt-2 text-lg font-semibold text-gray-900 dark:text-white capitalize">
                  {project.schedule_type}
                </p>
                {project.schedule_cron && (
                  <p className="mt-1 text-sm text-gray-500 dark:text-gray-400 font-mono">
                    {project.schedule_cron}
                  </p>
                )}
              </div>

              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
                <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">
                  {project.next_run_at ? 'Next Run' : 'Last Run'}
                </h3>
                <p className="mt-2 text-lg font-semibold text-gray-900 dark:text-white">
                  {project.next_run_at
                    ? formatDistanceToNow(new Date(project.next_run_at), { addSuffix: true })
                    : project.last_run_at
                    ? formatDistanceToNow(new Date(project.last_run_at), { addSuffix: true })
                    : 'Never'}
                </p>
              </div>
            </div>

            {/* Research Goal */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                Research Goal
              </h2>
              <p className="text-gray-700 dark:text-gray-300">{project.goal}</p>
            </div>

            {/* Recent Tasks */}
            {progress.recent_tasks && progress.recent_tasks.length > 0 && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                  Recent Tasks
                </h2>
                <div className="space-y-3">
                  {progress.recent_tasks.map((task) => (
                    <div
                      key={task.id}
                      className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg"
                    >
                      <div className="flex-1">
                        <p className="text-sm font-medium text-gray-900 dark:text-white">
                          {task.query}
                        </p>
                        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                          {task.sources_added} sources added
                        </p>
                      </div>
                      <span
                        className={`ml-4 px-2 py-1 text-xs font-medium rounded-full ${
                          task.status === 'completed'
                            ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300'
                            : task.status === 'failed'
                            ? 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300'
                            : task.status === 'running'
                            ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300'
                            : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
                        }`}
                      >
                        {task.status}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Tasks Tab */}
        {activeTab === 'tasks' && (
          <div className="space-y-6">
            {/* Generate Tasks Section */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Generate Research Tasks
              </h2>
              <div className="flex items-end gap-4">
                <div className="flex-1">
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Number of tasks to generate
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="20"
                    value={taskCount}
                    onChange={(e) => setTaskCount(parseInt(e.target.value))}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
                  />
                </div>
                <button
                  onClick={handleGenerateTasks}
                  disabled={isGeneratingTasks || generateTasks.isPending || createTasks.isPending}
                  className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
                >
                  {isGeneratingTasks ? 'Generating...' : 'Generate Tasks'}
                </button>
              </div>
            </div>

            {/* Tasks List */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
              <div className="p-6 border-b border-gray-200 dark:border-gray-700">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                  All Tasks ({tasks?.length || 0})
                </h2>
              </div>
              <div className="divide-y divide-gray-200 dark:divide-gray-700">
                {tasks && tasks.length > 0 ? (
                  tasks.map((task) => (
                    <div key={task.id} className="p-6">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h3 className="text-sm font-medium text-gray-900 dark:text-white">
                            {task.query}
                          </h3>
                          <div className="mt-2 flex items-center gap-4 text-xs text-gray-500 dark:text-gray-400">
                            <span>{task.sources_added} sources</span>
                            <span>•</span>
                            <span>{task.progress_percentage}% complete</span>
                            {task.completed_at && (
                              <>
                                <span>•</span>
                                <span>
                                  {formatDistanceToNow(new Date(task.completed_at), {
                                    addSuffix: true,
                                  })}
                                </span>
                              </>
                            )}
                          </div>
                        </div>
                        <span
                          className={`ml-4 px-2.5 py-0.5 text-xs font-medium rounded-full ${
                            task.status === 'completed'
                              ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300'
                              : task.status === 'failed'
                              ? 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300'
                              : task.status === 'running'
                              ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300'
                              : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
                          }`}
                        >
                          {task.status}
                        </span>
                      </div>
                      {task.summary && (
                        <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
                          {task.summary}
                        </p>
                      )}
                    </div>
                  ))
                ) : (
                  <div className="p-12 text-center">
                    <p className="text-gray-500 dark:text-gray-400">
                      No tasks yet. Generate some to get started!
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Briefings Tab */}
        {activeTab === 'briefings' && (
          <div className="space-y-6">
            {/* Generate Briefing Section */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                    Generate Research Briefing
                  </h2>
                  <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                    Create an AI-powered summary of all completed tasks
                  </p>
                </div>
                <button
                  onClick={handleGenerateBriefing}
                  disabled={generateBriefing.isPending}
                  className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
                >
                  {generateBriefing.isPending ? 'Generating...' : 'Generate Briefing'}
                </button>
              </div>
            </div>

            {/* Briefings List */}
            <div className="space-y-4">
              {briefings.length > 0 ? (
                briefings.map((briefing) => (
                  <div
                    key={briefing.id}
                    className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6 cursor-pointer hover:shadow-md transition-shadow"
                    onClick={() => navigate(`/research/briefings/${briefing.id}`)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                          {briefing.title}
                        </h3>
                        <p className="mt-2 text-sm text-gray-600 dark:text-gray-400 line-clamp-3">
                          {briefing.summary}
                        </p>
                        <div className="mt-4 flex items-center gap-4 text-xs text-gray-500 dark:text-gray-400">
                          <span>{briefing.sources_count} sources</span>
                          <span>•</span>
                          <span>
                            {formatDistanceToNow(new Date(briefing.generated_at), {
                              addSuffix: true,
                            })}
                          </span>
                          {!briefing.viewed_at && (
                            <>
                              <span>•</span>
                              <span className="text-blue-600 dark:text-blue-400 font-medium">
                                New
                              </span>
                            </>
                          )}
                        </div>
                      </div>
                      <svg
                        className="h-5 w-5 text-gray-400"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M9 5l7 7-7 7"
                        />
                      </svg>
                    </div>
                  </div>
                ))
              ) : (
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-12 text-center">
                  <p className="text-gray-500 dark:text-gray-400">
                    No briefings yet. Complete some tasks and generate your first briefing!
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Settings Tab */}
        {activeTab === 'settings' && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Project Settings
            </h2>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Settings UI coming soon...
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ProjectDetail;
