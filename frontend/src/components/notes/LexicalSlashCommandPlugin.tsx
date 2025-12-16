/**
 * Slash command plugin for Lexical editor
 * Shows formatting menu when user types "/"
 */
import { useEffect, useState, useCallback } from 'react';
import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';
import {
  $getSelection,
  $isRangeSelection,
  TextNode,
  COMMAND_PRIORITY_LOW,
  COMMAND_PRIORITY_HIGH,
  KEY_ARROW_DOWN_COMMAND,
  KEY_ARROW_UP_COMMAND,
  KEY_ENTER_COMMAND,
  KEY_ESCAPE_COMMAND,
} from 'lexical';
import { $setBlocksType } from '@lexical/selection';
import { $createHeadingNode } from '@lexical/rich-text';
import {
  INSERT_UNORDERED_LIST_COMMAND,
  INSERT_ORDERED_LIST_COMMAND,
  REMOVE_LIST_COMMAND,
  $isListNode,
} from '@lexical/list';
import { Bold, Italic, Underline as UnderlineIcon, Heading1, Heading2, Heading3, List, ListOrdered, Code } from 'lucide-react';
import { $createCodeNode } from '@lexical/code';

interface Command {
  id: string;
  label: string;
  icon: any;
  description: string;
  keywords: string[];
}

const COMMANDS: Command[] = [
  {
    id: 'heading1',
    label: 'Heading 1',
    icon: Heading1,
    description: 'Large heading',
    keywords: ['h1', 'heading', 'title'],
  },
  {
    id: 'heading2',
    label: 'Heading 2',
    icon: Heading2,
    description: 'Medium heading',
    keywords: ['h2', 'heading', 'subtitle'],
  },
  {
    id: 'heading3',
    label: 'Heading 3',
    icon: Heading3,
    description: 'Small heading',
    keywords: ['h3', 'heading'],
  },
  {
    id: 'bulletList',
    label: 'Bullet List',
    icon: List,
    description: 'Create a bulleted list',
    keywords: ['bullet', 'list', 'ul', 'unordered'],
  },
  {
    id: 'numberedList',
    label: 'Numbered List',
    icon: ListOrdered,
    description: 'Create a numbered list',
    keywords: ['number', 'list', 'ol', 'ordered'],
  },
  {
    id: 'code',
    label: 'Code Block',
    icon: Code,
    description: 'Insert a code block with syntax highlighting',
    keywords: ['code', 'snippet', 'programming', 'syntax'],
  },
];

