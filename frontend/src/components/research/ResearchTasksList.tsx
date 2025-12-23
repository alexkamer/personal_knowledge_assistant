/**
 * Research tasks list component - shows research history.
 */
import { Clock, CheckCircle, XCircle, Loader2, AlertCircle } from 'lucide-react';
import { ResearchTaskListItem } from '@/services/researchService';

interface ResearchTasksListProps {
  tasks: ResearchTaskListItem[];
  isLoading: boolean;
  onTaskClick: (taskId: string) => void;
}

export function ResearchTasksList({ tasks, isLoading, onTaskClick }: ResearchTasksListProps) {
  if (isLoading) {
    return (
      <div className="bg-white dark:bg-gray-900 rounded-lg shadow-sm border border-gray-200 dark:border-gray-800 p-12 text-center">
        <Loader2 className="w-8 h-8 animate-spin text-blue-500 mx-auto mb-4" />
        <p className="text-gray-600 dark:text-gray-400">Loading research history...</p>
      </div>
    );
  }

  if (tasks.length === 0) {
    return (
      <div className="bg-white dark:bg-gray-900 rounded-lg shadow-sm border border-gray-200 dark:border-gray-800 p-12 text-center">
        <Clock className="w-12 h-12 text-gray-300 dark:text-gray-700 mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">No Research History</h3>
        <p className="text-gray-600 dark:text-gray-400">
          Your completed research tasks will appear here
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-900 rounded-lg shadow-sm border border-gray-200 dark:border-gray-800 overflow-hidden">
      <div className="divide-y divide-stone-200 dark:divide-stone-800">
        {tasks.map((task) => (
          <button
            key={task.id}
            onClick={() => onTaskClick(task.id)}
            className="w-full p-6 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors text-left"
          >
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  {getStatusIcon(task.status)}
                  <span className={`text-sm font-medium ${getStatusColor(task.status)}`}>
                    {getStatusLabel(task.status)}
                  </span>
                </div>
                <h4 className="font-medium text-gray-900 dark:text-white mb-1">{task.query}</h4>
                <div className="flex items-center gap-4 text-sm text-gray-500 dark:text-gray-400">
                  <span>
                    {new Date(task.created_at).toLocaleDateString('en-US', {
                      month: 'short',
                      day: 'numeric',
                      year: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </span>
                  {task.status === 'completed' && (
                    <>
                      <span>•</span>
                      <span>{task.sources_added} sources added</span>
                    </>
                  )}
                  {task.sources_failed > 0 && (
                    <>
                      <span>•</span>
                      <span className="text-red-500 dark:text-red-400">
                        {task.sources_failed} failed
                      </span>
                    </>
                  )}
                </div>
              </div>
              <div className="flex-shrink-0">
                <span className="text-sm text-gray-400 dark:text-gray-500">View →</span>
              </div>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}

function getStatusIcon(status: string) {
  switch (status) {
    case 'completed':
      return <CheckCircle className="w-4 h-4 text-green-500" />;
    case 'failed':
      return <XCircle className="w-4 h-4 text-red-500" />;
    case 'running':
      return <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />;
    case 'cancelled':
      return <AlertCircle className="w-4 h-4 text-orange-500" />;
    default:
      return <Clock className="w-4 h-4 text-gray-400" />;
  }
}

function getStatusColor(status: string) {
  switch (status) {
    case 'completed':
      return 'text-green-600 dark:text-green-400';
    case 'failed':
      return 'text-red-600 dark:text-red-400';
    case 'running':
      return 'text-blue-600 dark:text-blue-400';
    case 'cancelled':
      return 'text-orange-600 dark:text-orange-400';
    default:
      return 'text-gray-600 dark:text-gray-400';
  }
}

function getStatusLabel(status: string) {
  switch (status) {
    case 'completed':
      return 'Completed';
    case 'failed':
      return 'Failed';
    case 'running':
      return 'In Progress';
    case 'queued':
      return 'Queued';
    case 'cancelled':
      return 'Cancelled';
    default:
      return status;
  }
}
