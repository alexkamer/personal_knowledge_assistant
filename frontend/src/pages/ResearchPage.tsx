/**
 * Research page for autonomous web research.
 */
import { useState } from 'react';
import { Search, XCircle, Plus } from 'lucide-react';
import { useResearchTasks, useResearchTask, useResearchResults } from '@/hooks/useResearch';
import { ResearchForm } from '@/components/research/ResearchForm';
import { ResearchProgressPanel } from '@/components/research/ResearchProgressPanel';
import { ResearchResultsPanel } from '@/components/research/ResearchResultsPanel';
import { ResearchTasksList } from '@/components/research/ResearchTasksList';

export function ResearchPage() {
  const [showForm, setShowForm] = useState(false);
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'new' | 'history'>('new');

  // Fetch research tasks
  const { data: tasksData, isLoading: isLoadingTasks } = useResearchTasks();

  // Get selected task details (with polling)
  const { data: taskData } = useResearchTask(selectedTaskId);

  // Get results when task is complete
  const { data: resultsData } = useResearchResults(
    taskData?.status === 'completed' ? selectedTaskId : null
  );

  const handleStartResearch = () => {
    setShowForm(true);
    setActiveTab('new');
  };

  const handleResearchStarted = (taskId: string) => {
    setShowForm(false);
    setSelectedTaskId(taskId);
  };

  const handleTaskClick = (taskId: string) => {
    setSelectedTaskId(taskId);
    setActiveTab('new');
  };

  return (
    <div className="min-h-screen bg-stone-50 dark:bg-stone-950">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-stone-900 dark:text-white flex items-center gap-3">
                <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                  <Search className="w-6 h-6 text-white" />
                </div>
                Web Researcher
              </h1>
              <p className="mt-2 text-stone-600 dark:text-stone-400">
                Autonomous AI agent that researches topics and adds findings to your knowledge base
              </p>
            </div>
            <button
              onClick={handleStartResearch}
              className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-lg hover:from-blue-600 hover:to-purple-700 transition-all shadow-sm"
            >
              <Plus size={20} />
              New Research
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 mb-6 bg-stone-200 dark:bg-stone-800 p-1 rounded-lg w-fit">
          <button
            onClick={() => setActiveTab('new')}
            className={`px-4 py-2 rounded-md font-medium transition-all ${
              activeTab === 'new'
                ? 'bg-white dark:bg-stone-900 text-stone-900 dark:text-white shadow-sm'
                : 'text-stone-600 dark:text-stone-400 hover:text-stone-900 dark:hover:text-white'
            }`}
          >
            Active Research
          </button>
          <button
            onClick={() => setActiveTab('history')}
            className={`px-4 py-2 rounded-md font-medium transition-all ${
              activeTab === 'history'
                ? 'bg-white dark:bg-stone-900 text-stone-900 dark:text-white shadow-sm'
                : 'text-stone-600 dark:text-stone-400 hover:text-stone-900 dark:hover:text-white'
            }`}
          >
            Research History
          </button>
        </div>

        {/* Content */}
        <div className="space-y-6">
          {activeTab === 'new' ? (
            <>
              {/* Research Form */}
              {showForm && (
                <div className="bg-white dark:bg-stone-900 rounded-lg shadow-sm border border-stone-200 dark:border-stone-800 p-6">
                  <ResearchForm
                    onStarted={handleResearchStarted}
                    onCancel={() => setShowForm(false)}
                  />
                </div>
              )}

              {/* Active Research Progress */}
              {selectedTaskId && taskData && (
                <div className="space-y-6">
                  {/* Progress Panel */}
                  {taskData.status === 'running' || taskData.status === 'queued' ? (
                    <ResearchProgressPanel task={taskData} />
                  ) : null}

                  {/* Results Panel */}
                  {taskData.status === 'completed' && resultsData ? (
                    <ResearchResultsPanel results={resultsData} />
                  ) : null}

                  {/* Failed State */}
                  {taskData.status === 'failed' ? (
                    <div className="bg-white dark:bg-stone-900 rounded-lg shadow-sm border border-red-200 dark:border-red-900 p-6">
                      <div className="flex items-start gap-3">
                        <XCircle className="w-6 h-6 text-red-500 flex-shrink-0 mt-0.5" />
                        <div>
                          <h3 className="text-lg font-semibold text-red-700 dark:text-red-400">
                            Research Failed
                          </h3>
                          <p className="mt-2 text-stone-600 dark:text-stone-400">
                            {taskData.error_message || 'An unknown error occurred'}
                          </p>
                        </div>
                      </div>
                    </div>
                  ) : null}
                </div>
              )}

              {/* Empty State */}
              {!showForm && !selectedTaskId && (
                <div className="bg-white dark:bg-stone-900 rounded-lg shadow-sm border border-stone-200 dark:border-stone-800 p-12 text-center">
                  <div className="w-16 h-16 bg-gradient-to-br from-blue-100 to-purple-100 dark:from-blue-900/20 dark:to-purple-900/20 rounded-full flex items-center justify-center mx-auto mb-4">
                    <Search className="w-8 h-8 text-blue-600 dark:text-blue-400" />
                  </div>
                  <h3 className="text-lg font-semibold text-stone-900 dark:text-white mb-2">
                    No Active Research
                  </h3>
                  <p className="text-stone-600 dark:text-stone-400 mb-6">
                    Start a new research task to automatically gather information from across the web
                  </p>
                  <button
                    onClick={handleStartResearch}
                    className="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-lg hover:from-blue-600 hover:to-purple-700 transition-all shadow-sm"
                  >
                    <Plus size={20} />
                    Start Research
                  </button>
                </div>
              )}
            </>
          ) : (
            /* Research History */
            <ResearchTasksList
              tasks={tasksData?.tasks || []}
              isLoading={isLoadingTasks}
              onTaskClick={handleTaskClick}
            />
          )}
        </div>
      </div>
    </div>
  );
}
