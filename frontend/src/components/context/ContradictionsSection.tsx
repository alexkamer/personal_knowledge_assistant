/**
 * ContradictionsSection Component
 *
 * Displays detected logical contradictions between the current source and related content.
 * Innovation: Contradiction Detective - helps users identify and resolve inconsistencies.
 */

import { useState } from 'react';
import { AlertTriangle, ChevronDown, ChevronUp, ExternalLink } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { ContradictionItem } from '@/types/context';

export interface ContradictionsSectionProps {
  /** List of detected contradictions */
  contradictions: ContradictionItem[];
}

export function ContradictionsSection({ contradictions }: ContradictionsSectionProps) {
  const [isExpanded, setIsExpanded] = useState(true);
  const navigate = useNavigate();

  if (contradictions.length === 0) {
    return null;
  }

  const handleSourceClick = (sourceType: string, sourceId: string) => {
    if (sourceType === 'note') {
      navigate('/notes');
      // Dispatch event to select the note
      setTimeout(() => {
        document.dispatchEvent(
          new CustomEvent('navigate-to-note', {
            detail: { noteId: sourceId },
          })
        );
      }, 100);
    } else if (sourceType === 'document') {
      navigate('/documents');
      // Dispatch event to select the document
      setTimeout(() => {
        document.dispatchEvent(
          new CustomEvent('navigate-to-document', {
            detail: { documentId: sourceId },
          })
        );
      }, 100);
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'high':
        return 'text-red-600 bg-red-50 dark:bg-red-900/20 border-red-300 dark:border-red-800';
      case 'medium':
        return 'text-orange-600 bg-orange-50 dark:bg-orange-900/20 border-orange-300 dark:border-orange-800';
      case 'low':
        return 'text-yellow-600 bg-yellow-50 dark:bg-yellow-900/20 border-yellow-300 dark:border-yellow-800';
      default:
        return 'text-gray-600 bg-gray-50 dark:bg-gray-900/20 border-gray-300 dark:border-gray-800';
    }
  };

  const getSeverityBadgeColor = (severity: string) => {
    switch (severity) {
      case 'high':
        return 'bg-red-100 text-red-800 dark:bg-red-900/50 dark:text-red-200';
      case 'medium':
        return 'bg-orange-100 text-orange-800 dark:bg-orange-900/50 dark:text-orange-200';
      case 'low':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/50 dark:text-yellow-200';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900/50 dark:text-gray-200';
    }
  };

  return (
    <div className="border-t border-gray-200 dark:border-gray-700 pt-6">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between hover:opacity-80 transition-opacity"
      >
        <h4 className="flex items-center gap-2 text-base font-semibold text-gray-900 dark:text-white">
          <AlertTriangle className="w-4 h-4 text-red-600 dark:text-red-400" />
          Contradiction Detective
          <span className="ml-1 px-2 py-0.5 text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900/50 dark:text-red-200 rounded-full">
            {contradictions.length}
          </span>
        </h4>
        {isExpanded ? (
          <ChevronUp className="w-5 h-5 text-gray-400" />
        ) : (
          <ChevronDown className="w-5 h-5 text-gray-400" />
        )}
      </button>

      {isExpanded && (
        <div className="mt-4 space-y-4">
          <p className="text-sm text-gray-600 dark:text-gray-400">
            AI detected potential logical contradictions in your knowledge base.
          </p>

          {contradictions.map((contradiction, index) => (
            <div
              key={index}
              className={`border rounded-lg p-4 ${getSeverityColor(contradiction.severity)}`}
            >
              {/* Header with severity and type */}
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <span className={`px-2 py-1 text-xs font-semibold rounded ${getSeverityBadgeColor(contradiction.severity)}`}>
                    {contradiction.severity.toUpperCase()}
                  </span>
                  <span className="text-xs text-gray-600 dark:text-gray-400">
                    {contradiction.contradiction_type}
                  </span>
                </div>
                <span className="text-xs text-gray-500 dark:text-gray-400">
                  {Math.round(contradiction.confidence * 100)}% confident
                </span>
              </div>

              {/* Explanation */}
              <p className="text-sm font-medium text-gray-900 dark:text-white mb-3">
                {contradiction.explanation}
              </p>

              {/* Source 1 */}
              <div className="mb-3">
                <button
                  onClick={() => handleSourceClick(contradiction.source1.type, contradiction.source1.id)}
                  className="flex items-center gap-1 text-xs font-semibold text-blue-600 dark:text-blue-400 hover:underline mb-1"
                >
                  {contradiction.source1.title}
                  <ExternalLink className="w-3 h-3" />
                </button>
                <p className="text-xs italic text-gray-700 dark:text-gray-300 pl-3 border-l-2 border-gray-300 dark:border-gray-600">
                  "{contradiction.source1.excerpt}"
                </p>
              </div>

              {/* VS divider */}
              <div className="flex items-center justify-center my-2">
                <span className="px-3 py-1 text-xs font-bold text-gray-500 dark:text-gray-400 bg-white dark:bg-gray-800 rounded">
                  VS
                </span>
              </div>

              {/* Source 2 */}
              <div>
                <button
                  onClick={() => handleSourceClick(contradiction.source2.type, contradiction.source2.id)}
                  className="flex items-center gap-1 text-xs font-semibold text-blue-600 dark:text-blue-400 hover:underline mb-1"
                >
                  {contradiction.source2.title}
                  <ExternalLink className="w-3 h-3" />
                </button>
                <p className="text-xs italic text-gray-700 dark:text-gray-300 pl-3 border-l-2 border-gray-300 dark:border-gray-600">
                  "{contradiction.source2.excerpt}"
                </p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
