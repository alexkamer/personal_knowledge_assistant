/**
 * Floating Message Card - Knowledge Garden Design System
 *
 * Beautiful floating message cards with gradient backgrounds for user messages
 * and glass-morphism effects for assistant messages.
 */

import React from 'react';
import { Copy, RotateCw, Check, ThumbsUp, ThumbsDown, ChevronDown, ChevronUp, FileText, StickyNote, Globe, User, Bot } from 'lucide-react';
import type { Message, SourceCitation } from '@/types/chat';
import { MarkdownRenderer } from './MarkdownRenderer';
import { ToolCallCard } from './ToolCallCard';
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
  isLatestAssistantMessage?: boolean;
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
  isLatestAssistantMessage = false,
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
        'w-full py-6 fade-in',
        isUser ? 'bg-transparent' : 'bg-gray-800/30'
      )}
    >
      <div className="max-w-3xl mx-auto px-4 sm:px-6">
        <div className="flex gap-4">
          {/* Avatar */}
          <div className="flex-shrink-0">
            <div className={cn(
              "w-8 h-8 rounded-full flex items-center justify-center",
              isUser ? "bg-blue-600" : "bg-emerald-600"
            )}>
              {isUser ? <User size={18} className="text-white" /> : <Bot size={18} className="text-white" />}
            </div>
          </div>

          {/* Message Content */}
          <div className="flex-1 min-w-0">
            {isUser ? (
              <div className="whitespace-pre-wrap break-words text-lg leading-relaxed text-white font-medium">
                {message.content}
              </div>
            ) : (
              <>
                {/* Show status as placeholder if no content yet */}
                {!message.content && message.metadata?.status && (
                  <div className="flex items-center gap-3 text-gray-400 py-2">
                    <div className="flex gap-1">
                      <div className="w-2 h-2 bg-primary-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                      <div className="w-2 h-2 bg-primary-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                      <div className="w-2 h-2 bg-primary-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                    </div>
                    <span className="text-sm">{message.metadata.status}</span>
                  </div>
                )}

                {/* Show content when available */}
                {message.content && (
                  <div className="prose dark:prose-invert prose-sm max-w-none">
                    <MarkdownRenderer
                      content={message.content}
                      sources={message.sources}
                      onSourceClick={onSourceClick}
                    />
                  </div>
                )}
              </>
            )}

            {/* Assistant Message Footer */}
            {!isUser && (
              <div className="space-y-3 mt-3">
                {/* Action Buttons */}
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => onCopyMessage(message.content, message.id)}
                    className="flex items-center gap-1.5 px-2.5 py-1.5 text-xs text-gray-300 hover:text-white hover:bg-gray-800 rounded-md transition-colors"
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
                      className="flex items-center gap-1.5 px-2.5 py-1.5 text-xs text-gray-300 hover:text-white hover:bg-gray-800 rounded-md transition-colors"
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
                        className="flex items-center gap-1.5 px-2.5 py-1.5 text-xs text-gray-300 hover:text-success-400 hover:bg-success-900/20 rounded-md transition-colors disabled:opacity-50"
                        title="Helpful response"
                      >
                        <ThumbsUp size={14} />
                      </button>
                      <button
                        onClick={() => onFeedback(message.id, false)}
                        disabled={feedbackLoading === message.id}
                        className="flex items-center gap-1.5 px-2.5 py-1.5 text-xs text-gray-300 hover:text-danger-400 hover:bg-danger-900/20 rounded-md transition-colors disabled:opacity-50"
                        title="Not helpful"
                      >
                        <ThumbsDown size={14} />
                      </button>
                    </>
                  )}
                </div>

                {/* Tool Calls - Agent Reasoning */}
                {message.tool_calls && message.tool_calls.length > 0 && (
                  <div className="border-t border-gray-600 pt-3">
                    <h4 className="text-xs font-semibold text-gray-300 mb-2">
                      🤖 Agent Reasoning
                    </h4>
                    <div className="space-y-2">
                      {message.tool_calls.map((toolCall, index) => (
                        <ToolCallCard
                          key={`${message.id}-tool-${index}`}
                          toolName={toolCall.tool}
                          parameters={toolCall.parameters}
                          result={toolCall.result}
                          error={toolCall.error}
                          status={toolCall.status}
                        />
                      ))}
                    </div>
                  </div>
                )}

                {/* Sources */}
                {message.sources && message.sources.length > 0 && (
                  <div className="border-t border-gray-600 pt-3">
                    <button
                      onClick={() => onToggleSources(message.id)}
                      className="flex items-center gap-2 text-xs font-medium text-gray-300 hover:text-white transition-colors"
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
                            className="flex items-center gap-1.5 px-2.5 py-1.5 text-xs bg-primary-900/20 text-primary-400 rounded-md hover:bg-primary-900/30 transition-colors"
                          >
                            {getSourceIcon(source.source_type)}
                            <span className="max-w-xs truncate">{source.source_title}</span>
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* Suggested Questions - Only show on latest assistant message */}
                {isLatestAssistantMessage && message.suggested_questions && message.suggested_questions.length > 0 && (
                  <div className="border-t border-gray-600 pt-3">
                    <p className="text-xs font-medium text-gray-300 mb-2">
                      Suggested follow-up questions:
                    </p>
                    <div className="space-y-2">
                      {message.suggested_questions.map((question, index) => (
                        <button
                          key={index}
                          onClick={() => onQuestionClick?.(question)}
                          className="w-full text-left px-3 py-2 text-sm text-primary-400 bg-primary-900/20 hover:bg-primary-900/30 rounded-lg transition-colors"
                        >
                          {question}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Timestamp */}
            <div className="mt-2">
              <span className="text-xs text-gray-400">
                {new Date(message.created_at).toLocaleTimeString('en-US', {
                  hour: 'numeric',
                  minute: '2-digit',
                })}
                {!isUser && message.model_used && (
                  <>
                    <span className="mx-1">•</span>
                    <span className="text-gray-500">{message.model_used}</span>
                  </>
                )}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
});

FloatingMessageCard.displayName = 'FloatingMessageCard';
