/**
 * Message list component displaying chat messages with source citations.
 */
import React from 'react';
import { Bot, User, FileText, StickyNote, Globe, Copy, RotateCw, Check, ThumbsUp, ThumbsDown, ChevronDown, ChevronUp } from 'lucide-react';
import type { Message, SourceCitation } from '@/types/chat';
import { SourcePreviewModal } from './SourcePreviewModal';
import { MetadataBadges } from './MetadataBadges';
import { MarkdownRenderer } from './MarkdownRenderer';
import { apiClient } from '@/services/api';

interface MessageListProps {
  messages: Message[];
  isLoading?: boolean;
  onRegenerateMessage?: (messageId: string) => void;
  onFeedbackSubmitted?: () => void;
  onQuestionClick?: (question: string) => void;
}

export function MessageList({ messages, isLoading, onRegenerateMessage, onFeedbackSubmitted, onQuestionClick }: MessageListProps) {
  const messagesEndRef = React.useRef<HTMLDivElement>(null);
  const [copiedMessageId, setCopiedMessageId] = React.useState<string | null>(null);
  const [selectedSource, setSelectedSource] = React.useState<SourceCitation | null>(null);
  const [feedbackLoading, setFeedbackLoading] = React.useState<string | null>(null);
  const [expandedSources, setExpandedSources] = React.useState<Set<string>>(new Set());

  React.useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleCopyMessage = async (content: string, messageId: string) => {
    try {
      await navigator.clipboard.writeText(content);
      setCopiedMessageId(messageId);
      setTimeout(() => setCopiedMessageId(null), 2000);
    } catch (err) {
      console.error('Failed to copy message:', err);
    }
  };

  const handleSourceClick = (source: SourceCitation) => {
    setSelectedSource(source);
  };

  const handleFeedback = async (messageId: string, isPositive: boolean) => {
    setFeedbackLoading(messageId);
    try {
      await apiClient.post(`/chat/messages/${messageId}/feedback`, {
        is_positive: isPositive,
      });
      onFeedbackSubmitted?.();
    } catch (err) {
      console.error('Failed to submit feedback:', err);
    } finally {
      setFeedbackLoading(null);
    }
  };

  const toggleSources = (messageId: string) => {
    setExpandedSources(prev => {
      const next = new Set(prev);
      if (next.has(messageId)) {
        next.delete(messageId);
      } else {
        next.add(messageId);
      }
      return next;
    });
  };

  if (messages.length === 0 && !isLoading) {
    return (
      <div className="flex items-center justify-center h-full text-gray-500 dark:text-gray-400">
        <div className="text-center">
          <Bot className="mx-auto mb-4 text-gray-300 dark:text-gray-600" size={64} />
          <p className="text-lg font-medium">Start a conversation</p>
          <p className="text-sm mt-2">
            Ask questions about your notes and documents
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto">
      {messages.map((message) => (
        <div
          key={message.id}
          className={`py-8 px-6 ${
            message.role === 'user'
              ? 'bg-gray-50 dark:bg-gray-900'
              : 'bg-white dark:bg-gray-800'
          }`}
        >
          <div className="max-w-3xl mx-auto flex gap-6">
            {/* Avatar */}
            <div
              className={`flex-shrink-0 w-8 h-8 rounded-sm flex items-center justify-center ${
                message.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-green-600 dark:bg-green-700 text-white'
              }`}
            >
              {message.role === 'user' ? <User size={16} /> : <Bot size={16} />}
            </div>

            {/* Message Content */}
            <div className="flex-1 min-w-0">
              <div className="text-gray-900 dark:text-gray-100">
              {message.role === 'user' ? (
                <div className="whitespace-pre-wrap break-words">
                  {message.content}
                </div>
              ) : (
                <MarkdownRenderer content={message.content} />
              )}

              {/* Action buttons for assistant messages */}
              {message.role === 'assistant' && (
                <div className="mt-4 flex items-center gap-2">
                <button
                  onClick={() => handleCopyMessage(message.content, message.id)}
                  className="flex items-center gap-1.5 px-2.5 py-1.5 text-xs text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md transition-colors"
                  title="Copy message"
                >
                  {copiedMessageId === message.id ? (
                    <>
                      <Check size={14} className="text-green-600 dark:text-green-400" />
                      <span className="text-green-600 dark:text-green-400">Copied!</span>
                    </>
                  ) : (
                    <>
                      <Copy size={14} />
                      <span>Copy</span>
                    </>
                  )}
                </button>
                {onRegenerateMessage && message.id !== 'streaming' && (
                  <button
                    onClick={() => onRegenerateMessage(message.id)}
                    className="flex items-center gap-1.5 px-2.5 py-1.5 text-xs text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md transition-colors"
                    title="Regenerate response"
                  >
                    <RotateCw size={14} />
                    <span>Regenerate</span>
                  </button>
                )}

                {/* Feedback buttons */}
                {message.id !== 'streaming' && (
                  <div className="flex items-center gap-1 ml-2 pl-2 border-l border-gray-300 dark:border-gray-600">
                    <button
                      onClick={() => handleFeedback(message.id, true)}
                      disabled={feedbackLoading === message.id}
                      className={`p-1.5 rounded-md transition-colors ${
                        message.feedback?.is_positive
                          ? 'text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/20'
                          : 'text-gray-600 dark:text-gray-400 hover:text-green-600 dark:hover:text-green-400 hover:bg-green-50 dark:hover:bg-green-900/20'
                      } ${feedbackLoading === message.id ? 'opacity-50 cursor-not-allowed' : ''}`}
                      title="Helpful response"
                    >
                      <ThumbsUp size={14} />
                    </button>
                    <button
                      onClick={() => handleFeedback(message.id, false)}
                      disabled={feedbackLoading === message.id}
                      className={`p-1.5 rounded-md transition-colors ${
                        message.feedback && !message.feedback.is_positive
                          ? 'text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20'
                          : 'text-gray-600 dark:text-gray-400 hover:text-red-600 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20'
                      } ${feedbackLoading === message.id ? 'opacity-50 cursor-not-allowed' : ''}`}
                      title="Not helpful"
                    >
                      <ThumbsDown size={14} />
                    </button>
                  </div>
                )}
                </div>
              )}

              {/* Sources (only for assistant messages) */}
              {message.role === 'assistant' && message.sources && message.sources.length > 0 && (
                <div className="mt-4 text-sm">
                <button
                  onClick={() => toggleSources(message.id)}
                  className="text-gray-700 dark:text-gray-300 font-semibold mb-2.5 flex items-center gap-1.5 hover:text-gray-900 dark:hover:text-white transition-colors"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
                  </svg>
                  Sources ({message.sources.length})
                  {expandedSources.has(message.id) ? (
                    <ChevronUp size={16} />
                  ) : (
                    <ChevronDown size={16} />
                  )}
                </button>
                {expandedSources.has(message.id) && (
                  <div className="flex flex-col gap-2.5">
                  {message.sources.map((source) => (
                    <button
                      key={`${source.source_id}-${source.chunk_index}`}
                      onClick={() => handleSourceClick(source)}
                      className="group text-left p-3 bg-white dark:bg-gray-700 rounded-lg border border-gray-200 dark:border-gray-600 hover:border-blue-300 dark:hover:border-blue-500 hover:shadow-sm transition-all cursor-pointer"
                      title={`Distance: ${source.distance.toFixed(3)} | Chunk: ${source.chunk_index} | Click to preview`}
                    >
                      <div className="flex items-start gap-2.5">
                        <div className={`p-1.5 rounded flex-shrink-0 ${
                          source.source_type === 'note' ? 'bg-yellow-50 dark:bg-yellow-900/20 text-yellow-600 dark:text-yellow-400' :
                          source.source_type === 'web' ? 'bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400' :
                          'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400'
                        }`}>
                          {source.source_type === 'note' ? (
                            <StickyNote size={14} />
                          ) : source.source_type === 'web' ? (
                            <Globe size={14} />
                          ) : (
                            <FileText size={14} />
                          )}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-start justify-between gap-2">
                            <div className="flex-1 min-w-0">
                              <div className="text-xs font-semibold text-gray-900 dark:text-white">
                                {source.source_title}
                              </div>
                              {source.section_title && (
                                <div className="text-[11px] text-gray-600 dark:text-gray-400 mt-0.5 truncate" title={source.section_title}>
                                  📍 {source.section_title}
                                </div>
                              )}
                              <div className="text-[10px] text-gray-500 dark:text-gray-400 mt-0.5">
                                {source.source_type === 'note' ? 'Note' : source.source_type === 'web' ? 'Web' : 'Document'} • Ref [{source.index}]
                              </div>
                            </div>
                          </div>
                          <div className="mt-2">
                            <MetadataBadges
                              contentType={source.content_type}
                              hasCode={source.has_code}
                              semanticDensity={source.semantic_density}
                            />
                          </div>
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
                )}
              </div>
            )}

              {/* Suggested Questions (only for assistant messages) */}
              {message.role === 'assistant' && message.suggested_questions && message.suggested_questions.length > 0 && (
                <div className="mt-4">
                  <p className="text-xs font-semibold text-gray-600 dark:text-gray-400 mb-2">
                    Suggested follow-up questions:
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {message.suggested_questions.map((question, index) => (
                      <button
                        key={index}
                        onClick={() => onQuestionClick?.(question)}
                        className="text-left px-3 py-2 text-sm bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 rounded-lg border border-blue-200 dark:border-blue-700 hover:bg-blue-100 dark:hover:bg-blue-900/30 hover:border-blue-300 dark:hover:border-blue-600 transition-colors"
                      >
                        {question}
                      </button>
                    ))}
                  </div>
                </div>
              )}
              </div>

              {/* Timestamp and model info */}
              <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                {new Date(message.created_at).toLocaleTimeString('en-US', {
                  hour: 'numeric',
                  minute: '2-digit',
                })}
                {message.model_used && (
                  <span className="ml-2">• {message.model_used}</span>
                )}
              </div>
            </div>
          </div>
        </div>
      ))}

      {isLoading && (
        <div className="py-8 px-6 bg-white dark:bg-gray-800">
          <div className="max-w-3xl mx-auto flex gap-6">
            <div className="flex-shrink-0 w-8 h-8 rounded-sm bg-green-600 dark:bg-green-700 text-white flex items-center justify-center">
              <Bot size={16} />
            </div>
            <div className="flex-1">
              <div className="flex gap-2">
                <div className="w-2 h-2 bg-gray-400 dark:bg-gray-500 rounded-full animate-bounce" />
                <div
                  className="w-2 h-2 bg-gray-400 dark:bg-gray-500 rounded-full animate-bounce"
                  style={{ animationDelay: '0.2s' }}
                />
                <div
                  className="w-2 h-2 bg-gray-400 dark:bg-gray-500 rounded-full animate-bounce"
                  style={{ animationDelay: '0.4s' }}
                />
              </div>
            </div>
          </div>
        </div>
      )}

      <div ref={messagesEndRef} />

      {/* Source Preview Modal */}
      <SourcePreviewModal
        source={selectedSource}
        onClose={() => setSelectedSource(null)}
      />
    </div>
  );
}
