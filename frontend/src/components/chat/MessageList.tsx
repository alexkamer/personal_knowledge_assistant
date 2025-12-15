/**
 * Message list component displaying chat messages with source citations.
 */
import React from 'react';
import { Bot, User, FileText, StickyNote } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import type { Message } from '@/types/chat';
import 'highlight.js/styles/github.css';

interface MessageListProps {
  messages: Message[];
  isLoading?: boolean;
}

export function MessageList({ messages, isLoading }: MessageListProps) {
  const messagesEndRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  if (messages.length === 0 && !isLoading) {
    return (
      <div className="flex items-center justify-center h-full text-gray-500">
        <div className="text-center">
          <Bot className="mx-auto mb-4 text-gray-300" size={64} />
          <p className="text-lg font-medium">Start a conversation</p>
          <p className="text-sm mt-2">
            Ask questions about your notes and documents
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto p-6 space-y-6">
      {messages.map((message) => (
        <div
          key={message.id}
          className={`flex gap-4 ${
            message.role === 'user' ? 'flex-row-reverse' : 'flex-row'
          }`}
        >
          {/* Avatar */}
          <div
            className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center ${
              message.role === 'user'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-200 text-gray-700'
            }`}
          >
            {message.role === 'user' ? <User size={20} /> : <Bot size={20} />}
          </div>

          {/* Message Content */}
          <div
            className={`flex-1 max-w-3xl ${
              message.role === 'user' ? 'text-right' : 'text-left'
            }`}
          >
            <div
              className={`inline-block p-4 rounded-lg ${
                message.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-white border border-gray-200 text-gray-900'
              }`}
            >
              {message.role === 'user' ? (
                <div className="whitespace-pre-wrap break-words">
                  {message.content}
                </div>
              ) : (
                <div className="prose prose-sm max-w-none">
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    rehypePlugins={[rehypeHighlight]}
                    components={{
                      code: ({ node, inline, className, children, ...props }: any) => {
                        return inline ? (
                          <code className="bg-gray-100 px-1.5 py-0.5 rounded text-sm font-mono" {...props}>
                            {children}
                          </code>
                        ) : (
                          <code className={className} {...props}>
                            {children}
                          </code>
                        );
                      },
                    }}
                  >
                    {message.content}
                  </ReactMarkdown>
                </div>
              )}
            </div>

            {/* Sources (only for assistant messages) */}
            {message.role === 'assistant' && message.sources && message.sources.length > 0 && (
              <div className="mt-3 text-sm">
                <p className="text-gray-600 font-medium mb-2">Sources:</p>
                <div className="flex flex-wrap gap-2">
                  {message.sources.map((source) => (
                    <div
                      key={`${source.source_id}-${source.chunk_index}`}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-gray-100 rounded-md text-gray-700 border border-gray-200"
                    >
                      {source.source_type === 'note' ? (
                        <StickyNote size={14} />
                      ) : (
                        <FileText size={14} />
                      )}
                      <span className="text-xs font-medium">
                        [{source.index}] {source.source_title}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Timestamp and model info */}
            <div className="mt-2 text-xs text-gray-500">
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
      ))}

      {isLoading && (
        <div className="flex gap-4">
          <div className="flex-shrink-0 w-10 h-10 rounded-full bg-gray-200 flex items-center justify-center">
            <Bot size={20} className="text-gray-700" />
          </div>
          <div className="flex-1">
            <div className="inline-block p-4 rounded-lg bg-white border border-gray-200">
              <div className="flex gap-2">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                <div
                  className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                  style={{ animationDelay: '0.2s' }}
                />
                <div
                  className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                  style={{ animationDelay: '0.4s' }}
                />
              </div>
            </div>
          </div>
        </div>
      )}

      <div ref={messagesEndRef} />
    </div>
  );
}
