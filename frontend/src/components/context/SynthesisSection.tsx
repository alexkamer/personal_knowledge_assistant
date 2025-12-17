/**
 * SynthesisSection Component
 *
 * Displays AI-generated synthesis of content connections.
 */

import { useState } from 'react';
import { Lightbulb, ChevronDown, ChevronUp } from 'lucide-react';

export interface SynthesisSectionProps {
  /** AI-generated synthesis text */
  content: string;
}

/**
 * Synthesis Section - shows AI-generated insights with expand/collapse
 */
export function SynthesisSection({ content }: SynthesisSectionProps) {
  const [isExpanded, setIsExpanded] = useState(true);

  return (
    <div className="border-t border-stone-200 dark:border-stone-700 pt-6">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between mb-3 text-left hover:opacity-80 transition-opacity"
      >
        <h4 className="text-sm font-semibold text-stone-700 dark:text-stone-300 flex items-center gap-2">
          <Lightbulb className="w-4 h-4 text-yellow-600 dark:text-yellow-500" />
          AI Synthesis
        </h4>
        {isExpanded ? (
          <ChevronUp className="w-4 h-4 text-stone-500" />
        ) : (
          <ChevronDown className="w-4 h-4 text-stone-500" />
        )}
      </button>

      {isExpanded && (
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
          <p className="text-sm text-stone-800 dark:text-stone-200 leading-relaxed">
            {content}
          </p>
        </div>
      )}
    </div>
  );
}

export default SynthesisSection;
