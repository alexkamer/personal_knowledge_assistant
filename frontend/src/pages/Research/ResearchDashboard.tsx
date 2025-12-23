/**
 * Research Dashboard - Main page for Research Autopilot
 *
 * Displays list of research projects with status, progress, and quick actions
 */
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useResearchProjects } from '@/hooks/useResearchProjects';
import ProjectCard from './components/ProjectCard';

const ResearchDashboard: React.FC = () => {
  const navigate = useNavigate();
  const [statusFilter, setStatusFilter] = useState<string | undefined>(undefined);

  const { data, isLoading, error } = useResearchProjects({
    status: statusFilter,
    limit: 50,
  });

  const projects = data?.projects || [];
  const activeProjects = projects.filter(p => p.status === 'active');
  const pausedProjects = projects.filter(p => p.status === 'paused');
  const completedProjects = projects.filter(p => p.status === 'completed');

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
            <p className="text-red-800 dark:text-red-200">
              Failed to load research projects. Please try again.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
                Research Autopilot
              </h1>
              <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                Automated research projects that run on a schedule
              </p>
              <div className="mt-2 flex items-center gap-2 text-xs">
                <span className="text-gray-500 dark:text-gray-400">Need one-time research?</span>
                <a
                  href="/research"
                  className="text-blue-600 dark:text-blue-400 hover:underline"
                >
                  Use Web Researcher →
                </a>
              </div>
            </div>
            <button
              onClick={() => navigate('/research/new')}
              className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              <svg className="mr-2 h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              New Project
            </button>
          </div>

          {/* Stats */}
          <div className="mt-6 grid grid-cols-1 gap-5 sm:grid-cols-3">
            <div className="bg-gray-50 dark:bg-gray-700/50 overflow-hidden rounded-lg px-4 py-5">
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">
                Active Projects
              </dt>
              <dd className="mt-1 text-3xl font-semibold text-gray-900 dark:text-white">
                {isLoading ? '...' : activeProjects.length}
              </dd>
            </div>
            <div className="bg-gray-50 dark:bg-gray-700/50 overflow-hidden rounded-lg px-4 py-5">
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">
                Total Tasks
              </dt>
              <dd className="mt-1 text-3xl font-semibold text-gray-900 dark:text-white">
                {isLoading ? '...' : projects.reduce((sum, p) => sum + p.total_tasks, 0)}
              </dd>
            </div>
            <div className="bg-gray-50 dark:bg-gray-700/50 overflow-hidden rounded-lg px-4 py-5">
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">
                Sources Collected
              </dt>
              <dd className="mt-1 text-3xl font-semibold text-gray-900 dark:text-white">
                {isLoading ? '...' : projects.reduce((sum, p) => sum + p.total_sources_added, 0)}
              </dd>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Filter Tabs */}
        <div className="mb-6">
          <div className="sm:hidden">
            <select
              value={statusFilter || 'all'}
              onChange={(e) => setStatusFilter(e.target.value === 'all' ? undefined : e.target.value)}
              className="block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
            >
              <option value="all">All Projects</option>
              <option value="active">Active ({activeProjects.length})</option>
              <option value="paused">Paused ({pausedProjects.length})</option>
              <option value="completed">Completed ({completedProjects.length})</option>
            </select>
          </div>
          <div className="hidden sm:block">
            <nav className="flex space-x-4" aria-label="Tabs">
              {[
                { name: 'All Projects', value: undefined, count: projects.length },
                { name: 'Active', value: 'active', count: activeProjects.length },
                { name: 'Paused', value: 'paused', count: pausedProjects.length },
                { name: 'Completed', value: 'completed', count: completedProjects.length },
              ].map((tab) => (
                <button
                  key={tab.name}
                  onClick={() => setStatusFilter(tab.value)}
                  className={`${
                    statusFilter === tab.value
                      ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
                      : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
                  } px-3 py-2 font-medium text-sm rounded-md`}
                >
                  {tab.name}
                  <span className="ml-2 py-0.5 px-2 rounded-full bg-gray-200 dark:bg-gray-600 text-xs">
                    {tab.count}
                  </span>
                </button>
              ))}
            </nav>
          </div>
        </div>

        {/* Loading State */}
        {isLoading && (
          <div className="flex justify-center items-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        )}

        {/* Empty State */}
        {!isLoading && projects.length === 0 && (
          <div className="text-center py-12">
            <svg
              className="mx-auto h-12 w-12 text-gray-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">
              No research projects
            </h3>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              Get started by creating your first autonomous research project.
            </p>
            <div className="mt-6">
              <button
                onClick={() => navigate('/research/new')}
                className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
              >
                <svg className="mr-2 h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                Create Project
              </button>
            </div>
          </div>
        )}

        {/* Project List */}
        {!isLoading && projects.length > 0 && (
          <div className="space-y-4">
            {projects.map((project) => (
              <ProjectCard key={project.id} project={project} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default ResearchDashboard;
