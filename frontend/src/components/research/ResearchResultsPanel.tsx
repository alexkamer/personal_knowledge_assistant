/**
 * Research results panel component - displays completed research.
 */
import { useState } from 'react';
import { CheckCircle, ExternalLink, Star, AlertTriangle, Lightbulb, FileText, ChevronDown, ChevronUp } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { ResearchResults } from '@/services/researchService';

interface ResearchResultsPanelProps {
  results: ResearchResults;
}

export function ResearchResultsPanel({ results }: ResearchResultsPanelProps) {
  const [expandedSources, setExpandedSources] = useState<Set<string>>(new Set());

  const getStars = (score: number | null) => {
    if (!score) return 0;
    return Math.round(score * 5);
  };

  const toggleSource = (sourceId: string) => {
    setExpandedSources((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(sourceId)) {
        newSet.delete(sourceId);
      } else {
        newSet.add(sourceId);
      }
      return newSet;
    });
  };


  return (
    <div className="bg-white dark:bg-gray-900 rounded-lg shadow-sm border border-gray-200 dark:border-gray-800 overflow-hidden">
      {/* Header */}
      <div className="bg-success-500 p-6">
        <div className="flex items-start gap-3">
          <CheckCircle className="w-6 h-6 text-white flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="text-xl font-semibold text-white">Research Complete!</h3>
            <p className="mt-1 text-green-50">{results.query}</p>
          </div>
        </div>
      </div>

      <div className="p-6 space-y-6">
        {/* Stats */}
        <div className="grid grid-cols-3 gap-4">
          <div className="text-center p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
            <div className="text-3xl font-bold text-green-600 dark:text-green-400">
              {results.sources_added}
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">Sources Added</div>
          </div>
          <div className="text-center p-4 bg-red-50 dark:bg-red-900/20 rounded-lg">
            <div className="text-3xl font-bold text-red-600 dark:text-red-400">
              {results.sources_failed}
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">Failed</div>
          </div>
          <div className="text-center p-4 bg-orange-50 dark:bg-orange-900/20 rounded-lg">
            <div className="text-3xl font-bold text-orange-600 dark:text-orange-400">
              {results.sources_skipped}
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">Skipped</div>
          </div>
        </div>

        {/* Summary */}
        {results.summary && (
          <div className="p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
            <h4 className="font-semibold text-blue-900 dark:text-blue-100 mb-2 flex items-center gap-2">
              <FileText className="w-4 h-4" />
              Summary
            </h4>
            <p className="text-gray-700 dark:text-gray-300 text-sm leading-relaxed">
              {results.summary}
            </p>
          </div>
        )}

        {/* Contradictions */}
        {results.contradictions_found > 0 && (
          <div className="p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
            <h4 className="font-semibold text-yellow-900 dark:text-yellow-100 mb-2 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4" />
              {results.contradictions_found} Contradiction{results.contradictions_found > 1 ? 's' : ''} Found
            </h4>
            <p className="text-gray-700 dark:text-gray-300 text-sm">
              Some sources contain conflicting information. Review the sources carefully.
            </p>
          </div>
        )}

        {/* Suggested Follow-ups */}
        {results.suggested_followups && results.suggested_followups.length > 0 && (
          <div className="p-4 bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800 rounded-lg">
            <h4 className="font-semibold text-purple-900 dark:text-purple-100 mb-3 flex items-center gap-2">
              <Lightbulb className="w-4 h-4" />
              Suggested Follow-ups
            </h4>
            <ul className="space-y-2">
              {results.suggested_followups.map((followup, index) => (
                <li key={index} className="text-gray-700 dark:text-gray-300 text-sm flex items-start gap-2">
                  <span className="text-purple-600 dark:text-purple-400">•</span>
                  {followup}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Sources */}
        <div>
          <h4 className="font-semibold text-gray-900 dark:text-white mb-4">
            Sources ({results.sources.length})
          </h4>
          <div className="space-y-3">
            {results.sources.map((source) => (
              <div
                key={source.id}
                className="p-4 border border-gray-200 dark:border-gray-800 rounded-lg hover:border-gray-300 dark:hover:border-gray-700 transition-colors"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      {/* Credibility Stars */}
                      {source.credibility_score !== null && (
                        <div className="flex items-center gap-0.5">
                          {Array.from({ length: 5 }).map((_, i) => (
                            <Star
                              key={i}
                              size={14}
                              className={
                                i < getStars(source.credibility_score!)
                                  ? 'fill-yellow-400 text-yellow-400'
                                  : 'text-gray-300 dark:text-gray-700'
                              }
                            />
                          ))}
                        </div>
                      )}
                      {/* Source Type Badge */}
                      {source.source_type && (
                        <span className="px-2 py-0.5 text-xs font-medium bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded">
                          {source.source_type}
                        </span>
                      )}
                      {/* Status Badge */}
                      <span
                        className={`px-2 py-0.5 text-xs font-medium rounded ${
                          source.status === 'scraped'
                            ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
                            : source.status === 'failed'
                            ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400'
                            : 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-400'
                        }`}
                      >
                        {source.status}
                      </span>
                    </div>

                    <h5 className="font-medium text-gray-900 dark:text-white">
                      {source.title || 'Untitled'}
                    </h5>
                    <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{source.domain}</p>

                    {/* Credibility Reasons */}
                    {source.credibility_reasons && source.credibility_reasons.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-1">
                        {source.credibility_reasons.map((reason, idx) => (
                          <span
                            key={idx}
                            className="text-xs px-2 py-0.5 bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 rounded"
                          >
                            {reason}
                          </span>
                        ))}
                      </div>
                    )}

                    {/* Failure Reason */}
                    {source.failure_reason && (
                      <p className="mt-2 text-sm text-red-600 dark:text-red-400">
                        {source.failure_reason}
                      </p>
                    )}
                  </div>

                  <a
                    href={source.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex-shrink-0 text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 transition-colors"
                    title="Open source"
                  >
                    <ExternalLink size={18} />
                  </a>
                </div>

                {/* Expandable Content */}
                {source.content && (
                  <div className="mt-3 border-t border-gray-200 dark:border-gray-800 pt-3">
                    <button
                      onClick={() => toggleSource(source.id)}
                      className="flex items-center gap-2 text-sm font-medium text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 transition-colors"
                    >
                      {expandedSources.has(source.id) ? (
                        <>
                          <ChevronUp size={16} />
                          Hide content
                        </>
                      ) : (
                        <>
                          <ChevronDown size={16} />
                          Read full content
                        </>
                      )}
                    </button>

                    {expandedSources.has(source.id) && (
                      <div className="mt-3 p-4 bg-gray-50 dark:bg-gray-800/50 rounded-lg border border-gray-200 dark:border-gray-700 max-h-96 overflow-y-auto">
                        <div className="prose prose-sm dark:prose-invert max-w-none">
                          <ReactMarkdown
                            remarkPlugins={[remarkGfm]}
                            components={{
                              code: ({ inline, className, children, ...props }: any) => {
                                return !inline ? (
                                  <pre className="bg-gray-900 dark:bg-black rounded p-3 overflow-x-auto">
                                    <code className={`text-green-400 text-xs font-mono ${className}`} {...props}>
                                      {children}
                                    </code>
                                  </pre>
                                ) : (
                                  <code className="bg-gray-200 dark:bg-gray-800 px-1 py-0.5 rounded text-xs font-mono" {...props}>
                                    {children}
                                  </code>
                                );
                              },
                            }}
                          >
                            {source.content}
                          </ReactMarkdown>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Next Steps */}
        <div className="pt-4 border-t border-gray-200 dark:border-gray-800">
          <p className="text-sm text-gray-600 dark:text-gray-400">
            💡 <strong>What's next?</strong> These sources have been added to your knowledge base. Head to the Chat page to ask questions about them!
          </p>
        </div>
      </div>
    </div>
  );
}
