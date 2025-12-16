/**
 * WikiLinkPlugin - Detects [[Note Title]] syntax and converts to WikiLinkNodes
 * Also provides autocomplete for note titles
 */
import { useEffect, useState, useCallback } from 'react';
import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';
import {
  $getSelection,
  $isRangeSelection,
  $isTextNode,
  COMMAND_PRIORITY_LOW,
  KEY_ENTER_COMMAND,
  TextNode,
} from 'lexical';
import { $createWikiLinkNode, WikiLinkNode } from './WikiLinkNode';
import { useNotes } from '../../hooks/useNotes';

const WIKI_LINK_REGEX = /\[\[([^\]]+)\]\]/g;

/**
 * Find best matching note for a wiki link title
 * Priority: exact match > starts with > contains
 */
function findMatchingNote(notes: any[], wikiLinkTitle: string) {
  const searchLower = wikiLinkTitle.toLowerCase().trim();

  // Try exact match first (case-insensitive)
  const exactMatch = notes.find(
    (n) => n.title.toLowerCase().trim() === searchLower
  );
  if (exactMatch) return exactMatch;

  // Try starts with (for partial matches like "Python" matching "Python Best Practices")
  const startsWithMatch = notes.find((n) =>
    n.title.toLowerCase().trim().startsWith(searchLower)
  );
  if (startsWithMatch) return startsWithMatch;

  // Try contains anywhere in title
  const containsMatch = notes.find((n) =>
    n.title.toLowerCase().includes(searchLower)
  );
  return containsMatch || null;
}

