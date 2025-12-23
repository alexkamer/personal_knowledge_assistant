/**
 * Keyboard Shortcuts Reference Modal
 * Press '?' to open this modal and see all available shortcuts
 */

import { X, Command, Keyboard } from 'lucide-react';

interface KeyboardShortcutsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

interface ShortcutGroup {
  title: string;
  shortcuts: Array<{
    keys: string[];
    description: string;
  }>;
}

const shortcutGroups: ShortcutGroup[] = [
  {
    title: 'Global',
    shortcuts: [
      { keys: ['⌘', 'K'], description: 'Open Command Palette' },
    ],
  },
  {
    title: 'Text Formatting',
    shortcuts: [
      { keys: ['⌘', 'B'], description: 'Bold' },
      { keys: ['⌘', 'I'], description: 'Italic' },
      { keys: ['⌘', 'U'], description: 'Underline' },
      { keys: ['⌘', '⇧', 'X'], description: 'Strikethrough' },
      { keys: ['⌘', 'E'], description: 'Inline code' },
      { keys: ['⌘', '⇧', 'K'], description: 'Insert link' },
    ],
  },
  {
    title: 'Structure',
    shortcuts: [
      { keys: ['Tab'], description: 'Indent' },
      { keys: ['⇧', 'Tab'], description: 'Outdent' },
      { keys: ['/'], description: 'Slash command menu' },
      { keys: ['[', '['], description: 'Wiki link' },
      { keys: ['-', 'Space'], description: 'Bullet list' },
      { keys: ['1', '.', 'Space'], description: 'Numbered list' },
    ],
  },
  {
    title: 'Command Palette',
    shortcuts: [
      { keys: ['↑', '↓'], description: 'Navigate results' },
      { keys: ['Enter'], description: 'Select item' },
      { keys: ['Esc'], description: 'Close' },
    ],
  },
  {
    title: 'Standard',
    shortcuts: [
      { keys: ['⌘', 'Z'], description: 'Undo' },
      { keys: ['⌘', '⇧', 'Z'], description: 'Redo' },
      { keys: ['⌘', 'A'], description: 'Select all' },
      { keys: ['⌘', 'C'], description: 'Copy' },
      { keys: ['⌘', 'V'], description: 'Paste' },
    ],
  },
];

export function KeyboardShortcutsModal({ isOpen, onClose }: KeyboardShortcutsModalProps) {
  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
      onClick={onClose}
    >
      <div
        className="w-full max-w-4xl max-h-[90vh] overflow-hidden rounded-lg border border-gray-700 bg-white shadow-2xl dark:bg-gray-800"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-gray-200 px-6 py-4 dark:border-gray-700">
          <div className="flex items-center gap-3">
            <Keyboard size={24} className="text-blue-600 dark:text-blue-400" />
            <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
              Keyboard Shortcuts
            </h2>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-2 text-gray-400 transition-colors hover:bg-gray-100 hover:text-gray-600 dark:hover:bg-gray-700 dark:hover:text-gray-300"
            title="Close (Esc)"
          >
            <X size={20} />
          </button>
        </div>

        {/* Content */}
        <div className="overflow-y-auto p-6" style={{ maxHeight: 'calc(90vh - 80px)' }}>
          <div className="grid grid-cols-1 gap-8 md:grid-cols-2">
            {shortcutGroups.map((group) => (
              <div key={group.title} className="space-y-3">
                <h3 className="text-sm font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">
                  {group.title}
                </h3>
                <div className="space-y-2">
                  {group.shortcuts.map((shortcut, index) => (
                    <div
                      key={index}
                      className="flex items-center justify-between rounded-lg bg-gray-50 px-4 py-3 dark:bg-gray-700/50"
                    >
                      <span className="text-sm text-gray-700 dark:text-gray-300">
                        {shortcut.description}
                      </span>
                      <div className="flex items-center gap-1">
                        {shortcut.keys.map((key, keyIndex) => (
                          <kbd
                            key={keyIndex}
                            className="min-w-[28px] rounded border border-gray-300 bg-white px-2 py-1 text-center font-mono text-xs font-semibold text-gray-900 shadow-sm dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100"
                          >
                            {key}
                          </kbd>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>

          {/* Tips Section */}
          <div className="mt-8 rounded-lg border border-blue-200 bg-blue-50 p-4 dark:border-blue-900 dark:bg-blue-900/20">
            <div className="flex items-start gap-3">
              <Command size={20} className="mt-0.5 flex-shrink-0 text-blue-600 dark:text-blue-400" />
              <div className="space-y-2">
                <h4 className="font-semibold text-blue-900 dark:text-blue-100">
                  Pro Tips
                </h4>
                <ul className="space-y-1 text-sm text-blue-800 dark:text-blue-200">
                  <li>• Use <kbd className="rounded bg-blue-100 px-1.5 py-0.5 font-mono text-xs dark:bg-blue-800">⌘K</kbd> Command Palette for quick navigation</li>
                  <li>• Type <kbd className="rounded bg-blue-100 px-1.5 py-0.5 font-mono text-xs dark:bg-blue-800">[[</kbd> to create wiki links between notes</li>
                  <li>• Type <kbd className="rounded bg-blue-100 px-1.5 py-0.5 font-mono text-xs dark:bg-blue-800">/</kbd> for quick formatting options</li>
                  <li>• Recent notes appear first in Command Palette (no query needed)</li>
                </ul>
              </div>
            </div>
          </div>

          {/* Platform Note */}
          <div className="mt-4 text-center text-xs text-gray-500 dark:text-gray-400">
            On Windows/Linux, use <kbd className="rounded bg-gray-200 px-1.5 py-0.5 font-mono dark:bg-gray-700">Ctrl</kbd> instead of{' '}
            <kbd className="rounded bg-gray-200 px-1.5 py-0.5 font-mono dark:bg-gray-700">⌘</kbd>
          </div>
        </div>

        {/* Footer */}
        <div className="border-t border-gray-200 px-6 py-3 text-center text-xs text-gray-500 dark:border-gray-700 dark:text-gray-400">
          Press <kbd className="rounded bg-gray-100 px-1.5 py-0.5 font-mono dark:bg-gray-700">?</kbd> anytime to open this help •{' '}
          <kbd className="rounded bg-gray-100 px-1.5 py-0.5 font-mono dark:bg-gray-700">Esc</kbd> to close
        </div>
      </div>
    </div>
  );
}
