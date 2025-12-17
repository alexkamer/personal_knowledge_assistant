/**
 * Modal component for previewing source content
 */
import { useEffect, useState } from 'react';
import { X, FileText, StickyNote, Globe, ExternalLink, Loader2 } from 'lucide-react';
import type { SourceCitation, ChunkDetail } from '@/types/chat';
import { apiClient } from '@/services/api';

interface SourcePreviewModalProps {
  source: SourceCitation | null;
  onClose: () => void;
}

export function SourcePreviewModal({ source, onClose }: SourcePreviewModalProps) {
  const [chunkDetail, setChunkDetail] = useState<ChunkDetail | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (source && source.source_type !== 'web') {
      fetchChunkContent();
    }
  }, [source]);

  const fetchChunkContent = async () => {
    if (!source) return;

    // Check if chunk_id is available
    if (!source.chunk_id) {
      setError('This source was created before chunk previews were available. Try regenerating the response to get detailed source previews.');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await apiClient.get(`/chat/chunks/${source.chunk_id}`);
      setChunkDetail(response.data);
    } catch (err: any) {
      console.error('Failed to fetch chunk content:', err);
      setError(err.response?.data?.detail || 'Failed to load source content');
    } finally {
      setIsLoading(false);
    }
  };

  if (!source) return null;

  const getSourceIcon = () => {
    if (source.source_type === 'note') return <StickyNote size={20} />;
    if (source.source_type === 'web') return <Globe size={20} />;
    return <FileText size={20} />;
  };

  const getSourceColor = () => {
    if (source.source_type === 'note') return 'text-yellow-600 dark:text-yellow-400 bg-yellow-50 dark:bg-yellow-900/20';
    if (source.source_type === 'web') return 'text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/20';
    return 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/20';
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50">
      <div className="bg-white dark:bg-stone-900 rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-start justify-between p-6 border-b border-stone-200 dark:border-stone-800">
          <div className="flex items-start gap-3 flex-1">
            <div className={`p-2 rounded-lg ${getSourceColor()}`}>
              {getSourceIcon()}
            </div>
            <div className="flex-1 min-w-0">
              <h2 className="text-xl font-semibold text-stone-900 dark:text-white mb-1">
                {source.source_title}
              </h2>
              <div className="flex items-center gap-3 text-sm text-stone-600 dark:text-stone-400">
                <span className="capitalize">{source.source_type}</span>
                <span>•</span>
                <span>Reference [{source.index}]</span>
                <span>•</span>
                <span>Chunk {source.chunk_index}</span>
                {source.distance !== undefined && (
                  <>
                    <span>•</span>
                    <span>Relevance: {(1 - source.distance).toFixed(2)}</span>
                  </>
                )}
              </div>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-stone-400 hover:text-stone-600 dark:hover:text-stone-300 hover:bg-stone-100 dark:hover:bg-stone-800 rounded-lg transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {isLoading ? (
            <div className="flex items-center justify-center h-64">
              <Loader2 className="animate-spin text-blue-600 dark:text-blue-400" size={32} />
            </div>
          ) : error ? (
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 text-red-700 dark:text-red-300">
              {error}
            </div>
          ) : source.source_type === 'web' ? (
            <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4 text-blue-700 dark:text-blue-300">
              <p>Web sources don't have stored content. Click "Open original source" below to view the webpage.</p>
            </div>
          ) : chunkDetail ? (
            <div className="prose prose-sm max-w-none">
              <h3 className="text-sm font-semibold text-stone-700 dark:text-stone-300 uppercase tracking-wide mb-3">
                Content
              </h3>
              <div className="bg-stone-50 dark:bg-stone-800 rounded-lg p-4 border border-stone-200 dark:border-stone-700">
                <p className="text-stone-800 dark:text-stone-200 whitespace-pre-wrap leading-relaxed">
                  {chunkDetail.content}
                </p>
              </div>

              <div className="mt-4 flex items-center gap-4 text-xs text-stone-600 dark:text-stone-400">
                <span>Tokens: {chunkDetail.token_count}</span>
                <span>•</span>
                <span>Chunk: {chunkDetail.chunk_index}</span>
              </div>

              {chunkDetail.metadata && Object.keys(chunkDetail.metadata).length > 0 && (
                <div className="mt-6">
                  <h3 className="text-sm font-semibold text-stone-700 dark:text-stone-300 uppercase tracking-wide mb-3">
                    Metadata
                  </h3>
                  <div className="bg-stone-50 dark:bg-stone-800 rounded-lg p-4 border border-stone-200 dark:border-stone-700">
                    <dl className="grid grid-cols-2 gap-3">
                      {Object.entries(chunkDetail.metadata).map(([key, value]) => (
                        <div key={key}>
                          <dt className="text-xs font-medium text-stone-500 dark:text-stone-400 uppercase">{key}</dt>
                          <dd className="text-sm text-stone-900 dark:text-white mt-1">{String(value)}</dd>
                        </div>
                      ))}
                    </dl>
                  </div>
                </div>
              )}
            </div>
          ) : null}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t border-stone-200 dark:border-stone-800 bg-stone-50 dark:bg-stone-800">
          <div className="text-sm text-stone-600 dark:text-stone-400">
            {source.source_type === 'web' && chunkDetail?.metadata?.url && (
              <a
                href={chunkDetail.metadata.url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300"
              >
                <ExternalLink size={16} />
                <span>Open original source</span>
              </a>
            )}
          </div>
          <button
            onClick={onClose}
            className="px-4 py-2 bg-stone-200 dark:bg-stone-700 text-stone-700 dark:text-stone-200 rounded-lg hover:bg-stone-300 dark:hover:bg-stone-600 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
