/**
 * Knowledge Evolution Timeline Component
 *
 * Displays a visual timeline showing how understanding of topics has evolved over time.
 * Shows snapshots, thought diffs, and learning progress.
 */

import { useState } from 'react';
import { X, Clock, Brain, TrendingUp, Search, Calendar } from 'lucide-react';
import { ThoughtDiffViewer } from './ThoughtDiffViewer';
import { useSnapshots, useEvolution, useTimeline } from '@/hooks/useKnowledgeEvolution';

export interface KnowledgeEvolutionTimelineProps {
  /** Whether the timeline modal is visible */
  isOpen: boolean;

  /** Callback to close the timeline */
  onClose: () => void;

  /** Optional initial topic to display */
  initialTopic?: string;
}

export function KnowledgeEvolutionTimeline({
  isOpen,
  onClose,
  initialTopic,
}: KnowledgeEvolutionTimelineProps) {
  const [selectedTopic, setSelectedTopic] = useState<string | null>(initialTopic || null);
  const [searchQuery, setSearchQuery] = useState('');

  const { data: timeline, isLoading: isLoadingTimeline } = useTimeline();
  const { data: snapshots, isLoading: isLoadingSnapshots } = useSnapshots(selectedTopic);
  const { data: evolution, isLoading: isLoadingEvolution } = useEvolution(selectedTopic);

  if (!isOpen) return null;

  const filteredTopics = timeline?.topics.filter((topic) =>
    topic.topic.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
    if (diffDays < 365) return `${Math.floor(diffDays / 30)} months ago`;
    return `${Math.floor(diffDays / 365)} years ago`;
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600 bg-green-100 dark:bg-green-900/50 dark:text-green-200';
    if (confidence >= 0.6) return 'text-yellow-600 bg-yellow-100 dark:bg-yellow-900/50 dark:text-yellow-200';
    return 'text-red-600 bg-red-100 dark:bg-red-900/50 dark:text-red-200';
  };

  return (
    <div className="fixed inset-0 bg-black/50 dark:bg-black/70 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-stone-800 rounded-lg shadow-2xl max-w-6xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="p-6 border-b border-stone-200 dark:border-stone-700">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <Clock className="w-6 h-6 text-purple-600 dark:text-purple-400" />
              <div>
                <h2 className="text-xl font-semibold text-stone-900 dark:text-white">
                  Knowledge Evolution Timeline
                </h2>
                <p className="text-sm text-stone-600 dark:text-stone-400 mt-1">
                  Track how your understanding evolves over time
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-stone-100 dark:hover:bg-stone-700 rounded-lg transition-colors"
              aria-label="Close timeline"
            >
              <X className="w-5 h-5 text-stone-500" />
            </button>
          </div>

          {/* Search Bar */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-stone-400" />
            <input
              type="text"
              placeholder="Search topics..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-stone-300 dark:border-stone-600 rounded-lg focus:ring-2 focus:ring-purple-600 focus:border-transparent dark:bg-stone-700 dark:text-white"
            />
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto">
          <div className="grid grid-cols-1 lg:grid-cols-3 h-full">
            {/* Topics Sidebar */}
            <div className="lg:col-span-1 border-r border-stone-200 dark:border-stone-700 p-4 space-y-3 overflow-y-auto">
              <h3 className="text-sm font-semibold text-stone-700 dark:text-stone-300 mb-3">
                Your Learning Journey
              </h3>

              {isLoadingTimeline ? (
                <div className="flex items-center justify-center py-8">
                  <div className="w-8 h-8 border-4 border-purple-600 border-t-transparent rounded-full animate-spin" />
                </div>
              ) : filteredTopics && filteredTopics.length > 0 ? (
                filteredTopics.map((item) => (
                  <button
                    key={item.topic}
                    onClick={() => setSelectedTopic(item.topic)}
                    className={`w-full text-left p-3 rounded-lg transition-colors ${
                      selectedTopic === item.topic
                        ? 'bg-purple-100 dark:bg-purple-900/50 border-2 border-purple-600'
                        : 'bg-stone-50 dark:bg-stone-700 hover:bg-stone-100 dark:hover:bg-stone-600 border-2 border-transparent'
                    }`}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <h4 className="font-semibold text-sm text-stone-900 dark:text-white">
                        {item.topic}
                      </h4>
                      <span
                        className={`text-xs px-2 py-0.5 rounded ${getConfidenceColor(
                          item.current_confidence
                        )}`}
                      >
                        {Math.round(item.current_confidence * 100)}%
                      </span>
                    </div>
                    <div className="flex items-center gap-2 text-xs text-stone-600 dark:text-stone-400">
                      <Calendar className="w-3 h-3" />
                      <span>{formatDate(item.last_snapshot_date)}</span>
                    </div>
                    <div className="mt-2 text-xs text-stone-500 dark:text-stone-400">
                      {item.snapshot_count} {item.snapshot_count === 1 ? 'snapshot' : 'snapshots'}
                    </div>
                  </button>
                ))
              ) : (
                <div className="text-center py-8 text-stone-500 dark:text-stone-400">
                  <Brain className="w-12 h-12 mx-auto mb-3 opacity-50" />
                  <p className="text-sm">No learning snapshots yet</p>
                  <p className="text-xs mt-1">
                    Create snapshots from your conversations to track progress
                  </p>
                </div>
              )}
            </div>

            {/* Detail View */}
            <div className="lg:col-span-2 p-6 overflow-y-auto">
              {!selectedTopic ? (
                <div className="flex flex-col items-center justify-center h-full text-stone-500 dark:text-stone-400">
                  <TrendingUp className="w-16 h-16 mb-4 opacity-50" />
                  <p className="text-lg font-medium">Select a topic to view evolution</p>
                  <p className="text-sm mt-2">See how your understanding has grown over time</p>
                </div>
              ) : isLoadingSnapshots || isLoadingEvolution ? (
                <div className="flex items-center justify-center h-full">
                  <div className="w-12 h-12 border-4 border-purple-600 border-t-transparent rounded-full animate-spin" />
                </div>
              ) : snapshots && snapshots.length > 0 ? (
                <div className="space-y-6">
                  <div>
                    <h3 className="text-lg font-semibold text-stone-900 dark:text-white mb-2">
                      {selectedTopic}
                    </h3>
                    <p className="text-sm text-stone-600 dark:text-stone-400">
                      {snapshots.length} {snapshots.length === 1 ? 'snapshot' : 'snapshots'} recorded
                    </p>
                  </div>

                  {/* Evolution Analysis */}
                  {evolution && snapshots.length >= 2 && (
                    <ThoughtDiffViewer
                      earlierSnapshot={evolution.earlier_snapshot}
                      laterSnapshot={evolution.later_snapshot}
                      evolutionAnalysis={evolution}
                    />
                  )}

                  {/* All Snapshots Timeline */}
                  <div className="border-t border-stone-200 dark:border-stone-700 pt-6">
                    <h4 className="text-sm font-semibold text-stone-700 dark:text-stone-300 mb-4">
                      Snapshot History
                    </h4>
                    <div className="space-y-4">
                      {snapshots
                        .slice()
                        .reverse()
                        .map((snapshot, index) => (
                          <div
                            key={snapshot.id}
                            className="flex gap-4 relative"
                          >
                            {/* Timeline Line */}
                            {index < snapshots.length - 1 && (
                              <div className="absolute left-3 top-8 bottom-0 w-0.5 bg-purple-300 dark:bg-purple-700" />
                            )}

                            {/* Timeline Node */}
                            <div className="flex-shrink-0">
                              <div className="w-6 h-6 rounded-full bg-purple-600 border-4 border-white dark:border-stone-800 relative z-10" />
                            </div>

                            {/* Snapshot Card */}
                            <div className="flex-1 bg-stone-50 dark:bg-stone-700 rounded-lg p-4 mb-4">
                              <div className="flex items-center justify-between mb-2">
                                <span className="text-xs text-stone-600 dark:text-stone-400">
                                  {new Date(snapshot.timestamp).toLocaleString()}
                                </span>
                                <span
                                  className={`text-xs px-2 py-0.5 rounded ${getConfidenceColor(
                                    snapshot.confidence
                                  )}`}
                                >
                                  {Math.round(snapshot.confidence * 100)}% confidence
                                </span>
                              </div>
                              <p className="text-sm text-stone-700 dark:text-stone-300 mb-3">
                                {snapshot.understanding}
                              </p>
                              {snapshot.key_concepts.length > 0 && (
                                <div className="flex flex-wrap gap-1">
                                  {snapshot.key_concepts.map((concept, i) => (
                                    <span
                                      key={i}
                                      className="text-xs px-2 py-1 bg-blue-100 text-blue-800 dark:bg-blue-900/50 dark:text-blue-200 rounded"
                                    >
                                      {concept}
                                    </span>
                                  ))}
                                </div>
                              )}
                            </div>
                          </div>
                        ))}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center h-full text-stone-500 dark:text-stone-400">
                  <Brain className="w-16 h-16 mb-4 opacity-50" />
                  <p className="text-lg font-medium">No snapshots for this topic</p>
                  <p className="text-sm mt-2">Start a conversation to create your first snapshot</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default KnowledgeEvolutionTimeline;
