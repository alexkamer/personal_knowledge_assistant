/**
 * Chat input component with glass-morphism design and model switcher.
 */
import React, { useState, useEffect } from 'react';
import { Send, ChevronDown, Globe, MessageSquare, GraduationCap } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
  initialValue?: string;
  selectedModel?: string;
  onModelChange?: (model: string) => void;
  webSearchEnabled?: boolean;
  onWebSearchToggle?: () => void;
  includeNotes?: boolean;
  onIncludeNotesToggle?: () => void;
  socraticMode?: boolean;
  onSocraticModeToggle?: () => void;
}

const AVAILABLE_MODELS = [
  { id: 'qwen2.5:14b', name: 'Qwen 2.5 14B', description: 'Best reasoning' },
  { id: 'phi4:14b', name: 'Phi-4 14B', description: 'Complex analysis' },
  { id: 'llama3.2:3b', name: 'Llama 3.2 3B', description: 'Fast responses' },
  { id: 'gemma3:latest', name: 'Gemma 3', description: 'Balanced' },
];

export function ChatInput({
  onSend,
  disabled = false,
  placeholder = 'Ask a question about your notes and documents...',
  initialValue = '',
  selectedModel = 'qwen2.5:14b',
  onModelChange,
  webSearchEnabled = true,
  onWebSearchToggle,
  includeNotes = false,
  onIncludeNotesToggle,
  socraticMode = false,
  onSocraticModeToggle,
}: ChatInputProps) {
  const [message, setMessage] = useState(initialValue);
  const [isModelDropdownOpen, setIsModelDropdownOpen] = useState(false);

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

  const currentModel = AVAILABLE_MODELS.find(m => m.id === selectedModel) || AVAILABLE_MODELS[0];

  return (
    <form
      onSubmit={handleSubmit}
      className="border-t border-white/20 dark:border-stone-800/50 p-6 bg-white/80 dark:bg-stone-900/80 backdrop-blur-xl backdrop-saturate-150 relative z-10"
    >
      <div className="max-w-4xl mx-auto space-y-4">
        {/* Top Controls Row */}
        <div className="flex items-center gap-3">
          {/* Model Switcher */}
          <div className="relative">
            <button
              type="button"
              onClick={() => setIsModelDropdownOpen(!isModelDropdownOpen)}
              className="flex items-center gap-2 px-3 py-2 rounded-lg bg-stone-100 dark:bg-stone-800 hover:bg-stone-200 dark:hover:bg-stone-700 border border-stone-300 dark:border-stone-700 transition-colors text-sm"
            >
              <span className="font-medium text-stone-900 dark:text-white">{currentModel.name}</span>
              <ChevronDown size={16} className="text-stone-600 dark:text-stone-400" />
            </button>

            {/* Model Dropdown */}
            {isModelDropdownOpen && (
              <>
                {/* Backdrop to close dropdown */}
                <div
                  className="fixed inset-0 z-10"
                  onClick={() => setIsModelDropdownOpen(false)}
                />

                {/* Dropdown menu */}
                <div className="absolute bottom-full mb-2 left-0 w-64 bg-white dark:bg-stone-800 rounded-xl shadow-2xl border border-stone-200 dark:border-stone-700 py-2 z-20">
                  <div className="px-3 py-2 text-xs font-semibold text-stone-500 dark:text-stone-400 uppercase tracking-wider">
                    Select Model
                  </div>
                  {AVAILABLE_MODELS.map((model) => (
                    <button
                      key={model.id}
                      type="button"
                      onClick={() => {
                        onModelChange?.(model.id);
                        setIsModelDropdownOpen(false);
                      }}
                      className={cn(
                        "w-full text-left px-3 py-2.5 hover:bg-stone-100 dark:hover:bg-stone-700 transition-colors",
                        selectedModel === model.id && "bg-indigo-50 dark:bg-indigo-900/20"
                      )}
                    >
                      <div className="font-medium text-stone-900 dark:text-white text-sm">
                        {model.name}
                      </div>
                      <div className="text-xs text-stone-600 dark:text-stone-400 mt-0.5">
                        {model.description}
                      </div>
                    </button>
                  ))}
                </div>
              </>
            )}
          </div>

          {/* Inline Toggles */}
          <div className="flex items-center gap-2">
            {/* Web Search Toggle */}
            {onWebSearchToggle && (
              <button
                type="button"
                onClick={onWebSearchToggle}
                className={cn(
                  "flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-xs transition-colors",
                  webSearchEnabled
                    ? "bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400 border border-green-300 dark:border-green-700"
                    : "bg-stone-100 dark:bg-stone-800 text-stone-600 dark:text-stone-400 border border-stone-300 dark:border-stone-700 hover:bg-stone-200 dark:hover:bg-stone-700"
                )}
              >
                <Globe size={13} />
                <span className="whitespace-nowrap">{webSearchEnabled ? '✓ Web' : 'Docs only'}</span>
              </button>
            )}

            {/* Include Notes Toggle */}
            {onIncludeNotesToggle && (
              <button
                type="button"
                onClick={onIncludeNotesToggle}
                className={cn(
                  "flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-xs transition-colors",
                  includeNotes
                    ? "bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-400 border border-blue-300 dark:border-blue-700"
                    : "bg-stone-100 dark:bg-stone-800 text-stone-600 dark:text-stone-400 border border-stone-300 dark:border-stone-700 hover:bg-stone-200 dark:hover:bg-stone-700"
                )}
              >
                <MessageSquare size={13} />
                <span className="whitespace-nowrap">{includeNotes ? '✓ Notes' : 'Verified only'}</span>
              </button>
            )}

            {/* Socratic Mode Toggle */}
            {onSocraticModeToggle && (
              <button
                type="button"
                onClick={onSocraticModeToggle}
                className={cn(
                  "flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-xs transition-colors",
                  socraticMode
                    ? "bg-purple-50 dark:bg-purple-900/20 text-purple-700 dark:text-purple-400 border border-purple-300 dark:border-purple-700"
                    : "bg-stone-100 dark:bg-stone-800 text-stone-600 dark:text-stone-400 border border-stone-300 dark:border-stone-700 hover:bg-stone-200 dark:hover:bg-stone-700"
                )}
                title="Enable Socratic Learning Mode: AI teaches through guided questions"
              >
                <GraduationCap size={13} />
                <span className="whitespace-nowrap">{socraticMode ? '✓ Socratic' : 'Direct'}</span>
              </button>
            )}
          </div>
        </div>

        {/* Input Area */}
        <div className="flex gap-3 items-end">
          <div className="flex-1">
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={placeholder}
              disabled={disabled}
              rows={3}
              className="w-full px-4 py-3 border border-stone-300 dark:border-stone-700 rounded-xl resize-none bg-white dark:bg-stone-800 text-stone-900 dark:text-white placeholder-stone-500 dark:placeholder-stone-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent disabled:bg-stone-100 dark:disabled:bg-stone-700 disabled:cursor-not-allowed transition-all"
            />
            <p className="mt-2 text-xs text-stone-500 dark:text-stone-400">
              Press Enter to send, Shift+Enter for new line
            </p>
          </div>

          <button
            type="submit"
            disabled={disabled || !message.trim()}
            className="flex-shrink-0 p-4 bg-gradient-to-r from-indigo-500 to-indigo-600 hover:from-indigo-600 hover:to-indigo-700 text-white rounded-xl hover:shadow-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            aria-label="Send message"
          >
            <Send size={20} />
          </button>
        </div>
      </div>
    </form>
  );
}
