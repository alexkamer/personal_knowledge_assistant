/**
 * Chat input component for sending messages.
 */
import React, { useState, useEffect } from 'react';
import { Send } from 'lucide-react';

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
  initialValue?: string;
}

export function ChatInput({
  onSend,
  disabled = false,
  placeholder = 'Ask a question about your notes and documents...',
  initialValue = '',
}: ChatInputProps) {
  const [message, setMessage] = useState(initialValue);

  // Update message when initialValue changes (from prefilled questions)
  useEffect(() => {
    if (initialValue) {
      setMessage(initialValue);
    }
  }, [initialValue]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = message.trim();
    if (trimmed && !disabled) {
      onSend(trimmed);
      setMessage('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="border-t border-stone-200 dark:border-stone-800 p-4 bg-white dark:bg-stone-900">
      <div className="flex gap-3 items-end">
        <div className="flex-1">
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={disabled}
            rows={3}
            className="w-full px-4 py-3 border border-stone-300 dark:border-stone-700 rounded-lg resize-none bg-white dark:bg-stone-800 text-stone-900 dark:text-white placeholder-stone-500 dark:placeholder-stone-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-stone-100 dark:disabled:bg-stone-700 disabled:cursor-not-allowed"
          />
          <p className="mt-2 text-xs text-stone-500 dark:text-stone-400">
            Press Enter to send, Shift+Enter for new line
          </p>
        </div>

        <button
          type="submit"
          disabled={disabled || !message.trim()}
          className="flex-shrink-0 p-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-stone-300 dark:disabled:bg-stone-700 disabled:cursor-not-allowed transition-colors"
          aria-label="Send message"
        >
          <Send size={20} />
        </button>
      </div>
    </form>
  );
}
