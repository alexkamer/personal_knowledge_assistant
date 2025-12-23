/**
 * Command Palette - Universal search and action interface
 * Inspired by Linear, VS Code, and Obsidian
 *
 * Features:
 * - Cmd+K to open
 * - Fuzzy search across notes and commands
 * - Keyboard navigation (arrows, Enter, Escape)
 * - Recent items prioritized
 * - Shows keyboard shortcuts
 *
 * Usage:
 *   <CommandPalette isOpen={true} onClose={() => {}} onSelectNote={(id) => {}} />
 */

import { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import { Search, FileText, Plus, Tag, Clock, ArrowRight, Command } from 'lucide-react';
import { useNotes } from '@/hooks/useNotes';
import type { Note } from '@/types/note';

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectNote: (noteId: string) => void;
  onCreateNote?: () => void;
  onFilterByTag?: (tag: string) => void;
  currentNoteId?: string | null;
}

interface Command {
  id: string;
  label: string;
  description?: string;
  icon: React.ReactNode;
  shortcut?: string;
  action: () => void;
  category: 'action' | 'note' | 'recent';
  searchText: string; // Combined text for fuzzy matching
}

/**
 * Simple fuzzy match scoring
 * Returns a score (higher is better) if query matches text, or null if no match
 */
function fuzzyMatch(text: string, query: string): number | null {
  text = text.toLowerCase();
  query = query.toLowerCase();

  // Exact match gets highest score
  if (text.includes(query)) {
    return 1000 - text.indexOf(query);
  }

  // Fuzzy match: check if all query characters appear in order
  let textIndex = 0;
  let queryIndex = 0;
  let score = 0;
  let consecutiveMatches = 0;

  while (textIndex < text.length && queryIndex < query.length) {
    if (text[textIndex] === query[queryIndex]) {
      queryIndex++;
      consecutiveMatches++;
      score += consecutiveMatches * 10; // Bonus for consecutive matches
    } else {
      consecutiveMatches = 0;
    }
    textIndex++;
  }

  // All query characters must be found
  if (queryIndex === query.length) {
    return score;
  }

  return null;
}

