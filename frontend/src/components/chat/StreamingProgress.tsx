/**
 * Streaming progress indicator showing real-time word count and status.
 */
import { ActivitySquare } from 'lucide-react';

interface StreamingProgressProps {
  content: string;
  status?: string;
}

export function StreamingProgress({ content, status }: StreamingProgressProps) {
  // Count words in the streamed content
  const wordCount = content.trim().split(/\s+/).filter(word => word.length > 0).length;

  // Calculate approximate reading time (assuming 200 words per minute)
  const readingTimeMinutes = Math.ceil(wordCount / 200);

  return (
    <div className="flex items-center gap-3 px-4 py-2 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg text-xs">
      <div className="flex items-center gap-2">
        <ActivitySquare size={14} className="text-blue-600 dark:text-blue-400 animate-pulse" />
        <span className="font-medium text-blue-700 dark:text-blue-300">
          {status || 'Generating'}
        </span>
      </div>
      <div className="flex items-center gap-4 text-gray-600 dark:text-gray-400">
        <span>
          {wordCount} {wordCount === 1 ? 'word' : 'words'}
        </span>
        {wordCount > 0 && (
          <span>
            ~{readingTimeMinutes} min read
          </span>
        )}
      </div>
    </div>
  );
}
