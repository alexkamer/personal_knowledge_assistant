/**
 * RelatedContentSection Component
 *
 * Displays a list of semantically related content items.
 */

import { FileText, Youtube, StickyNote, ExternalLink } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { RelatedContentItem, SourceType } from '@/types/context';

export interface RelatedContentSectionProps {
  /** List of related content items */
  items: RelatedContentItem[];
}

/**
 * Get icon component for a source type
 */
function getSourceIcon(sourceType: SourceType) {
  switch (sourceType) {
    case 'note':
      return StickyNote;
    case 'document':
      return FileText;
    case 'youtube':
      return Youtube;
  }
}

/**
 * Get display label for a source type
 */
function getSourceLabel(sourceType: SourceType): string {
  switch (sourceType) {
    case 'note':
      return 'Note';
    case 'document':
      return 'Document';
    case 'youtube':
      return 'YouTube Video';
  }
}

/**
 * Get similarity badge color based on score
 */
function getSimilarityColor(score: number): string {
  if (score >= 0.8) return 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400';
  if (score >= 0.6) return 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400';
  return 'bg-stone-100 text-stone-800 dark:bg-stone-700 dark:text-stone-300';
}

/**
 * Format timestamp as MM:SS
 */
function formatTimestamp(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

/**
 * Related Content Section - displays related items with navigation
 */
export function RelatedContentSection({ items }: RelatedContentSectionProps) {
  const navigate = useNavigate();

  const handleItemClick = (item: RelatedContentItem) => {
    switch (item.source_type) {
      case 'note':
        navigate('/notes');
        // Dispatch custom event to select note
        document.dispatchEvent(
          new CustomEvent('navigate-to-note', {
            detail: { noteId: item.source_id },
          })
        );
        break;
      case 'document':
        navigate('/documents');
        // Dispatch custom event to select document
        document.dispatchEvent(
          new CustomEvent('navigate-to-document', {
            detail: { documentId: item.source_id },
          })
        );
        break;
      case 'youtube':
        if (item.timestamp) {
          navigate(`/youtube?v=${item.source_id}&t=${Math.floor(item.timestamp)}`);
        } else {
          navigate(`/youtube?v=${item.source_id}`);
        }
        break;
    }
  };

  return (
    <div>
      <h4 className="text-sm font-semibold text-stone-700 dark:text-stone-300 mb-3">
        Related Content
      </h4>
      <div className="space-y-3">
        {items.map((item) => {
          const Icon = getSourceIcon(item.source_type);
          const label = getSourceLabel(item.source_type);
          const similarityColor = getSimilarityColor(item.similarity_score);

          return (
            <button
              key={`${item.source_type}-${item.source_id}`}
              onClick={() => handleItemClick(item)}
              className="w-full text-left p-3 bg-stone-50 dark:bg-stone-900/50 hover:bg-stone-100 dark:hover:bg-stone-900 rounded-lg transition-colors border border-stone-200 dark:border-stone-700 group"
            >
              {/* Header */}
              <div className="flex items-start justify-between gap-2 mb-2">
                <div className="flex items-center gap-2 flex-1 min-w-0">
                  <Icon className="w-4 h-4 text-stone-500 dark:text-stone-400 flex-shrink-0" />
                  <span className="text-xs text-stone-600 dark:text-stone-400 flex-shrink-0">
                    {label}
                  </span>
                  {item.timestamp !== undefined && (
                    <span className="text-xs text-blue-600 dark:text-blue-400 flex-shrink-0">
                      {formatTimestamp(item.timestamp)}
                    </span>
                  )}
                </div>
                <ExternalLink className="w-4 h-4 text-stone-400 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0" />
              </div>

              {/* Title */}
              <h5 className="text-sm font-medium text-stone-900 dark:text-white mb-2 line-clamp-2">
                {item.source_title}
              </h5>

              {/* Preview */}
              {item.preview && (
                <p className="text-xs text-stone-600 dark:text-stone-400 line-clamp-2 mb-2">
                  {item.preview}
                </p>
              )}

              {/* Footer */}
              <div className="flex items-center gap-2">
                <span
                  className={`text-xs px-2 py-0.5 rounded-full font-medium ${similarityColor}`}
                >
                  {Math.round(item.similarity_score * 100)}% match
                </span>
                {item.chunk_count > 1 && (
                  <span className="text-xs text-stone-500 dark:text-stone-400">
                    {item.chunk_count} sections
                  </span>
                )}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}

export default RelatedContentSection;