export function CommandPalette({
  isOpen,
  onClose,
  onSelectNote,
  onCreateNote,
  onFilterByTag,
  currentNoteId,
}: CommandPaletteProps) {
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

  // Fetch all notes for searching (use a high limit to get most notes)
  const { data: notesData } = useNotes(0, 1000);
  const notes = notesData?.notes || [];

  // Load recent notes from localStorage
  const recentNoteIds = useMemo(() => {
    const stored = localStorage.getItem('recentNotes');
    if (!stored) return [];
    try {
      return JSON.parse(stored) as string[];
    } catch {
      return [];
    }
  }, []);

  // Build commands list
  const allCommands = useMemo((): Command[] => {
    const commands: Command[] = [];

    // Action commands
    commands.push({
      id: 'create-note',
      label: 'Create new note',
      description: 'Start writing a new note',
      icon: <Plus size={16} />,
      shortcut: 'Cmd+N',
      action: () => {
        onCreateNote?.();
        onClose();
      },
      category: 'action',
      searchText: 'create new note',
    });

    // Recent notes (prioritized)
    const recentNotes = notes
      .filter((note) => recentNoteIds.includes(note.id))
      .sort((a, b) => recentNoteIds.indexOf(a.id) - recentNoteIds.indexOf(b.id))
      .slice(0, 5);

    recentNotes.forEach((note) => {
      commands.push({
        id: `recent-${note.id}`,
        label: note.title,
        description: 'Recent',
        icon: <Clock size={16} />,
        action: () => {
          onSelectNote(note.id);
          onClose();
        },
        category: 'recent',
        searchText: note.title.toLowerCase(),
      });
    });

    // All notes (excluding recent and current)
    notes
      .filter((note) => !recentNoteIds.includes(note.id) && note.id !== currentNoteId)
      .forEach((note) => {
        commands.push({
          id: `note-${note.id}`,
          label: note.title,
          description: note.tags_rel.map((t) => t.name).join(', '),
          icon: <FileText size={16} />,
          action: () => {
            onSelectNote(note.id);
            onClose();
          },
          category: 'note',
          searchText: `${note.title.toLowerCase()} ${note.tags_rel.map((t) => t.name).join(' ')}`,
        });
      });

    // Tag filter commands
    if (onFilterByTag) {
      const allTags = new Set<string>();
      notes.forEach((note) => {
        note.tags_rel.forEach((tag) => allTags.add(tag.name));
      });

      allTags.forEach((tag) => {
        commands.push({
          id: `tag-${tag}`,
          label: `Filter by #${tag}`,
          description: 'Show all notes with this tag',
          icon: <Tag size={16} />,
          action: () => {
            onFilterByTag(tag);
            onClose();
          },
          category: 'action',
          searchText: `tag ${tag}`,
        });
      });
    }

    return commands;
  }, [notes, recentNoteIds, currentNoteId, onSelectNote, onCreateNote, onFilterByTag, onClose]);

  // Filter and rank commands based on query
  const filteredCommands = useMemo(() => {
    if (!query.trim()) {
      // No query: show recent notes first, then actions
      return allCommands
        .filter((cmd) => cmd.category === 'recent' || cmd.category === 'action')
        .slice(0, 10);
    }

    // Fuzzy match and score
    const scored = allCommands
      .map((cmd) => {
        const score = fuzzyMatch(cmd.searchText, query);
        return { command: cmd, score };
      })
      .filter((item) => item.score !== null)
      .sort((a, b) => {
        // Sort by score (higher is better)
        if (a.score !== b.score) {
          return (b.score || 0) - (a.score || 0);
        }
        // Tie-breaker: prefer recent notes
        if (a.command.category === 'recent' && b.command.category !== 'recent') return -1;
        if (a.command.category !== 'recent' && b.command.category === 'recent') return 1;
        return 0;
      });

    return scored.slice(0, 10).map((item) => item.command);
  }, [query, allCommands]);

  // Reset selection when filtered list changes
  useEffect(() => {
    setSelectedIndex(0);
  }, [filteredCommands]);

  // Focus input when opened
  useEffect(() => {
    if (isOpen) {
      inputRef.current?.focus();
      setQuery('');
      setSelectedIndex(0);
    }
  }, [isOpen]);

  // Keyboard navigation
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        onClose();
      } else if (e.key === 'ArrowDown') {
        e.preventDefault();
        setSelectedIndex((prev) => Math.min(prev + 1, filteredCommands.length - 1));
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setSelectedIndex((prev) => Math.max(prev - 1, 0));
      } else if (e.key === 'Enter') {
        e.preventDefault();
        const selected = filteredCommands[selectedIndex];
        if (selected) {
          selected.action();
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, selectedIndex, filteredCommands, onClose]);

  // Scroll selected item into view
  useEffect(() => {
    if (!listRef.current) return;
    const selectedElement = listRef.current.children[selectedIndex] as HTMLElement;
    if (selectedElement) {
      selectedElement.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
    }
  }, [selectedIndex]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center bg-black/50 pt-[20vh]"
      onClick={onClose}
    >
      <div
        className="w-full max-w-2xl overflow-hidden rounded-lg border border-gray-700 bg-white shadow-2xl dark:bg-gray-800"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Search Input */}
        <div className="flex items-center border-b border-gray-200 px-4 py-3 dark:border-gray-700">
          <Search size={20} className="mr-3 text-gray-400" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search notes or type a command..."
            className="flex-1 bg-transparent text-base text-gray-900 placeholder-gray-400 outline-none dark:text-gray-100"
          />
          <div className="ml-2 flex items-center gap-1 text-xs text-gray-400">
            <Command size={12} />
            <span>K</span>
          </div>
        </div>

        {/* Results List */}
        <div
          ref={listRef}
          className="max-h-[400px] overflow-y-auto overscroll-contain py-2"
        >
          {filteredCommands.length === 0 ? (
            <div className="px-4 py-8 text-center text-sm text-gray-500">
              No results found
            </div>
          ) : (
            filteredCommands.map((command, index) => (
              <button
                key={command.id}
                onClick={() => command.action()}
                className={`flex w-full items-center gap-3 px-4 py-3 text-left transition-colors ${
                  index === selectedIndex
                    ? 'bg-blue-50 dark:bg-blue-900/20'
                    : 'hover:bg-gray-50 dark:hover:bg-gray-700/50'
                }`}
              >
                {/* Icon */}
                <div
                  className={`flex-shrink-0 ${
                    index === selectedIndex
                      ? 'text-blue-600 dark:text-blue-400'
                      : 'text-gray-400'
                  }`}
                >
                  {command.icon}
                </div>

                {/* Label and Description */}
                <div className="flex-1 min-w-0">
                  <div className="truncate text-sm font-medium text-gray-900 dark:text-gray-100">
                    {command.label}
                  </div>
                  {command.description && (
                    <div className="truncate text-xs text-gray-500 dark:text-gray-400">
                      {command.description}
                    </div>
                  )}
                </div>

                {/* Shortcut or Arrow */}
                <div className="flex-shrink-0 text-xs text-gray-400">
                  {command.shortcut ? (
                    <span className="rounded bg-gray-100 px-1.5 py-0.5 font-mono dark:bg-gray-700">
                      {command.shortcut}
                    </span>
                  ) : (
                    <ArrowRight size={14} />
                  )}
                </div>
              </button>
            ))
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between border-t border-gray-200 px-4 py-2 text-xs text-gray-500 dark:border-gray-700">
          <span>↑↓ Navigate • Enter Select • Esc Close</span>
          <span>{filteredCommands.length} results</span>
        </div>
      </div>
    </div>
  );
}
