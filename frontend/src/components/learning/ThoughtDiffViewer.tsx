/**
 * Thought Diff Viewer Component
 *
 * Displays git-diff-style comparison of understanding between two snapshots.
 * Shows added concepts (green), removed misconceptions (red), and confidence changes.
 */

import { TrendingUp, TrendingDown, Plus, Minus, AlertCircle, CheckCircle } from 'lucide-react';
import type { ConceptualSnapshot, EvolutionAnalysis } from '@/services/knowledgeEvolutionService';

export interface ThoughtDiffViewerProps {
  earlierSnapshot: ConceptualSnapshot;
  laterSnapshot: ConceptualSnapshot;
  evolutionAnalysis: EvolutionAnalysis;
}

export function ThoughtDiffViewer({
  earlierSnapshot,
  laterSnapshot,
  evolutionAnalysis,
}: ThoughtDiffViewerProps) {
  const confidenceChange = laterSnapshot.confidence - earlierSnapshot.confidence;
  const confidencePercent = Math.round(confidenceChange * 100);

  return (
    <div className="space-y-6">
      {/* Header with Confidence Change */}
      <div className="flex items-center justify-between p-4 bg-gradient-to-r from-purple-50 to-blue-50 dark:from-purple-900/20 dark:to-blue-900/20 rounded-lg border border-purple-200 dark:border-purple-800">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Understanding Evolution
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            {new Date(earlierSnapshot.timestamp).toLocaleDateString()} →{' '}
            {new Date(laterSnapshot.timestamp).toLocaleDateString()}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {confidenceChange > 0 ? (
            <TrendingUp className="w-6 h-6 text-green-600 dark:text-green-400" />
          ) : confidenceChange < 0 ? (
            <TrendingDown className="w-6 h-6 text-red-600 dark:text-red-400" />
          ) : null}
          <div className="text-right">
            <div
              className={`text-2xl font-bold ${
                confidenceChange > 0
                  ? 'text-green-600 dark:text-green-400'
                  : confidenceChange < 0
                  ? 'text-red-600 dark:text-red-400'
                  : 'text-gray-600 dark:text-gray-400'
              }`}
            >
              {confidenceChange > 0 ? '+' : ''}
              {confidencePercent}%
            </div>
            <div className="text-xs text-gray-600 dark:text-gray-400">Confidence Change</div>
          </div>
        </div>
      </div>

      {/* Side-by-Side Comparison */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Before */}
        <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
          <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2">
            <span className="text-red-600 dark:text-red-400">Before</span>
            <span className="text-xs text-gray-500">
              ({Math.round(earlierSnapshot.confidence * 100)}% confident)
            </span>
          </h4>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
            {earlierSnapshot.understanding}
          </p>
          {earlierSnapshot.misconceptions.length > 0 && (
            <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
              <p className="text-xs font-semibold text-red-700 dark:text-red-300 mb-2">
                Misconceptions:
              </p>
              {earlierSnapshot.misconceptions.map((misconception, i) => (
                <div key={i} className="flex items-start gap-2 text-xs text-red-600 dark:text-red-400 mb-1">
                  <AlertCircle className="w-3 h-3 mt-0.5 flex-shrink-0" />
                  <span>{misconception}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* After */}
        <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
          <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2">
            <span className="text-green-600 dark:text-green-400">After</span>
            <span className="text-xs text-gray-500">
              ({Math.round(laterSnapshot.confidence * 100)}% confident)
            </span>
          </h4>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
            {laterSnapshot.understanding}
          </p>
          {evolutionAnalysis.misconceptions_corrected.length > 0 && (
            <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
              <p className="text-xs font-semibold text-green-700 dark:text-green-300 mb-2">
                Misconceptions Corrected:
              </p>
              {evolutionAnalysis.misconceptions_corrected.map((correction, i) => (
                <div key={i} className="flex items-start gap-2 text-xs text-green-600 dark:text-green-400 mb-1">
                  <CheckCircle className="w-3 h-3 mt-0.5 flex-shrink-0" />
                  <span>{correction}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Diff-Style Changes */}
      <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 bg-gray-50 dark:bg-gray-900">
        <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-3">
          Conceptual Diff
        </h4>
        <div className="space-y-1 font-mono text-xs">
          {/* Added Concepts */}
          {evolutionAnalysis.concepts_gained.map((concept, i) => (
            <div key={`gained-${i}`} className="flex items-start gap-2 text-green-700 dark:text-green-300 bg-green-50 dark:bg-green-900/20 px-2 py-1 rounded">
              <Plus className="w-3 h-3 mt-0.5 flex-shrink-0" />
              <span>{concept}</span>
            </div>
          ))}

          {/* Removed Concepts (usually misconceptions) */}
          {evolutionAnalysis.concepts_lost.map((concept, i) => (
            <div key={`lost-${i}`} className="flex items-start gap-2 text-red-700 dark:text-red-300 bg-red-50 dark:bg-red-900/20 px-2 py-1 rounded">
              <Minus className="w-3 h-3 mt-0.5 flex-shrink-0" />
              <span className="line-through">{concept}</span>
            </div>
          ))}

          {evolutionAnalysis.concepts_gained.length === 0 &&
            evolutionAnalysis.concepts_lost.length === 0 && (
              <p className="text-gray-500 dark:text-gray-400 italic">
                No conceptual changes detected
              </p>
            )}
        </div>
      </div>

      {/* Learning Insights */}
      {evolutionAnalysis.insights.length > 0 && (
        <div className="border border-blue-200 dark:border-blue-800 rounded-lg p-4 bg-blue-50 dark:bg-blue-900/20">
          <h4 className="text-sm font-semibold text-blue-900 dark:text-blue-100 mb-3">
            Learning Insights
          </h4>
          <ul className="space-y-2">
            {evolutionAnalysis.insights.map((insight, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-blue-700 dark:text-blue-300">
                <span className="text-blue-600 dark:text-blue-400 mt-0.5">→</span>
                {insight}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Learning Velocity */}
      <div className="flex items-center justify-between p-3 bg-purple-50 dark:bg-purple-900/20 rounded-lg border border-purple-200 dark:border-purple-800">
        <span className="text-sm font-medium text-purple-900 dark:text-purple-100">
          Learning Velocity:
        </span>
        <span className="text-sm font-bold text-purple-600 dark:text-purple-400">
          {evolutionAnalysis.learning_velocity}
        </span>
      </div>
    </div>
  );
}

export default ThoughtDiffViewer;
