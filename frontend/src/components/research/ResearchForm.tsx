/**
 * Research form component for starting new research.
 */
import { useState } from 'react';
import { Loader2, Search } from 'lucide-react';
import { useStartResearch } from '@/hooks/useResearch';

interface ResearchFormProps {
  onStarted: (taskId: string) => void;
  onCancel: () => void;
}

export function ResearchForm({ onStarted, onCancel }: ResearchFormProps) {
  const [query, setQuery] = useState('');
  const [maxSources, setMaxSources] = useState(10);
  const [depth, setDepth] = useState<'quick' | 'thorough' | 'deep'>('thorough');

  const startResearch = useStartResearch();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!query.trim()) return;

    try {
      const result = await startResearch.mutateAsync({
        query: query.trim(),
        max_sources: maxSources,
        depth,
      });

      onStarted(result.task_id);
    } catch (error) {
      console.error('Failed to start research:', error);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-stone-900 dark:text-white mb-4">
          Start New Research
        </h2>
        <p className="text-sm text-stone-600 dark:text-stone-400 mb-6">
          The AI agent will search the web, evaluate sources, and add high-quality information to
          your knowledge base.
        </p>
      </div>

      {/* Query Input */}
      <div>
        <label
          htmlFor="query"
          className="block text-sm font-medium text-stone-900 dark:text-white mb-2"
        >
          Research Question
        </label>
        <textarea
          id="query"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="What would you like to research? (e.g., 'Latest developments in transformer optimization')"
          className="w-full px-4 py-3 bg-stone-50 dark:bg-stone-800 border border-stone-200 dark:border-stone-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 resize-none text-stone-900 dark:text-white placeholder-stone-400 dark:placeholder-stone-500"
          rows={3}
          required
        />
      </div>

      {/* Max Sources */}
      <div>
        <label
          htmlFor="maxSources"
          className="block text-sm font-medium text-stone-900 dark:text-white mb-2"
        >
          Maximum Sources: {maxSources}
        </label>
        <input
          type="range"
          id="maxSources"
          min="3"
          max="20"
          value={maxSources}
          onChange={(e) => setMaxSources(Number(e.target.value))}
          className="w-full"
        />
        <div className="flex justify-between text-xs text-stone-500 dark:text-stone-400 mt-1">
          <span>3 (Quick)</span>
          <span>20 (Comprehensive)</span>
        </div>
      </div>

      {/* Depth */}
      <div>
        <label className="block text-sm font-medium text-stone-900 dark:text-white mb-3">
          Research Depth
        </label>
        <div className="grid grid-cols-3 gap-3">
          {[
            { value: 'quick', label: 'Quick', desc: '~2 min' },
            { value: 'thorough', label: 'Thorough', desc: '~5 min' },
            { value: 'deep', label: 'Deep', desc: '~10 min' },
          ].map((option) => (
            <button
              key={option.value}
              type="button"
              onClick={() => setDepth(option.value as typeof depth)}
              className={`p-3 rounded-lg border-2 transition-all ${
                depth === option.value
                  ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                  : 'border-stone-200 dark:border-stone-700 hover:border-stone-300 dark:hover:border-stone-600'
              }`}
            >
              <div className="font-medium text-stone-900 dark:text-white">{option.label}</div>
              <div className="text-xs text-stone-500 dark:text-stone-400 mt-1">{option.desc}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-3 pt-4">
        <button
          type="submit"
          disabled={startResearch.isPending || !query.trim()}
          className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-lg hover:from-blue-600 hover:to-purple-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
        >
          {startResearch.isPending ? (
            <>
              <Loader2 size={20} className="animate-spin" />
              Starting...
            </>
          ) : (
            <>
              <Search size={20} />
              Start Research
            </>
          )}
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 text-stone-700 dark:text-stone-300 hover:bg-stone-100 dark:hover:bg-stone-800 rounded-lg transition-all"
        >
          Cancel
        </button>
      </div>

      {startResearch.isError && (
        <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
          <p className="text-sm text-red-700 dark:text-red-400">
            Failed to start research. Please try again.
          </p>
        </div>
      )}
    </form>
  );
}
