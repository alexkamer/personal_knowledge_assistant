/**
 * Component to display tool execution results.
 */
import { CheckCircle, XCircle } from 'lucide-react';
import { ToolResult } from '@/types/chat';

interface ToolResultDisplayProps {
  toolResult: ToolResult;
}

export default function ToolResultDisplay({ toolResult }: ToolResultDisplayProps) {
  const { tool, success, result, error, metadata } = toolResult;

  // Format tool name for display
  const formatToolName = (name: string): string => {
    return name
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  // Format result based on tool type
  const formatResult = (toolName: string, resultData: any): React.ReactNode => {
    // Calculator result
    if (toolName === 'calculator' && resultData?.expression && resultData?.result !== undefined) {
      return (
        <div className="font-mono text-sm">
          {resultData.expression} = <span className="font-bold">{resultData.result}</span>
        </div>
      );
    }

    // Code executor result
    if (toolName === 'code_executor') {
      return (
        <div className="space-y-2">
          {resultData?.stdout && (
            <div>
              <div className="text-xs text-gray-600 dark:text-gray-400 mb-1">Output:</div>
              <pre className="bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded p-2 text-xs overflow-x-auto">
                {resultData.stdout}
              </pre>
            </div>
          )}
          {resultData?.stderr && (
            <div>
              <div className="text-xs text-gray-600 dark:text-gray-400 mb-1">Errors:</div>
              <pre className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded p-2 text-xs overflow-x-auto text-red-800 dark:text-red-200">
                {resultData.stderr}
              </pre>
            </div>
          )}
          {resultData?.return_code !== undefined && (
            <div className="text-xs text-gray-600 dark:text-gray-400">
              Exit code: {resultData.return_code}
            </div>
          )}
        </div>
      );
    }

    // Web search result
    if (toolName === 'web_search' && resultData?.results) {
      return (
        <div className="space-y-1">
          <div className="text-sm text-gray-700 dark:text-gray-300">
            Found {resultData.results.length} results
          </div>
          {resultData.results.slice(0, 2).map((r: any, idx: number) => (
            <div key={idx} className="text-xs text-gray-600 dark:text-gray-400">
              • {r.title || r.url}
            </div>
          ))}
        </div>
      );
    }

    // Document search result
    if (toolName === 'document_search' && resultData?.results_count !== undefined) {
      return (
        <div className="text-sm text-gray-700 dark:text-gray-300">
          Found {resultData.results_count} relevant passages in your documents
        </div>
      );
    }

    // Generic result display
    if (typeof resultData === 'string') {
      return <div className="text-sm text-gray-800 dark:text-gray-200">{resultData}</div>;
    }

    // JSON fallback
    return (
      <pre className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded p-2 text-xs overflow-x-auto">
        {JSON.stringify(resultData, null, 2)}
      </pre>
    );
  };

  return (
    <div
      className={`tool-result rounded-lg p-3 mb-2 ${
        success
          ? 'bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800'
          : 'bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800'
      }`}
    >
      {/* Result header */}
      <div className="flex items-center gap-2 mb-2">
        {success ? (
          <CheckCircle className="w-4 h-4 text-green-600 dark:text-green-400" />
        ) : (
          <XCircle className="w-4 h-4 text-red-600 dark:text-red-400" />
        )}
        <span
          className={`font-semibold ${
            success
              ? 'text-green-900 dark:text-green-100'
              : 'text-red-900 dark:text-red-100'
          }`}
        >
          {formatToolName(tool)} {success ? 'Result' : 'Failed'}
        </span>
      </div>

      {/* Result content */}
      {success ? (
        <div className="text-gray-800 dark:text-gray-200">{formatResult(tool, result)}</div>
      ) : (
        <div className="text-red-800 dark:text-red-200 text-sm">
          Error: {error || 'Unknown error'}
        </div>
      )}

      {/* Metadata (if present) */}
      {metadata && Object.keys(metadata).length > 0 && (
        <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
          {Object.entries(metadata)
            .filter(([key]) => key !== 'tool')
            .map(([key, value]) => (
              <span key={key} className="mr-3">
                {key}: {String(value)}
              </span>
            ))}
        </div>
      )}
    </div>
  );
}
