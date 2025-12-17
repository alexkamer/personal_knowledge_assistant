/**
 * Learning Gaps Panel Component
 *
 * Displays detected foundational knowledge gaps and personalized learning paths.
 * Innovation 3: Helps users build complete understanding by revealing prerequisites.
 */

import { useState } from 'react';
import { X, AlertCircle, CheckCircle, Clock, Lightbulb, ChevronRight } from 'lucide-react';
import type { LearningGap, LearningPathResponse } from '@/services/learningGapsService';

export interface LearningGapsPanelProps {
  /** Whether the panel is visible */
  isOpen: boolean;

  /** Callback to close the panel */
  onClose: () => void;

  /** The user's question being analyzed */
  userQuestion: string;

  /** Detected learning gaps */
  gaps: LearningGap[];

  /** Optional learning path */
  learningPath?: LearningPathResponse;

  /** Loading state */
  isLoading?: boolean;

  /** Error message if detection failed */
  error?: string | null;

  /** Callback to generate learning path */
  onGeneratePath?: () => void;
}

export function LearningGapsPanel({
  isOpen,
  onClose,
  userQuestion,
  gaps,
  learningPath,
  isLoading = false,
  error = null,
  onGeneratePath,
}: LearningGapsPanelProps) {
  const [expandedGapIndex, setExpandedGapIndex] = useState<number | null>(null);

  if (!isOpen) return null;

  const getImportanceBadgeColor = (importance: string) => {
    switch (importance) {
      case 'critical':
        return 'bg-red-100 text-red-800 dark:bg-red-900/50 dark:text-red-200 border-red-300 dark:border-red-700';
      case 'important':
        return 'bg-orange-100 text-orange-800 dark:bg-orange-900/50 dark:text-orange-200 border-orange-300 dark:border-orange-700';
      case 'helpful':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900/50 dark:text-blue-200 border-blue-300 dark:border-blue-700';
      default:
        return 'bg-stone-100 text-stone-800 dark:bg-stone-900/50 dark:text-stone-200 border-stone-300 dark:border-stone-700';
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 dark:bg-black/70 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-stone-800 rounded-lg shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-stone-200 dark:border-stone-700">
          <div className="flex items-center gap-3">
            <AlertCircle className="w-6 h-6 text-blue-600 dark:text-blue-400" />
            <div>
              <h2 className="text-xl font-semibold text-stone-900 dark:text-white">
                Learning Gaps Detected
              </h2>
              <p className="text-sm text-stone-600 dark:text-stone-400 mt-1">
                Missing foundational knowledge for: "{userQuestion}"
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-stone-100 dark:hover:bg-stone-700 rounded-lg transition-colors"
            aria-label="Close panel"
          >
            <X className="w-5 h-5 text-stone-500" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {isLoading ? (
            <div className="flex flex-col items-center justify-center py-12 space-y-3">
              <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
              <p className="text-sm text-stone-600 dark:text-stone-400">
                Analyzing knowledge gaps...
              </p>
            </div>
          ) : error ? (
            <div className="flex flex-col items-center justify-center py-12 space-y-3">
              <AlertCircle className="w-16 h-16 text-red-600 dark:text-red-400" />
              <p className="text-lg font-medium text-stone-900 dark:text-white">
                Analysis Failed
              </p>
              <p className="text-sm text-stone-600 dark:text-stone-400 text-center max-w-md">
                {error}
              </p>
            </div>
          ) : gaps.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 space-y-3">
              <CheckCircle className="w-16 h-16 text-green-600 dark:text-green-400" />
              <p className="text-lg font-medium text-stone-900 dark:text-white">
                No Gaps Detected!
              </p>
              <p className="text-sm text-stone-600 dark:text-stone-400 text-center max-w-md">
                You have the foundational knowledge needed to understand this topic.
              </p>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Summary */}
              <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
                <div className="flex items-start gap-3">
                  <Lightbulb className="w-5 h-5 text-blue-600 dark:text-blue-400 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-blue-900 dark:text-blue-100">
                      Detected {gaps.length} foundational {gaps.length === 1 ? 'gap' : 'gaps'}
                    </p>
                    <p className="text-sm text-blue-700 dark:text-blue-300 mt-1">
                      Learning these prerequisites will help you understand the topic more deeply.
                    </p>
                  </div>
                </div>
              </div>

              {/* Gaps List */}
              <div className="space-y-4">
                {gaps.map((gap, index) => (
                  <div
                    key={index}
                    className="border border-stone-200 dark:border-stone-700 rounded-lg overflow-hidden"
                  >
                    {/* Gap Header */}
                    <button
                      onClick={() =>
                        setExpandedGapIndex(expandedGapIndex === index ? null : index)
                      }
                      className="w-full flex items-center justify-between p-4 hover:bg-stone-50 dark:hover:bg-stone-700/50 transition-colors"
                    >
                      <div className="flex items-center gap-3 flex-1 text-left">
                        <span
                          className={`px-2 py-1 text-xs font-semibold rounded border ${getImportanceBadgeColor(
                            gap.importance
                          )}`}
                        >
                          {gap.importance.toUpperCase()}
                        </span>
                        <h3 className="font-semibold text-stone-900 dark:text-white">
                          {gap.topic}
                        </h3>
                        <div className="flex items-center gap-1 text-xs text-stone-500 dark:text-stone-400">
                          <Clock className="w-3 h-3" />
                          <span>{gap.estimated_time}</span>
                        </div>
                      </div>
                      <ChevronRight
                        className={`w-5 h-5 text-stone-400 transition-transform ${
                          expandedGapIndex === index ? 'rotate-90' : ''
                        }`}
                      />
                    </button>

                    {/* Gap Details (Expanded) */}
                    {expandedGapIndex === index && (
                      <div className="px-4 pb-4 space-y-3 border-t border-stone-200 dark:border-stone-700 pt-3">
                        {/* Description */}
                        <div>
                          <h4 className="text-sm font-semibold text-stone-700 dark:text-stone-300 mb-1">
                            What is this?
                          </h4>
                          <p className="text-sm text-stone-600 dark:text-stone-400">
                            {gap.description}
                          </p>
                        </div>

                        {/* Prerequisite For */}
                        <div>
                          <h4 className="text-sm font-semibold text-stone-700 dark:text-stone-300 mb-1">
                            Why it matters
                          </h4>
                          <p className="text-sm text-stone-600 dark:text-stone-400">
                            {gap.prerequisite_for}
                          </p>
                        </div>

                        {/* Learning Resources */}
                        <div>
                          <h4 className="text-sm font-semibold text-stone-700 dark:text-stone-300 mb-1">
                            How to learn
                          </h4>
                          <div className="text-sm text-stone-600 dark:text-stone-400 bg-stone-50 dark:bg-stone-800 rounded p-3">
                            {gap.learning_resources.map((resource, i) => (
                              <p key={i} className="mb-1 last:mb-0">
                                {resource}
                              </p>
                            ))}
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>

              {/* Learning Path Section */}
              {learningPath ? (
                <div className="bg-gradient-to-r from-purple-50 to-blue-50 dark:from-purple-900/20 dark:to-blue-900/20 border border-purple-200 dark:border-purple-800 rounded-lg p-5">
                  <h3 className="text-lg font-semibold text-stone-900 dark:text-white mb-2 flex items-center gap-2">
                    <Lightbulb className="w-5 h-5 text-purple-600 dark:text-purple-400" />
                    Recommended Learning Path
                  </h3>
                  <p className="text-sm text-stone-600 dark:text-stone-400 mb-4">
                    Follow this sequence to build complete understanding ({learningPath.total_estimated_time})
                  </p>
                  <ol className="space-y-2">
                    {learningPath.learning_sequence.map((step, index) => (
                      <li key={index} className="flex items-start gap-3">
                        <span className="flex items-center justify-center w-6 h-6 rounded-full bg-purple-600 text-white text-sm font-semibold flex-shrink-0">
                          {index + 1}
                        </span>
                        <span className="text-sm text-stone-700 dark:text-stone-300 pt-0.5">
                          {step}
                        </span>
                      </li>
                    ))}
                  </ol>
                </div>
              ) : (
                onGeneratePath && (
                  <button
                    onClick={onGeneratePath}
                    className="w-full py-3 px-4 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
                  >
                    <Lightbulb className="w-5 h-5" />
                    Generate Learning Path
                  </button>
                )
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default LearningGapsPanel;
