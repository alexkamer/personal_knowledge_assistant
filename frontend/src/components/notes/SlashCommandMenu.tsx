/**
 * Slash command menu for formatting and quick actions
 * - Searchable/filterable as user types
 * - Fuzzy matching to highlight closest match
 * - Enter key selects highlighted command
 */
import { useState, useEffect, useRef } from 'react';
import { Bold, Italic, Underline as UnderlineIcon, Heading1, Heading2, Heading3, Palette, Highlighter } from 'lucide-react';

interface SlashCommand {
  id: string;
  label: string;
  icon: any;
  description: string;
  action: () => void;
}

interface SlashCommandMenuProps {
  position: { top: number; left: number };
  onSelect: (command: SlashCommand) => void;
  onClose: () => void;
  searchQuery?: string;
}

export function SlashCommandMenu({ position, onSelect, onClose, searchQuery = '' }: SlashCommandMenuProps) {
  const [query, setQuery] = useState(searchQuery);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  const commands: SlashCommand[] = [
    {
      id: 'bold',
      label: 'Bold',
      icon: Bold,
      description: 'Make text bold',
      action: () => {},
    },
    {
      id: 'italic',
      label: 'Italic',
      icon: Italic,
      description: 'Make text italic',
      action: () => {},
    },
    {
      id: 'underline',
      label: 'Underline',
      icon: UnderlineIcon,
      description: 'Underline text',
      action: () => {},
    },
    {
      id: 'heading1',
      label: 'Heading 1',
      icon: Heading1,
      description: 'Large heading',
      action: () => {},
    },
    {
      id: 'heading2',
      label: 'Heading 2',
      icon: Heading2,
      description: 'Medium heading',
      action: () => {},
    },
    {
      id: 'heading3',
      label: 'Heading 3',
      icon: Heading3,
      description: 'Small heading',
      action: () => {},
    },
    {
      id: 'color',
      label: 'Text Color',
      icon: Palette,
      description: 'Change text color',
      action: () => {},
    },
    {
      id: 'highlight',
      label: 'Highlight',
      icon: Highlighter,
      description: 'Highlight background',
      action: () => {},
    },
  ];

  // Fuzzy match scoring - returns a score based on how well the query matches
  const fuzzyScore = (text: string, query: string): number => {
    if (!query) return 1; // No query = all items match equally

    const textLower = text.toLowerCase();
    const queryLower = query.toLowerCase();

    // Exact match at start = highest score
    if (textLower.startsWith(queryLower)) return 1000;

    // Contains query = high score
    if (textLower.includes(queryLower)) return 500;

    // Fuzzy match - check if all query characters appear in order
    let queryIndex = 0;
    let score = 0;

    for (let i = 0; i < textLower.length && queryIndex < queryLower.length; i++) {
      if (textLower[i] === queryLower[queryIndex]) {
        score += 100;
        queryIndex++;
      }
    }

    // Return score if all characters matched, otherwise 0
    return queryIndex === queryLower.length ? score : 0;
  };

  // Filter and sort commands by fuzzy match score
  const filteredCommands = commands
    .map((cmd) => ({
      command: cmd,
      score: Math.max(
        fuzzyScore(cmd.label, query),
        fuzzyScore(cmd.description, query)
      ),
    }))
    .filter((item) => item.score > 0)
    .sort((a, b) => b.score - a.score)
    .map((item) => item.command);

  // Auto-focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  // Reset selected index when filtered results change
  useEffect(() => {
    setSelectedIndex(0);
  }, [query]);

  // Handle keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      e.stopPropagation();
      setSelectedIndex((prev) => (prev + 1) % filteredCommands.length);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      e.stopPropagation();
      setSelectedIndex((prev) => (prev - 1 + filteredCommands.length) % filteredCommands.length);
    } else if (e.key === 'Enter') {
      e.preventDefault();
      e.stopPropagation();
      if (filteredCommands[selectedIndex]) {
        onSelect(filteredCommands[selectedIndex]);
      }
    } else if (e.key === 'Escape') {
      e.preventDefault();
      e.stopPropagation();
      onClose();
    }
  };

  return (
    <div
      className="fixed bg-white rounded-lg shadow-xl border border-gray-200 z-50 min-w-[280px] overflow-hidden"
      style={{ top: position.top, left: position.left }}
    >
      {/* Search input */}
      <div className="border-b border-gray-200 p-2">
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Search commands..."
          className="w-full px-2 py-1 text-sm outline-none"
        />
      </div>

      {/* Command list */}
      <div className="py-2 max-h-[300px] overflow-y-auto">
        {filteredCommands.length === 0 ? (
          <div className="px-4 py-2.5 text-sm text-gray-500">No commands found</div>
        ) : (
          filteredCommands.map((command, index) => {
            const Icon = command.icon;
            const isSelected = index === selectedIndex;

            return (
              <button
                key={command.id}
                onClick={() => {
                  onSelect(command);
                  onClose();
                }}
                onMouseEnter={() => setSelectedIndex(index)}
                className={`w-full flex items-center gap-3 px-4 py-2.5 transition-colors text-left ${
                  isSelected ? 'bg-blue-100' : 'hover:bg-blue-50'
                }`}
              >
                <Icon size={18} className="text-gray-600" />
                <div className="flex-1">
                  <div className="text-sm font-medium text-gray-900">{command.label}</div>
                  <div className="text-xs text-gray-500">{command.description}</div>
                </div>
              </button>
            );
          })
        )}
      </div>
    </div>
  );
}