export function WikiLinkPlugin() {
  const [editor] = useLexicalComposerContext();
  const { data: notesData } = useNotes();
  const notes = notesData?.notes || [];
  const [showAutocomplete, setShowAutocomplete] = useState(false);
  const [autocompleteQuery, setAutocompleteQuery] = useState('');
  const [autocompletePosition, setAutocompletePosition] = useState({ top: 0, left: 0 });

  // Convert [[text]] to WikiLinkNodes
  const convertWikiLinks = useCallback(() => {
    editor.update(() => {
      const selection = $getSelection();
      if (!$isRangeSelection(selection)) return;

      const nodes = selection.getNodes();

      nodes.forEach((node) => {
        if (!$isTextNode(node)) return;

        const text = node.getTextContent();
        const matches = Array.from(text.matchAll(WIKI_LINK_REGEX));

        if (matches.length === 0) return;

        // Process matches in reverse to maintain positions
        for (let i = matches.length - 1; i >= 0; i--) {
          const match = matches[i];
          const noteTitle = match[1];
          const matchStart = match.index!;
          const matchEnd = matchStart + match[0].length;

          // Find matching note by title (supports partial matches)
          const matchingNote = findMatchingNote(notes, noteTitle);

          // Split the text node and insert wiki link
          if (matchStart === 0 && matchEnd === text.length) {
            // Replace entire node
            const wikiLink = $createWikiLinkNode(
              noteTitle,
              matchingNote?.id || null
            );
            node.replace(wikiLink);
          } else if (matchStart === 0) {
            // Split at end
            const [, after] = node.splitText(matchEnd);
            const wikiLink = $createWikiLinkNode(
              noteTitle,
              matchingNote?.id || null
            );
            node.replace(wikiLink);
            wikiLink.insertAfter(after);
          } else if (matchEnd === text.length) {
            // Split at start
            const [before] = node.splitText(matchStart);
            const wikiLink = $createWikiLinkNode(
              noteTitle,
              matchingNote?.id || null
            );
            before.insertAfter(wikiLink);
          } else {
            // Split at both ends
            const [before, , after] = node.splitText(matchStart, matchEnd);
            const wikiLink = $createWikiLinkNode(
              noteTitle,
              matchingNote?.id || null
            );
            before.insertAfter(wikiLink);
            wikiLink.insertAfter(after);
          }
        }
      });
    });
  }, [editor, notes]);

  // Detect [[ trigger for autocomplete
  useEffect(() => {
    return editor.registerTextContentListener((textContent) => {
      editor.getEditorState().read(() => {
        const selection = $getSelection();
        if (!$isRangeSelection(selection)) {
          setShowAutocomplete(false);
          return;
        }

        const anchor = selection.anchor;
        const anchorNode = anchor.getNode();

        if (!$isTextNode(anchorNode)) {
          setShowAutocomplete(false);
          return;
        }

        const text = anchorNode.getTextContent();
        const offset = anchor.offset;

        // Look for [[ before cursor
        const beforeCursor = text.slice(0, offset);
        const lastDoubleBracket = beforeCursor.lastIndexOf('[[');

        if (lastDoubleBracket !== -1) {
          const afterBrackets = beforeCursor.slice(lastDoubleBracket + 2);

          // Check if there's no closing ]] yet
          if (!afterBrackets.includes(']]')) {
            setAutocompleteQuery(afterBrackets);
            setShowAutocomplete(true);

            // Calculate cursor position for autocomplete
            try {
              const domSelection = window.getSelection();
              if (domSelection && domSelection.rangeCount > 0) {
                const range = domSelection.getRangeAt(0);
                const rect = range.getBoundingClientRect();

                // Position autocomplete below and to the left of cursor
                // Add some offset to avoid overlapping with text
                setAutocompletePosition({
                  top: rect.bottom + window.scrollY + 5,
                  left: rect.left + window.scrollX
                });
              } else {
                // Fallback to center of screen if we can't get cursor position
                setAutocompletePosition({ top: 200, left: 200 });
              }
            } catch (error) {
              console.error('Error calculating autocomplete position:', error);
              setAutocompletePosition({ top: 200, left: 200 });
            }
            return;
          }
        }

        setShowAutocomplete(false);
      });
    });
  }, [editor]);

  // Listen for space or closing ]] to trigger conversion
  useEffect(() => {
    return editor.registerUpdateListener(({ editorState }) => {
      editorState.read(() => {
        const selection = $getSelection();
        if (!$isRangeSelection(selection)) return;

        const anchor = selection.anchor;
        const node = anchor.getNode();

        if (!$isTextNode(node)) return;

        const text = node.getTextContent();

        // Check if we just closed a wiki link with ]]
        if (text.includes(']]')) {
          convertWikiLinks();
        }
      });
    });
  }, [editor, convertWikiLinks]);

  const filteredNotes = notes.filter((note) =>
    note.title.toLowerCase().includes(autocompleteQuery.toLowerCase())
  ).slice(0, 5);

  const handleSelectNote = (noteTitle: string) => {
    editor.update(() => {
      const selection = $getSelection();
      if (!$isRangeSelection(selection)) return;

      const anchor = selection.anchor;
      const node = anchor.getNode();

      if (!$isTextNode(node)) return;

      const text = node.getTextContent();
      const offset = anchor.offset;
      const beforeCursor = text.slice(0, offset);
      const lastDoubleBracket = beforeCursor.lastIndexOf('[[');

      if (lastDoubleBracket !== -1) {
        // Replace from [[ to cursor with [[Title]]
        const before = text.slice(0, lastDoubleBracket);
        const after = text.slice(offset);

        const newText = `${before}[[${noteTitle}]]${after}`;
        node.setTextContent(newText);

        // Move cursor after ]]
        const newOffset = lastDoubleBracket + noteTitle.length + 4;
        selection.anchor.set(node.getKey(), newOffset, 'text');
        selection.focus.set(node.getKey(), newOffset, 'text');
      }
    });

    setShowAutocomplete(false);

    // Trigger conversion after a brief delay
    setTimeout(() => convertWikiLinks(), 10);
  };

  if (!showAutocomplete || filteredNotes.length === 0) {
    return null;
  }

  return (
    <div
      className="fixed z-50 bg-white border border-gray-200 rounded-lg shadow-lg py-1 w-64"
      style={{ top: autocompletePosition.top, left: autocompletePosition.left }}
    >
      <div className="px-3 py-1 text-xs font-medium text-gray-500 border-b border-gray-100">
        Link to note
      </div>
      {filteredNotes.map((note) => (
        <button
          key={note.id}
          onClick={() => handleSelectNote(note.title)}
          className="w-full text-left px-3 py-2 hover:bg-blue-50 transition-colors"
        >
          <div className="font-medium text-sm text-gray-900">{note.title}</div>
          {note.content && (
            <div className="text-xs text-gray-500 truncate">
              {note.content.slice(0, 60)}...
            </div>
          )}
        </button>
      ))}
    </div>
  );
}
