/**
 * Token Usage Indicator Component
 *
 * Displays token usage statistics for a conversation with visual progress bar.
 */
import { useEffect, useState } from 'react';
import { chatService } from '@/services/chatService';

interface TokenUsageProps {
  conversationId: string | null;
  model?: string;
}

export function TokenUsage({ conversationId, model = 'qwen2.5:14b' }: TokenUsageProps) {
  const [usage, setUsage] = useState<{
    total_tokens: number;
    limit: number;
    usage_percent: number;
    remaining: number;
    is_warning: boolean;
    is_critical: boolean;
    messages_count: number;
  } | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!conversationId) {
      setUsage(null);
      return;
    }

    const fetchTokenUsage = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await chatService.getTokenUsage(conversationId, model);
        setUsage(data);
      } catch (err) {
        console.error('Failed to fetch token usage:', err);
        setError('Failed to load token usage');
      } finally {
        setLoading(false);
      }
    };

    fetchTokenUsage();
  }, [conversationId, model]);

  if (!conversationId || loading) {
    return null;
  }

  if (error) {
    return (
      <div className="text-xs text-stone-500 dark:text-stone-400">
        {error}
      </div>
    );
  }

  if (!usage) {
    return null;
  }

  // Determine color based on usage
  let colorClass = 'bg-green-500';
  let bgColorClass = 'bg-green-100 dark:bg-green-900/30';
  let textColorClass = 'text-green-700 dark:text-green-300';

  if (usage.is_critical) {
    colorClass = 'bg-red-500';
    bgColorClass = 'bg-red-100 dark:bg-red-900/30';
    textColorClass = 'text-red-700 dark:text-red-300';
  } else if (usage.is_warning) {
    colorClass = 'bg-yellow-500';
    bgColorClass = 'bg-yellow-100 dark:bg-yellow-900/30';
    textColorClass = 'text-yellow-700 dark:text-yellow-300';
  }

  return (
    <div className="flex items-center gap-3">
      {/* Token usage bar */}
      <div className="flex-1 min-w-[120px]">
        <div className="flex items-center justify-between text-xs text-stone-600 dark:text-stone-400 mb-1">
          <span>Context</span>
          <span className={textColorClass}>
            {usage.usage_percent.toFixed(1)}%
          </span>
        </div>
        <div className={`h-2 rounded-full ${bgColorClass} overflow-hidden`}>
          <div
            className={`h-full ${colorClass} transition-all duration-300`}
            style={{ width: `${Math.min(usage.usage_percent, 100)}%` }}
          />
        </div>
      </div>

      {/* Token count details */}
      <div className="text-xs text-stone-600 dark:text-stone-400 whitespace-nowrap">
        <span className="font-medium">{usage.total_tokens.toLocaleString()}</span>
        <span className="text-stone-400 dark:text-stone-500"> / </span>
        <span>{usage.limit.toLocaleString()}</span>
      </div>

      {/* Warning/Critical badge */}
      {usage.is_critical && (
        <div className="flex items-center gap-1 px-2 py-0.5 bg-red-100 dark:bg-red-900/30 rounded text-xs text-red-700 dark:text-red-300 font-medium">
          <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
          Critical
        </div>
      )}
      {usage.is_warning && !usage.is_critical && (
        <div className="flex items-center gap-1 px-2 py-0.5 bg-yellow-100 dark:bg-yellow-900/30 rounded text-xs text-yellow-700 dark:text-yellow-300 font-medium">
          <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
          Warning
        </div>
      )}
    </div>
  );
}
