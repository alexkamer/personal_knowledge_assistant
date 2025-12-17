/**
 * ContextPanel Component
 *
 * Main component for displaying contextual intelligence.
 * Shows related content, AI synthesis, and suggested questions.
 */

import { Sparkles, ChevronRight, ChevronLeft } from 'lucide-react';
import { SourceType } from '@/types/context';
import { useContext } from '@/hooks/useContext';
import { RelatedContentSection } from './RelatedContentSection';
import { SynthesisSection } from './SynthesisSection';
import { SuggestedQuestionsSection } from './SuggestedQuestionsSection';
import { ContradictionsSection } from './ContradictionsSection';

export interface ContextPanelProps {
  /** Type of source being analyzed */
  sourceType: SourceType | null;

  /** ID of the source being analyzed */
  sourceId: string | null;

  /** Whether the panel is collapsed */
  isCollapsed?: boolean;

  /** Callback when toggle button is clicked */
  onToggle?: () => void;
}

/**
 * Context Panel - displays contextual intelligence for content
 *
 * Shows related content from across notes, documents, and YouTube videos,
 * along with AI-generated synthesis and suggested questions.
 */
export function ContextPanel({
  sourceType,
  sourceId,
  isCollapsed = false,
  onToggle,
}: ContextPanelProps) {
  const { data: context, isLoading, error } = useContext(sourceType, sourceId);

  // Don't render if no source provided
  if (!sourceType || !sourceId) {
    return null;
  }

  // Collapsed state - show toggle button
  if (isCollapsed) {
    return (
      <div className="fixed right-0 top-1/2 -translate-y-1/2 z-10">
        <button
          onClick={onToggle}
          className="bg-white dark:bg-stone-800 shadow-lg rounded-l-lg p-3 hover:bg-stone-50 dark:hover:bg-stone-700 transition-colors border-l-4 border-blue-600"
          aria-label="Open context panel"
        >
          <ChevronLeft className="w-5 h-5 text-blue-600" />
        </button>
      </div>
    );
  }

  // Expanded state - show full panel
  return (
    <div className="sticky top-6 bg-white dark:bg-stone-800 rounded-lg shadow-lg p-6 max-h-[calc(100vh-8rem)] overflow-y-auto border border-stone-200 dark:border-stone-700">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold flex items-center gap-2 text-stone-900 dark:text-white">
          <Sparkles className="w-5 h-5 text-blue-600" />
          Context Intelligence
        </h3>
        {onToggle && (
          <button
            onClick={onToggle}
            className="p-1 hover:bg-stone-100 dark:hover:bg-stone-700 rounded transition-colors"
            aria-label="Collapse context panel"
          >
            <ChevronRight className="w-5 h-5 text-stone-500" />
          </button>
        )}
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="flex flex-col items-center justify-center py-12 space-y-3">
          <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
          <p className="text-sm text-stone-600 dark:text-stone-400">
            Analyzing connections...
          </p>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
          <p className="text-sm text-red-800 dark:text-red-200">
            Failed to load context intelligence. Please try again.
          </p>
        </div>
      )}

      {/* Content */}
      {context && !isLoading && !error && (
        <div className="space-y-6">
          {/* Related Content */}
          {context.related_content.length > 0 ? (
            <>
              <RelatedContentSection items={context.related_content} />

              {/* Contradiction Detective */}
              {context.contradictions && context.contradictions.length > 0 && (
                <ContradictionsSection contradictions={context.contradictions} />
              )}

              {/* AI Synthesis */}
              {context.synthesis && (
                <SynthesisSection content={context.synthesis} />
              )}

              {/* Suggested Questions */}
              {context.suggested_questions.length > 0 && (
                <SuggestedQuestionsSection
                  questions={context.suggested_questions}
                />
              )}
            </>
          ) : (
            /* Empty State */
            <div className="flex flex-col items-center justify-center py-12 space-y-3">
              <Sparkles className="w-12 h-12 text-stone-300 dark:text-stone-600" />
              <p className="text-sm text-stone-600 dark:text-stone-400 text-center">
                No related content found yet.
                <br />
                Keep adding notes, documents, and videos!
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default ContextPanel;
