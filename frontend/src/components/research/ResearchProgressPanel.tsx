/**
 * Research progress panel component - shows live progress.
 */
import { Loader2, Search, FileText, CheckCircle, X } from 'lucide-react';
import { ResearchTask } from '@/services/researchService';
import { useCancelResearch } from '@/hooks/useResearch';

interface ResearchProgressPanelProps {
  task: ResearchTask;
}

export function ResearchProgressPanel({ task }: ResearchProgressPanelProps) {
  const cancelResearch = useCancelResearch();

  const handleCancel = async () => {
    if (window.confirm('Are you sure you want to cancel this research task?')) {
      try {
        await cancelResearch.mutateAsync(task.id);
      } catch (error) {
        console.error('Failed to cancel research:', error);
      }
    }
  };

  const formatTime = (seconds: number | null) => {
    if (!seconds) return '...';
    if (seconds < 60) return `${seconds}s`;
    return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
  };

  return (
    <div className="bg-white dark:bg-gray-900 rounded-lg shadow-sm border border-gray-200 dark:border-gray-800 p-6">
      <div className="flex items-start justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
            <Loader2 className="w-5 h-5 animate-spin text-blue-500" />
            Research in Progress
          </h3>
          <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">{task.query}</p>
        </div>
        <button
          onClick={handleCancel}
          disabled={cancelResearch.isPending}
          className="text-gray-500 hover:text-red-500 dark:text-gray-400 dark:hover:text-red-400 transition-colors"
          title="Cancel research"
        >
          <X size={20} />
        </button>
      </div>

      {/* Progress Bar */}
      <div className="mb-6">
        <div className="flex items-center justify-between text-sm mb-2">
          <span className="text-gray-700 dark:text-gray-300 font-medium">
            {task.current_step || 'Processing...'}
          </span>
          <span className="text-gray-500 dark:text-gray-400">{task.progress_percentage}%</span>
        </div>
        <div className="w-full bg-gray-800 rounded-full h-2 overflow-hidden">
          <div
            className="h-full bg-primary-500 rounded-full transition-all duration-500"
            style={{ width: `${task.progress_percentage}%` }}
          />
        </div>
        {task.estimated_time_remaining && (
          <div className="text-xs text-gray-500 dark:text-gray-400 mt-2">
            Estimated time remaining: {formatTime(task.estimated_time_remaining)}
          </div>
        )}
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <StatCard
          icon={<Search className="w-4 h-4" />}
          label="Found"
          value={task.sources_found}
          color="blue"
        />
        <StatCard
          icon={<FileText className="w-4 h-4" />}
          label="Scraped"
          value={task.sources_scraped}
          color="purple"
        />
        <StatCard
          icon={<CheckCircle className="w-4 h-4" />}
          label="Added"
          value={task.sources_added}
          color="green"
        />
        <StatCard
          icon={<X className="w-4 h-4" />}
          label="Failed"
          value={task.sources_failed}
          color="red"
        />
        <StatCard
          icon={<X className="w-4 h-4" />}
          label="Skipped"
          value={task.sources_skipped}
          color="orange"
        />
      </div>
    </div>
  );
}

interface StatCardProps {
  icon: React.ReactNode;
  label: string;
  value: number;
  color: 'blue' | 'purple' | 'green' | 'red' | 'orange';
}

function StatCard({ icon, label, value, color }: StatCardProps) {
  const colorClasses = {
    blue: 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/20',
    purple: 'text-purple-600 dark:text-purple-400 bg-purple-50 dark:bg-purple-900/20',
    green: 'text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/20',
    red: 'text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20',
    orange: 'text-orange-600 dark:text-orange-400 bg-orange-50 dark:bg-orange-900/20',
  };

  return (
    <div className="text-center">
      <div className={`w-10 h-10 rounded-lg ${colorClasses[color]} flex items-center justify-center mx-auto mb-2`}>
        {icon}
      </div>
      <div className="text-2xl font-bold text-gray-900 dark:text-white">{value}</div>
      <div className="text-xs text-gray-500 dark:text-gray-400">{label}</div>
    </div>
  );
}