export function LexicalSlashCommandPlugin() {
  const [editor] = useLexicalComposerContext();
  const [showMenu, setShowMenu] = useState(false);
  const [menuPosition, setMenuPosition] = useState<{ top: number; left: number } | null>(null);
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);

  // Filter commands based on query
  const filteredCommands = query
    ? COMMANDS.filter((cmd) =>
        [...cmd.keywords, cmd.label.toLowerCase()].some((keyword) =>
          keyword.includes(query.toLowerCase())
        )
      )
    : COMMANDS;

  const executeCommand = useCallback(
    (command: Command) => {
      editor.update(() => {
        const selection = $getSelection();
        if (!$isRangeSelection(selection)) return;

        // Get the text node containing the slash
        const anchor = selection.anchor;
        const textNode = anchor.getNode();

        if (textNode instanceof TextNode) {
          const text = textNode.getTextContent();
          const slashIndex = text.lastIndexOf('/');

          if (slashIndex !== -1) {
            // Remove everything from the slash onwards (including any query text)
            const beforeSlash = text.substring(0, slashIndex);
            textNode.setTextContent(beforeSlash);

            // Move cursor to end of the text node
            textNode.select();
          }
        }

        // Apply the formatting command
        if (command.id.startsWith('heading')) {
          const headingTag = command.id.replace('heading', 'h') as 'h1' | 'h2' | 'h3';
          $setBlocksType(selection, () => $createHeadingNode(headingTag));

          // After applying heading, remove any unwanted paragraph that was created
          // and keep cursor in the heading
          const newSelection = $getSelection();
          if ($isRangeSelection(newSelection)) {
            const currentNode = newSelection.anchor.getNode();
            const parent = currentNode.getTopLevelElementOrThrow();

            // Check if a sibling paragraph was created after the heading
            const nextSibling = parent.getNextSibling();
            if (nextSibling && nextSibling.getType() === 'paragraph') {
              // Check if it's empty or nearly empty
              const textContent = nextSibling.getTextContent();
              if (textContent.trim().length === 0) {
                nextSibling.remove();
              }
            }

            // Ensure cursor stays at the end of the heading
            parent.selectEnd();
          }
        } else if (command.id === 'bulletList') {
          editor.dispatchCommand(INSERT_UNORDERED_LIST_COMMAND, undefined);
        } else if (command.id === 'numberedList') {
          editor.dispatchCommand(INSERT_ORDERED_LIST_COMMAND, undefined);
        } else if (command.id === 'code') {
          $setBlocksType(selection, () => $createCodeNode());
        }
      });

      setShowMenu(false);
      setQuery('');
      setSelectedIndex(0);
    },
    [editor]
  );

  // Listen for "/" character
  useEffect(() => {
    return editor.registerUpdateListener(({ editorState }) => {
      editorState.read(() => {
        const selection = $getSelection();
        if (!$isRangeSelection(selection)) {
          setShowMenu(false);
          return;
        }

        const anchor = selection.anchor;
        const node = anchor.getNode();

        if (node instanceof TextNode) {
          const text = node.getTextContent();
          const offset = anchor.offset;

          // Check if we just typed "/"
          if (text[offset - 1] === '/') {
            setShowMenu(true);
            setQuery('');

            // Get cursor position for menu placement
            const domSelection = window.getSelection();
            if (domSelection && domSelection.rangeCount > 0) {
              const range = domSelection.getRangeAt(0);
              const rect = range.getBoundingClientRect();
              setMenuPosition({
                top: rect.bottom + window.scrollY,
                left: rect.left + window.scrollX,
              });
            }
          } else if (showMenu) {
            // Update query as user types
            const lastSlash = text.lastIndexOf('/');
            if (lastSlash !== -1 && offset > lastSlash) {
              setQuery(text.substring(lastSlash + 1, offset));
            } else {
              setShowMenu(false);
            }
          }
        }
      });
    });
  }, [editor, showMenu]);

  // Handle keyboard navigation with native event listener
  useEffect(() => {
    if (!showMenu) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'ArrowDown') {
        event.preventDefault();
        event.stopPropagation();
        setSelectedIndex((prev) => (prev + 1) % filteredCommands.length);
      } else if (event.key === 'ArrowUp') {
        event.preventDefault();
        event.stopPropagation();
        setSelectedIndex((prev) => (prev - 1 + filteredCommands.length) % filteredCommands.length);
      } else if (event.key === 'Enter') {
        event.preventDefault();
        event.stopPropagation();
        event.stopImmediatePropagation();
        if (filteredCommands[selectedIndex]) {
          executeCommand(filteredCommands[selectedIndex]);
        }
      } else if (event.key === 'Escape') {
        event.preventDefault();
        event.stopPropagation();
        setShowMenu(false);
        setQuery('');
      }
    };

    // Add listener at capture phase to intercept before Lexical
    document.addEventListener('keydown', handleKeyDown, true);

    return () => {
      document.removeEventListener('keydown', handleKeyDown, true);
    };
  }, [showMenu, filteredCommands, selectedIndex, executeCommand]);

  // Reset selected index when filtered commands change
  useEffect(() => {
    setSelectedIndex(0);
  }, [query]);

  if (!showMenu || !menuPosition) return null;

  return (
    <div
      className="fixed bg-white rounded-lg shadow-xl border border-gray-200 z-50 min-w-[280px] overflow-hidden"
      style={{ top: menuPosition.top, left: menuPosition.left }}
    >
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
                onClick={() => executeCommand(command)}
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
