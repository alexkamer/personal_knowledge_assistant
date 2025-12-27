/**
 * Tool call card component for displaying agent reasoning steps
 */
import { ChevronDown, ChevronRight, Wrench, CheckCircle, XCircle, Loader2, RotateCw } from 'lucide-react';
import { useState } from 'react';
import { cn } from '../../lib/utils';

export interface ToolCallCardProps {
  toolName: string;
  parameters: Record<string, any>;
  result?: any;
  error?: string;
  status: 'pending' | 'success' | 'error';
  thought?: string;
  onRetry?: () => void;
}

export function ToolCallCard({
  toolName,
  parameters,
  result,
  error,
  status,
  thought,
  onRetry
}: ToolCallCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const statusConfig = {
    pending: {
      icon: Loader2,
      iconClass: 'text-blue-600 dark:text-blue-400 animate-spin',
      borderClass: 'border-blue-200 dark:border-blue-800',
      bgClass: 'bg-blue-50 dark:bg-blue-900/20',
      textClass: 'text-blue-700 dark:text-blue-300'
    },
    success: {
      icon: CheckCircle,
      iconClass: 'text-green-600 dark:text-green-400',
      borderClass: 'border-green-200 dark:border-green-800',
      bgClass: 'bg-green-50 dark:bg-green-900/20',
      textClass: 'text-green-700 dark:text-green-300'
    },
    error: {
      icon: XCircle,
      iconClass: 'text-red-600 dark:text-red-400',
      borderClass: 'border-red-200 dark:border-red-800',
      bgClass: 'bg-red-50 dark:bg-red-900/20',
      textClass: 'text-red-700 dark:text-red-300'
    }
  };

  const config = statusConfig[status];
  const StatusIcon = config.icon;

  // Format tool name for display
  const displayToolName = toolName
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase());

  return (
    <div className={cn(
      "rounded-lg border p-3 mb-3 transition-colors",
      config.borderClass,
      config.bgClass
    )}>
      {/* Header - Always visible */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center gap-2 w-full text-left"
      >
        {isExpanded ? (
          <ChevronDown size={16} className="text-gray-600 dark:text-gray-400 flex-shrink-0" />
        ) : (
          <ChevronRight size={16} className="text-gray-600 dark:text-gray-400 flex-shrink-0" />
        )}
        <Wrench size={16} className="text-gray-600 dark:text-gray-400 flex-shrink-0" />
        <span className={cn("font-medium text-sm flex-grow", config.textClass)}>
          {displayToolName}
        </span>
        <StatusIcon size={16} className={cn("flex-shrink-0", config.iconClass)} />
      </button>

      {/* Thought or Error preview - Show when collapsed */}
      {!isExpanded && thought && status !== 'error' && (
        <p className="mt-2 text-xs text-gray-600 dark:text-gray-400 ml-8 italic">
          "{thought}"
        </p>
      )}
      {!isExpanded && status === 'error' && error && (
        <p className="mt-2 text-xs text-red-600 dark:text-red-400 ml-8">
          {error.length > 100 ? `${error.substring(0, 100)}...` : error}
        </p>
      )}

      {/* Expanded content */}
      {isExpanded && (
        <div className="mt-3 ml-8 space-y-2 text-xs">
          {/* Thought */}
          {thought && (
            <div>
              <p className="font-medium text-gray-700 dark:text-gray-300 mb-1">Reasoning:</p>
              <p className="text-gray-600 dark:text-gray-400 italic">"{thought}"</p>
            </div>
          )}

          {/* Parameters */}
          <div>
            <p className="font-medium text-gray-700 dark:text-gray-300 mb-1">Parameters:</p>
            <div className="bg-white dark:bg-gray-800 rounded p-2 border border-gray-200 dark:border-gray-700">
              <pre className="text-xs text-gray-700 dark:text-gray-300 whitespace-pre-wrap font-mono">
                {JSON.stringify(parameters, null, 2)}
              </pre>
            </div>
          </div>

          {/* Result */}
          {status === 'success' && result && (
            <div>
              <p className="font-medium text-gray-700 dark:text-gray-300 mb-1">Result:</p>
              <div className="bg-white dark:bg-gray-800 rounded p-2 border border-gray-200 dark:border-gray-700">
                {typeof result === 'string' ? (
                  <p className="text-gray-700 dark:text-gray-300">{result}</p>
                ) : (
                  <pre className="text-xs text-gray-700 dark:text-gray-300 whitespace-pre-wrap font-mono">
                    {JSON.stringify(result, null, 2)}
                  </pre>
                )}
              </div>
            </div>
          )}

          {/* Error */}
          {status === 'error' && error && (
            <div>
              <p className="font-medium text-red-700 dark:text-red-300 mb-1">Error:</p>
              <div className="bg-white dark:bg-gray-800 rounded p-2 border border-red-200 dark:border-red-700">
                <p className="text-red-700 dark:text-red-300">{error}</p>
              </div>
              {onRetry && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onRetry();
                  }}
                  className="mt-2 flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-white bg-red-600 hover:bg-red-700 rounded-md transition-colors"
                  title="Retry this tool call"
                >
                  <RotateCw size={14} />
                  <span>Retry</span>
                </button>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
