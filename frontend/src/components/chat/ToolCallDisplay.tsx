/**
 * Component to display individual tool invocations with parameters.
 */
import { Wrench } from 'lucide-react';
import { ToolCall } from '@/types/chat';

interface ToolCallDisplayProps {
  toolCall: ToolCall;
}

export default function ToolCallDisplay({ toolCall }: ToolCallDisplayProps) {
  // Format tool name for display (e.g., "web_search" -> "Web Search")
  const formatToolName = (name: string): string => {
    return name
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  // Format parameters for display
  const formatParameters = (params: Record<string, any>): string => {
    if (Object.keys(params).length === 0) {
      return 'No parameters';
    }

    // For single parameters, show inline
    if (Object.keys(params).length === 1) {
      const key = Object.keys(params)[0];
      const value = params[key];
      if (typeof value === 'string' && value.length < 100) {
        return `${key}: "${value}"`;
      }
    }

    // For complex parameters, show as JSON
    return JSON.stringify(params, null, 2);
  };

  return (
    <div className="tool-call bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3 mb-2">
      {/* Tool header */}
      <div className="flex items-center gap-2 mb-2">
        <Wrench className="w-4 h-4 text-blue-600 dark:text-blue-400" />
        <span className="font-semibold text-blue-900 dark:text-blue-100">
          {formatToolName(toolCall.tool)}
        </span>
      </div>

      {/* Thought (if present) */}
      {toolCall.thought && (
        <div className="text-sm text-gray-700 dark:text-gray-300 mb-2 italic">
          💭 {toolCall.thought}
        </div>
      )}

      {/* Parameters */}
      <div className="text-sm">
        <span className="text-gray-600 dark:text-gray-400 font-medium">Parameters: </span>
        {Object.keys(toolCall.parameters).length === 1 &&
        typeof Object.values(toolCall.parameters)[0] === 'string' &&
        (Object.values(toolCall.parameters)[0] as string).length < 100 ? (
          <span className="text-gray-800 dark:text-gray-200">
            {formatParameters(toolCall.parameters)}
          </span>
        ) : (
          <pre className="mt-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded p-2 overflow-x-auto text-xs font-mono">
            {formatParameters(toolCall.parameters)}
          </pre>
        )}
      </div>
    </div>
  );
}
