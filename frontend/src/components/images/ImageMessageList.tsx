/**
 * List of image generation messages (prompts and images).
 */
import { useEffect, useRef } from 'react';
import { Loader2 } from 'lucide-react';
import { ImageMessage } from './ImageMessage';
import type { ImageGenerationMessage } from '@/types/imageGeneration';

interface ImageMessageListProps {
  messages: ImageGenerationMessage[];
  isStreaming: boolean;
  status?: string;
}

export function ImageMessageList({ messages, isStreaming, status }: ImageMessageListProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isStreaming]);

  return (
    <div className="h-full overflow-y-auto">
      {messages.length === 0 && !isStreaming ? (
        // Empty state
        <div className="h-full flex items-center justify-center">
          <div className="text-center max-w-md px-4">
            <div className="w-16 h-16 mx-auto mb-4 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-2xl flex items-center justify-center">
              <svg className="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
                />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-white mb-2">Generate Amazing Images</h2>
            <p className="text-gray-400 mb-4">
              Describe the image you want to create and let AI bring your vision to life.
            </p>
            <div className="text-sm text-gray-500 space-y-1">
              <p>Try: "A serene mountain landscape at sunset"</p>
              <p>Or: "A futuristic city with flying cars"</p>
            </div>
          </div>
        </div>
      ) : (
        // Messages
        <div className="py-6 space-y-6">
          {messages.map((message) => (
            <ImageMessage key={message.id} message={message} />
          ))}

          {/* Loading indicator */}
          {isStreaming && status && (
            <div className="max-w-3xl mx-auto px-4">
              <div className="flex items-center gap-3 text-gray-400">
                <Loader2 className="animate-spin" size={20} />
                <span className="text-sm">{status}</span>
              </div>
            </div>
          )}

          {/* Scroll anchor */}
          <div ref={messagesEndRef} />
        </div>
      )}
    </div>
  );
}
