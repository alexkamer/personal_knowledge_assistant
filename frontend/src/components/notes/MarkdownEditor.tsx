/**
 * Markdown editor with preview-first UX - Notion-like interface.
 * Shows rendered content by default, click to edit.
 */
import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Edit2 } from 'lucide-react';

interface MarkdownEditorProps {
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

export function MarkdownEditor({ value, onChange, disabled, placeholder }: MarkdownEditorProps) {
  const [isEditing, setIsEditing] = useState(false);

  return (
    <div className="space-y-2">
      {/* Rendered preview or edit mode */}
      {!isEditing ? (
        <div className="group relative">
          {/* Preview Content */}
          <div
            onClick={() => !disabled && setIsEditing(true)}
            className={`prose prose-sm max-w-none p-6 border-2 border-stone-200 rounded-lg min-h-[300px] bg-white transition-all ${
              !disabled ? 'cursor-text hover:border-blue-300 hover:shadow-sm' : ''
            }`}
          >
            {value ? (
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {value}
              </ReactMarkdown>
            ) : (
              <p className="text-stone-400 italic">
                {placeholder || 'Click to start writing...'}
              </p>
            )}
          </div>

          {/* Edit button hint on hover */}
          {!disabled && value && (
            <button
              type="button"
              onClick={() => setIsEditing(true)}
              className="absolute top-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1.5 px-3 py-1.5 bg-white border border-stone-300 rounded-md text-xs font-medium text-stone-700 hover:bg-stone-50 shadow-sm"
            >
              <Edit2 size={12} />
              Edit
            </button>
          )}
        </div>
      ) : (
        <div className="space-y-3">
          {/* Edit mode */}
          <textarea
            value={value}
            onChange={(e) => onChange(e.target.value)}
            rows={14}
            autoFocus
            className="w-full px-4 py-3 border-2 border-blue-400 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm resize-y shadow-sm"
            placeholder={placeholder || 'Write your note in Markdown...\n\n**Bold**, *italic*, `code`, [links](url), and more!'}
            disabled={disabled}
          />

          {/* Done editing button */}
          <div className="flex items-center justify-between">
            <div className="text-xs text-stone-500">
              <span className="font-medium">Markdown:</span> **bold** *italic* `code` [link](url) # heading - list &gt; quote
            </div>
            <button
              type="button"
              onClick={() => setIsEditing(false)}
              className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 transition-colors"
            >
              Done Editing
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
