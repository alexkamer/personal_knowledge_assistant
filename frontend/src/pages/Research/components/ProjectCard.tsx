/**
 * Project Card Component
 *
 * Displays a research project with status, progress, and quick actions
 */
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { formatDistanceToNow } from 'date-fns';
import {
  useRunProject,
  usePauseProject,
  useResumeProject,
  useDeleteProject,
} from '@/hooks/useResearchProjects';
import type { ResearchProject } from '@/services/research-api';

interface ProjectCardProps {
  project: ResearchProject;
}

const ProjectCard: React.FC<ProjectCardProps> = ({ project }) => {
  const navigate = useNavigate();
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  const runProject = useRunProject();
  const pauseProject = usePauseProject();
  const resumeProject = useResumeProject();
  const deleteProject = useDeleteProject();

  const progressPercent = project.total_tasks > 0
    ? Math.round((project.completed_tasks / project.total_tasks) * 100)
    : 0;

  const getStatusBadge = () => {
    const badges = {
      active: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300',
      paused: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300',
      completed: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300',
      archived: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300',
    };
    return badges[project.status] || badges.active;
  };

  const getScheduleText = () => {
    if (project.schedule_type === 'manual') return 'Manual';
    if (project.schedule_type === 'daily') return 'Daily';
    if (project.schedule_type === 'weekly') return 'Weekly';
    if (project.schedule_type === 'monthly') return 'Monthly';
    if (project.schedule_type === 'custom') return 'Custom';
    return project.schedule_type;
  };

  const handleRunNow = async () => {
    try {
      await runProject.mutateAsync(project.id);
    } catch (error) {
      console.error('Failed to run project:', error);
    }
  };

  const handlePause = async () => {
    try {
      await pauseProject.mutateAsync(project.id);
    } catch (error) {
      console.error('Failed to pause project:', error);
    }
  };

  const handleResume = async () => {
    try {
      await resumeProject.mutateAsync(project.id);
    } catch (error) {
      console.error('Failed to resume project:', error);
    }
  };

  const handleDelete = async () => {
    try {
      await deleteProject.mutateAsync({ id: project.id, deleteTasks: false });
      setShowDeleteConfirm(false);
    } catch (error) {
      console.error('Failed to delete project:', error);
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 hover:shadow-md transition-shadow">
      <div className="p-6">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-3">
              <h3
                onClick={() => navigate(`/research/projects/${project.id}`)}
                className="text-lg font-semibold text-gray-900 dark:text-white cursor-pointer hover:text-blue-600 dark:hover:text-blue-400"
              >
                {project.name}
              </h3>
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusBadge()}`}>
                {project.status}
              </span>
            </div>
            {project.description && (
              <p className="mt-1 text-sm text-gray-500 dark:text-gray-400 line-clamp-2">
                {project.description}
              </p>
            )}
          </div>

          {/* Actions Menu */}
          <div className="ml-4 flex items-center gap-2">
            {project.status === 'active' && (
              <>
                <button
                  onClick={handleRunNow}
                  disabled={runProject.isPending}
                  className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  title="Run Now"
                >
                  {runProject.isPending ? (
                    <div className="animate-spin h-3 w-3 border-2 border-white border-t-transparent rounded-full" />
                  ) : (
                    <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  )}
                  <span className="ml-1">Run</span>
                </button>
                <button
                  onClick={handlePause}
                  disabled={pauseProject.isPending}
                  className="inline-flex items-center px-3 py-1.5 border border-gray-300 dark:border-gray-600 text-xs font-medium rounded text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 disabled:opacity-50"
                  title="Pause"
                >
                  <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </button>
              </>
            )}
            {project.status === 'paused' && (
              <button
                onClick={handleResume}
                disabled={resumeProject.isPending}
                className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded text-white bg-green-600 hover:bg-green-700 disabled:opacity-50"
                title="Resume"
              >
                <svg className="h-3 w-3 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                </svg>
                Resume
              </button>
            )}
            <button
              onClick={() => setShowDeleteConfirm(true)}
              className="inline-flex items-center px-3 py-1.5 border border-red-300 dark:border-red-600 text-xs font-medium rounded text-red-700 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20"
              title="Delete"
            >
              <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="mt-4">
          <div className="flex items-center justify-between text-sm mb-1">
            <span className="text-gray-500 dark:text-gray-400">Progress</span>
            <span className="font-medium text-gray-900 dark:text-white">
              {project.total_tasks === 0
                ? 'No tasks yet'
                : `${project.completed_tasks} of ${project.total_tasks} completed`
              }
            </span>
          </div>
          {project.total_tasks > 0 && (
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all"
                style={{ width: `${progressPercent}%` }}
              />
            </div>
          )}
        </div>

        {/* Stats Grid */}
        <div className="mt-4 grid grid-cols-3 gap-4 text-sm">
          <div>
            <p className="text-gray-500 dark:text-gray-400">Schedule</p>
            <p className="mt-1 font-medium text-gray-900 dark:text-white">
              {getScheduleText()}
            </p>
          </div>
          <div>
            <p className="text-gray-500 dark:text-gray-400">Sources</p>
            <p className="mt-1 font-medium text-gray-900 dark:text-white">
              {project.total_sources_added}
            </p>
          </div>
          <div>
            <p className="text-gray-500 dark:text-gray-400">
              {project.next_run_at ? 'Next Run' : 'Last Run'}
            </p>
            <p className="mt-1 font-medium text-gray-900 dark:text-white">
              {project.next_run_at
                ? formatDistanceToNow(new Date(project.next_run_at), { addSuffix: true })
                : project.last_run_at
                ? formatDistanceToNow(new Date(project.last_run_at), { addSuffix: true })
                : 'Never'}
            </p>
          </div>
        </div>
      </div>

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-md mx-4">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
              Delete Project?
            </h3>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
              Are you sure you want to delete "{project.name}"? This action cannot be undone.
              Tasks and sources will remain in the database.
            </p>
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setShowDeleteConfirm(false)}
                className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
              >
                Cancel
              </button>
              <button
                onClick={handleDelete}
                disabled={deleteProject.isPending}
                className="px-4 py-2 bg-red-600 text-white rounded-md text-sm font-medium hover:bg-red-700 disabled:opacity-50"
              >
                {deleteProject.isPending ? 'Deleting...' : 'Delete'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProjectCard;
