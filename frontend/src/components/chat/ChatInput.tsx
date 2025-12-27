/**
 * Chat input component with glass-morphism design and model switcher.
 */
import React, { useState, useEffect, useRef } from 'react';
import { Send, ChevronDown, Globe, MessageSquare, GraduationCap, Paperclip, Square, Bot } from 'lucide-react';
import { cn } from '@/lib/utils';
import { ChatAttachment } from './ChatAttachment';

// Source filter options
export type SourceFilter = 'general' | 'docs' | 'web';

interface ChatInputProps {
  onSend: (message: string, files?: File[]) => void;
  disabled?: boolean;
  placeholder?: string;
  initialValue?: string;
  selectedModel?: string;
  onModelChange?: (model: string) => void;
  sourceFilter?: SourceFilter;
  onSourceFilterChange?: (filter: SourceFilter) => void;
  socraticMode?: boolean;
  onSocraticModeToggle?: () => void;
  agentMode?: boolean;
  onAgentModeToggle?: () => void;
  isStreaming?: boolean;
  onStopGeneration?: () => void;
}

const AVAILABLE_MODELS = [
  { id: 'gemini-2.5-flash', name: 'Gemini 2.5 Flash', description: 'Google - Best price-performance', category: 'cloud' },
  { id: 'gemini-2.0-flash-exp', name: 'Gemini 2.0 Flash', description: 'Google - Balanced multimodal', category: 'cloud' },
  { id: 'gemini-2.5-flash-preview', name: 'Gemini 2.5 Flash Preview', description: 'Google - Preview version', category: 'cloud' },
  { id: 'gemini-2.5-flash-lite-preview', name: 'Gemini 2.5 Flash Lite', description: 'Google - Fastest & cheapest', category: 'cloud' },
  { id: 'qwen2.5:14b', name: 'Qwen 2.5 14B', description: 'Best reasoning', category: 'local' },
  { id: 'phi4:14b', name: 'Phi-4 14B', description: 'Complex analysis', category: 'local' },
  { id: 'llama3.2:3b', name: 'Llama 3.2 3B', description: 'Fast responses', category: 'local' },
  { id: 'gemma3:latest', name: 'Gemma 3', description: 'Balanced', category: 'local' },
];

const MAX_FILE_SIZE_MB = 25;
const MAX_FILES = 5;
const ALLOWED_FILE_TYPES = ['.pdf', '.docx', '.txt', '.md'];

