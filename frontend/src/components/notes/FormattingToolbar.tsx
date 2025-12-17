/**
 * Floating formatting toolbar for text selection
 */
import { Bold, Italic, Underline as UnderlineIcon, Palette, Highlighter } from 'lucide-react';

interface FormattingToolbarProps {
  position: { top: number; left: number };
  onFormat: (format: string, value?: string) => void;
  onClose: () => void;
}

export function FormattingToolbar({ position, onFormat }: FormattingToolbarProps) {
  const colors = [
    { name: 'Red', value: '#ef4444' },
    { name: 'Orange', value: '#f97316' },
    { name: 'Yellow', value: '#eab308' },
    { name: 'Green', value: '#22c55e' },
    { name: 'Blue', value: '#3b82f6' },
    { name: 'Purple', value: '#a855f7' },
    { name: 'Pink', value: '#ec4899' },
    { name: 'Gray', value: '#6b7280' },
  ];

  const highlights = [
    { name: 'Yellow', value: '#fef08a' },
    { name: 'Green', value: '#bbf7d0' },
    { name: 'Blue', value: '#bfdbfe' },
    { name: 'Purple', value: '#e9d5ff' },
    { name: 'Pink', value: '#fbcfe8' },
    { name: 'Red', value: '#fecaca' },
  ];

  return (
    <div
      className="fixed bg-white rounded-lg shadow-xl border border-stone-200 p-2 z-50 flex gap-1"
      style={{ top: position.top - 50, left: position.left }}
    >
      {/* Bold */}
      <button
        onClick={() => onFormat('bold')}
        className="p-2 hover:bg-stone-100 rounded transition-colors"
        title="Bold (Cmd+B)"
      >
        <Bold size={16} className="text-stone-700" />
      </button>

      {/* Italic */}
      <button
        onClick={() => onFormat('italic')}
        className="p-2 hover:bg-stone-100 rounded transition-colors"
        title="Italic (Cmd+I)"
      >
        <Italic size={16} className="text-stone-700" />
      </button>

      {/* Underline */}
      <button
        onClick={() => onFormat('underline')}
        className="p-2 hover:bg-stone-100 rounded transition-colors"
        title="Underline (Cmd+U)"
      >
        <UnderlineIcon size={16} className="text-stone-700" />
      </button>

      {/* Divider */}
      <div className="w-px bg-stone-300 mx-1" />

      {/* Text Color */}
      <div className="relative group">
        <button className="p-2 hover:bg-stone-100 rounded transition-colors" title="Text Color">
          <Palette size={16} className="text-stone-700" />
        </button>
        <div className="hidden group-hover:block absolute top-full left-0 mt-1 bg-white rounded-lg shadow-xl border border-stone-200 p-2">
          <div className="text-xs font-medium text-stone-600 mb-2 px-1">Text Color</div>
          <div className="grid grid-cols-4 gap-1">
            {colors.map((color) => (
              <button
                key={color.value}
                onClick={() => onFormat('color', color.value)}
                className="w-6 h-6 rounded border border-stone-300 hover:scale-110 transition-transform"
                style={{ backgroundColor: color.value }}
                title={color.name}
              />
            ))}
          </div>
        </div>
      </div>

      {/* Highlight */}
      <div className="relative group">
        <button className="p-2 hover:bg-stone-100 rounded transition-colors" title="Highlight">
          <Highlighter size={16} className="text-stone-700" />
        </button>
        <div className="hidden group-hover:block absolute top-full left-0 mt-1 bg-white rounded-lg shadow-xl border border-stone-200 p-2">
          <div className="text-xs font-medium text-stone-600 mb-2 px-1">Highlight</div>
          <div className="grid grid-cols-3 gap-1">
            {highlights.map((highlight) => (
              <button
                key={highlight.value}
                onClick={() => onFormat('highlight', highlight.value)}
                className="w-6 h-6 rounded border border-stone-300 hover:scale-110 transition-transform"
                style={{ backgroundColor: highlight.value }}
                title={highlight.name}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
