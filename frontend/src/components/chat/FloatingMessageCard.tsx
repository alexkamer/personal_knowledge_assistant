/**
 * Floating Message Card - Knowledge Garden Design System
 *
 * Beautiful floating message cards with gradient backgrounds for user messages
 * and glass-morphism effects for assistant messages.
 */

import React from 'react';
import { Copy, RotateCw, Check, ThumbsUp, ThumbsDown, ChevronDown, ChevronUp, FileText, StickyNote, Globe } from 'lucide-react';
import type { Message, SourceCitation } from '@/types/chat';
import { MarkdownRenderer } from './MarkdownRenderer';
import { cn } from '@/lib/utils';

interface FloatingMessageCardProps {
  message: Message;
  copiedMessageId: string | null;
  feedbackLoading: string | null;
  expandedSources: Set<string>;
  onCopyMessage: (content: string, messageId: string) => void;
  onSourceClick: (source: SourceCitation) => void;
  onFeedback: (messageId: string, isPositive: boolean) => void;
  onToggleSources: (messageId: string) => void;
  onRegenerateMessage?: (messageId: string) => void;
  onQuestionClick?: (question: string) => void;
}

export const FloatingMessageCard = React.memo<FloatingMessageCardProps>(({
  message,
  copiedMessageId,
  feedbackLoading,
  expandedSources,
  onCopyMessage,
  onSourceClick,
  onFeedback,
  onToggleSources,
  onRegenerateMessage,
  onQuestionClick,
}) => {
  const isUser = message.role === 'user';
  const isSourcesExpanded = expandedSources.has(message.id);

  const getSourceIcon = (sourceType: string) => {
    switch (sourceType) {
      case 'note':
        return <StickyNote size={14} />;
      case 'document':
        return <FileText size={14} />;
      case 'web':
        return <Globe size={14} />;
      default:
        return <FileText size={14} />;
    }
  };

  return (
    <div
      className={cn(
        'flex mb-6 px-4 sm:px-6',
        isUser ? 'justify-end animate-slide-in-right' : 'justify-start animate-slide-in-left'
      )}
    >
      <div
        className={cn(
          'max-w-2xl rounded-2xl shadow-lg transition-all duration-200',
          isUser
            ? 'bg-gradient-to-br from-indigo-500 to-indigo-600 text-white rounded-br-md ml-12'
            : 'bg-white/90 dark:bg-stone-900/80 backdrop-blur-xl border border-stone-200/50 dark:border-stone-800/50 text-stone-900 dark:text-stone-100 rounded-bl-md mr-12 hover:shadow-xl'
        )}
      >
        {/* Message Content */}
        <div className="px-6 py-4">
          {isUser ? (
            <div className="whitespace-pre-wrap break-words text-base leading-relaxed">
              {message.content}
            </div>
          ) : (
            <div className="prose dark:prose-invert prose-sm max-w-none">
              <MarkdownRenderer content={message.content} />
            </div>
          )}
        </div>

        {/* Assistant Message Footer */}
        {!isUser && (
          <div className="px-6 pb-4 space-y-3">
            {/* Action Buttons */}
            <div className="flex items-center gap-2 pt-2">
              <button
                onClick={() => onCopyMessage(message.content, message.id)}
                className="flex items-center gap-1.5 px-2.5 py-1.5 text-xs text-stone-600 dark:text-stone-400 hover:text-stone-900 dark:hover:text-white hover:bg-stone-100 dark:hover:bg-stone-700 rounded-md transition-colors"
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
                  className="flex items-center gap-1.5 px-2.5 py-1.5 text-xs text-stone-600 dark:text-stone-400 hover:text-stone-900 dark:hover:text-white hover:bg-stone-100 dark:hover:bg-stone-700 rounded-md transition-colors"
                  title="Regenerate response"
                >
                  <RotateCw size={14} />
                  <span>Regenerate</span>
                </button>
              )}

              {/* Feedback buttons */}
              {message.id !== 'streaming' && (
                <>
                  <button
                    onClick={() => onFeedback(message.id, true)}
                    disabled={feedbackLoading === message.id}
                    className="flex items-center gap-1.5 px-2.5 py-1.5 text-xs text-stone-600 dark:text-stone-400 hover:text-green-600 dark:hover:text-green-400 hover:bg-green-50 dark:hover:bg-green-900/20 rounded-md transition-colors disabled:opacity-50"
                    title="Helpful response"
                  >
                    <ThumbsUp size={14} />
                  </button>
                  <button
                    onClick={() => onFeedback(message.id, false)}
                    disabled={feedbackLoading === message.id}
                    className="flex items-center gap-1.5 px-2.5 py-1.5 text-xs text-stone-600 dark:text-stone-400 hover:text-red-600 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-md transition-colors disabled:opacity-50"
                    title="Not helpful"
                  >
                    <ThumbsDown size={14} />
                  </button>
                </>
              )}
            </div>

            {/* Sources */}
            {message.sources && message.sources.length > 0 && (
              <div className="border-t border-stone-200 dark:border-stone-700 pt-3">
                <button
                  onClick={() => onToggleSources(message.id)}
                  className="flex items-center gap-2 text-xs font-medium text-stone-600 dark:text-stone-400 hover:text-stone-900 dark:hover:text-white transition-colors"
                >
                  <span>Sources ({message.sources.length})</span>
                  {isSourcesExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                </button>

                {isSourcesExpanded && (
                  <div className="mt-3 flex flex-wrap gap-2">
                    {message.sources.map((source, index) => (
                      <button
                        key={index}
                        onClick={() => onSourceClick(source)}
                        className="flex items-center gap-1.5 px-2.5 py-1.5 text-xs bg-indigo-50 dark:bg-indigo-900/20 text-indigo-700 dark:text-indigo-400 rounded-md hover:bg-indigo-100 dark:hover:bg-indigo-900/30 transition-colors"
                      >
                        {getSourceIcon(source.source_type)}
                        <span className="max-w-xs truncate">{source.source_title}</span>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Suggested Questions */}
            {message.suggested_questions && message.suggested_questions.length > 0 && (
              <div className="border-t border-stone-200 dark:border-stone-700 pt-3">
                <p className="text-xs font-medium text-stone-600 dark:text-stone-400 mb-2">
                  Suggested follow-up questions:
                </p>
                <div className="space-y-2">
                  {message.suggested_questions.map((question, index) => (
                    <button
                      key={index}
                      onClick={() => onQuestionClick?.(question)}
                      className="w-full text-left px-3 py-2 text-sm text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/20 hover:bg-blue-100 dark:hover:bg-blue-900/30 rounded-lg transition-colors"
                    >
                      {question}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* User Message Timestamp */}
        {isUser && (
          <div className="px-6 pb-3">
            <span className="text-xs text-indigo-200">
              {new Date(message.created_at).toLocaleTimeString('en-US', {
                hour: 'numeric',
                minute: '2-digit',
              })}
            </span>
          </div>
        )}

        {/* Assistant Message Timestamp */}
        {!isUser && (
          <div className="px-6 pb-3 flex items-center gap-2 text-xs text-stone-400 dark:text-stone-600">
            <span>
              {new Date(message.created_at).toLocaleTimeString('en-US', {
                hour: 'numeric',
                minute: '2-digit',
              })}
            </span>
            {message.model_used && (
              <>
                <span>•</span>
                <span>{message.model_used}</span>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
});

FloatingMessageCard.displayName = 'FloatingMessageCard';