export function ChatInput({
  onSend,
  disabled = false,
  placeholder = 'Ask a question about your notes and documents...',
  initialValue = '',
  selectedModel = 'gemini-2.5-flash',
  onModelChange,
  sourceFilter = 'general',
  onSourceFilterChange,
  socraticMode = false,
  onSocraticModeToggle,
  agentMode = false,
  onAgentModeToggle,
  isStreaming = false,
  onStopGeneration,
}: ChatInputProps) {
  const [message, setMessage] = useState(initialValue);
  const [isModelDropdownOpen, setIsModelDropdownOpen] = useState(false);
  const [attachedFiles, setAttachedFiles] = useState<File[]>([]);
  const [fileError, setFileError] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const dragCounterRef = useRef(0); // Track drag enter/leave events

  // Update message when initialValue changes (from prefilled questions)
  useEffect(() => {
    if (initialValue) {
      setMessage(initialValue);
    }
  }, [initialValue]);

  const validateFiles = (files: FileList | File[]): File[] => {
    const fileArray = Array.from(files);
    const validFiles: File[] = [];
    let error: string | null = null;

    // Check total count
    if (attachedFiles.length + fileArray.length > MAX_FILES) {
      setFileError(`Maximum ${MAX_FILES} files allowed`);
      return [];
    }

    for (const file of fileArray) {
      // Check file size
      const sizeMB = file.size / (1024 * 1024);
      if (sizeMB > MAX_FILE_SIZE_MB) {
        error = `File "${file.name}" exceeds ${MAX_FILE_SIZE_MB}MB limit`;
        break;
      }

      // Check file type
      const extension = '.' + file.name.split('.').pop()?.toLowerCase();
      if (!ALLOWED_FILE_TYPES.includes(extension)) {
        error = `File type "${extension}" not supported. Allowed: ${ALLOWED_FILE_TYPES.join(', ')}`;
        break;
      }

      validFiles.push(file);
    }

    if (error) {
      setFileError(error);
      return [];
    }

    return validFiles;
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFileError(null);
    if (e.target.files) {
      const validFiles = validateFiles(e.target.files);
      if (validFiles.length > 0) {
        setAttachedFiles([...attachedFiles, ...validFiles]);
      }
    }
    // Reset input so same file can be selected again
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleRemoveFile = (index: number) => {
    setAttachedFiles(attachedFiles.filter((_, i) => i !== index));
    setFileError(null);
  };

  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    dragCounterRef.current++;
    if (e.dataTransfer.items && e.dataTransfer.items.length > 0) {
      setIsDragging(true);
    }
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    dragCounterRef.current--;
    if (dragCounterRef.current === 0) {
      setIsDragging(false);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    dragCounterRef.current = 0;

    setFileError(null);
    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      const validFiles = validateFiles(files);
      if (validFiles.length > 0) {
        setAttachedFiles([...attachedFiles, ...validFiles]);
      }
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = message.trim();
    if (trimmed && !disabled) {
      onSend(trimmed, attachedFiles.length > 0 ? attachedFiles : undefined);
      setMessage('');
      setAttachedFiles([]);
      setFileError(null);
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
      className="border-t border-white/10 dark:border-gray-800/50 p-4 bg-transparent relative z-10"
    >
      <div className="max-w-3xl mx-auto space-y-3">
        {/* Top Controls Row */}
        <div className="flex items-center gap-3">
          {/* Model Switcher */}
          <div className="relative">
            <button
              type="button"
              onClick={() => setIsModelDropdownOpen(!isModelDropdownOpen)}
              className="flex items-center gap-2 px-3 py-2 rounded-lg bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 border border-gray-300 dark:border-gray-700 transition-colors text-sm"
            >
              <span className="font-medium text-gray-900 dark:text-white">{currentModel.name}</span>
              <ChevronDown size={16} className="text-gray-600 dark:text-gray-400" />
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
                <div className="absolute bottom-full mb-2 left-0 w-64 bg-white dark:bg-gray-800 rounded-xl shadow-2xl border border-gray-200 dark:border-gray-700 py-2 z-20">
                  {/* Cloud Models Section */}
                  <div className="px-3 py-2 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Cloud Models
                  </div>
                  {AVAILABLE_MODELS.filter(m => m.category === 'cloud').map((model) => (
                    <button
                      key={model.id}
                      type="button"
                      onClick={() => {
                        onModelChange?.(model.id);
                        setIsModelDropdownOpen(false);
                      }}
                      className={cn(
                        "w-full text-left px-3 py-2.5 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors",
                        selectedModel === model.id && "bg-primary-50 dark:bg-primary-900/20"
                      )}
                    >
                      <div className="font-medium text-gray-900 dark:text-white text-sm">
                        {model.name}
                      </div>
                      <div className="text-xs text-gray-600 dark:text-gray-400 mt-0.5">
                        {model.description}
                      </div>
                    </button>
                  ))}

                  {/* Divider */}
                  <div className="my-2 border-t border-gray-200 dark:border-gray-700" />

                  {/* Local Models Section */}
                  <div className="px-3 py-2 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Local Models
                  </div>
                  {AVAILABLE_MODELS.filter(m => m.category === 'local').map((model) => (
                    <button
                      key={model.id}
                      type="button"
                      onClick={() => {
                        onModelChange?.(model.id);
                        setIsModelDropdownOpen(false);
                      }}
                      className={cn(
                        "w-full text-left px-3 py-2.5 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors",
                        selectedModel === model.id && "bg-primary-50 dark:bg-primary-900/20"
                      )}
                    >
                      <div className="font-medium text-gray-900 dark:text-white text-sm">
                        {model.name}
                      </div>
                      <div className="text-xs text-gray-600 dark:text-gray-400 mt-0.5">
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
            {/* Source Filter Button Group */}
            {onSourceFilterChange && (
              <div className="flex items-center gap-0.5 p-0.5 bg-gray-100 dark:bg-gray-800 rounded-lg border border-gray-300 dark:border-gray-700">
                <button
                  type="button"
                  onClick={() => onSourceFilterChange('web')}
                  className={cn(
                    "flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-xs transition-colors",
                    sourceFilter === 'web'
                      ? "bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400 border border-green-300 dark:border-green-700 shadow-sm"
                      : "text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
                  )}
                  title="Search the web"
                >
                  <Globe size={13} />
                  <span className="whitespace-nowrap">Web</span>
                </button>

                <button
                  type="button"
                  onClick={() => onSourceFilterChange('docs')}
                  className={cn(
                    "flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-xs transition-colors",
                    sourceFilter === 'docs'
                      ? "bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-400 border border-blue-300 dark:border-blue-700 shadow-sm"
                      : "text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
                  )}
                  title="Search your documents only"
                >
                  <MessageSquare size={13} />
                  <span className="whitespace-nowrap">Docs only</span>
                </button>

                <button
                  type="button"
                  onClick={() => onSourceFilterChange('general')}
                  className={cn(
                    "flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-xs transition-colors",
                    sourceFilter === 'general'
                      ? "bg-purple-50 dark:bg-purple-900/20 text-purple-700 dark:text-purple-400 border border-purple-300 dark:border-purple-700 shadow-sm"
                      : "text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
                  )}
                  title="Use general knowledge only (no document search)"
                >
                  <GraduationCap size={13} />
                  <span className="whitespace-nowrap">General</span>
                </button>
              </div>
            )}

            {/* Socratic Mode Toggle */}
            {onSocraticModeToggle && (
              <button
                type="button"
                onClick={onSocraticModeToggle}
                className={cn(
                  "flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-xs transition-colors",
                  socraticMode
                    ? "bg-orange-50 dark:bg-orange-900/20 text-orange-700 dark:text-orange-400 border border-orange-300 dark:border-orange-700"
                    : "bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 border border-gray-300 dark:border-gray-700 hover:bg-gray-200 dark:hover:bg-gray-700"
                )}
                title="Enable Socratic Learning Mode: AI teaches through guided questions"
              >
                <GraduationCap size={13} />
                <span className="whitespace-nowrap">{socraticMode ? '✓ Socratic' : 'Direct'}</span>
              </button>
            )}

            {/* Agent Mode Toggle */}
            {onAgentModeToggle && (
              <button
                type="button"
                onClick={onAgentModeToggle}
                className={cn(
                  "flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-xs transition-colors",
                  agentMode
                    ? "bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-400 border border-blue-300 dark:border-blue-700"
                    : "bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 border border-gray-300 dark:border-gray-700 hover:bg-gray-200 dark:hover:bg-gray-700"
                )}
                title="Enable Agent Mode: AI decides when to search your knowledge base"
              >
                <Bot size={13} />
                <span className="whitespace-nowrap">{agentMode ? '✓ Agent' : 'Standard'}</span>
              </button>
            )}
          </div>
        </div>

        {/* Attached Files Display */}
        {attachedFiles.length > 0 && (
          <div className="flex flex-wrap gap-2 px-1">
            {attachedFiles.map((file, index) => (
              <ChatAttachment
                key={`${file.name}-${index}`}
                filename={file.name}
                size={file.size}
                onRemove={() => handleRemoveFile(index)}
                status="pending"
              />
            ))}
          </div>
        )}

        {/* File Error Message */}
        {fileError && (
          <div className="px-1 text-sm text-red-600 dark:text-red-400">
            {fileError}
          </div>
        )}

        {/* Input Area */}
        <div className="flex gap-3 items-end">
          {/* File Input (hidden) */}
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept={ALLOWED_FILE_TYPES.join(',')}
            onChange={handleFileSelect}
            className="hidden"
          />

          <div className="flex-1">
            <div
              className="relative"
              data-chat-input-dropzone
              onDragEnter={handleDragEnter}
              onDragLeave={handleDragLeave}
              onDragOver={handleDragOver}
              onDrop={handleDrop}
            >
              <textarea
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={placeholder}
                disabled={disabled}
                rows={3}
                className="w-full px-4 py-3 pr-12 border border-gray-300 dark:border-gray-700 rounded-xl resize-none bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-stone-500 dark:placeholder-stone-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent disabled:bg-gray-100 dark:disabled:bg-gray-700 disabled:cursor-not-allowed transition-all"
              />

              {/* Drag and Drop Overlay */}
              {isDragging && (
                <div className="absolute inset-0 bg-indigo-50 dark:bg-indigo-900/20 border-2 border-dashed border-indigo-500 rounded-xl flex items-center justify-center z-10 pointer-events-none">
                  <div className="text-center">
                    <Paperclip className="w-8 h-8 mx-auto mb-2 text-indigo-600 dark:text-indigo-400" />
                    <p className="text-sm font-medium text-indigo-700 dark:text-indigo-300">
                      Drop files here
                    </p>
                    <p className="text-xs text-indigo-600 dark:text-indigo-400 mt-1">
                      PDF, DOCX, TXT, MD (max 25MB)
                    </p>
                  </div>
                </div>
              )}

              {/* Attach File Button (inside textarea) */}
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                disabled={disabled || attachedFiles.length >= MAX_FILES}
                className="absolute right-3 bottom-3 p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                title={attachedFiles.length >= MAX_FILES ? `Maximum ${MAX_FILES} files allowed` : 'Attach files (PDF, DOCX, TXT, MD)'}
              >
                <Paperclip size={18} />
              </button>
            </div>

            <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
              Press Enter to send, Shift+Enter for new line
              {attachedFiles.length > 0 && ` • ${attachedFiles.length}/${MAX_FILES} files attached`}
            </p>
          </div>

          {isStreaming ? (
            <button
              type="button"
              onClick={onStopGeneration}
              className="flex-shrink-0 p-4 bg-red-500 hover:bg-red-600 text-white rounded-xl hover:shadow-lg focus:outline-none focus:ring-2 focus:ring-red-500 transition-all"
              aria-label="Stop generation"
            >
              <Square size={20} fill="currentColor" />
            </button>
          ) : (
            <button
              type="submit"
              disabled={disabled || !message.trim()}
              className="flex-shrink-0 p-4 bg-primary-500 hover:bg-primary-600 text-white rounded-xl hover:shadow-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
              aria-label="Send message"
            >
              <Send size={20} />
            </button>
          )}
        </div>
      </div>
    </form>
  );
}
