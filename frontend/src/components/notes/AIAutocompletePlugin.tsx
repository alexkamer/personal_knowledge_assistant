/**
 * AI-powered autocomplete plugin for Lexical editor.
 * Shows inline ghost text suggestions that can be accepted with Tab key.
 */
import { useEffect, useState, useRef } from 'react';
import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';
import {
  $getSelection,
  $isRangeSelection,
  $isTextNode,
  $createTextNode,
  TextNode,
} from 'lexical';
import { autocompleteService } from '../../services/autocompleteService';

export function AIAutocompletePlugin() {
  const [editor] = useLexicalComposerContext();
  const [suggestion, setSuggestion] = useState<string>('');
  const [ghostTextStyle, setGhostTextStyle] = useState<{ top: number; left: number; fontSize: string; lineHeight: string } | null>(null);
  const debounceRef = useRef<NodeJS.Timeout>();
  const abortControllerRef = useRef<AbortController>();
  const lastCompletedTextRef = useRef<string>(''); // Track last text we completed for

  // Listen to editor changes and trigger autocomplete
  useEffect(() => {
    return editor.registerUpdateListener(({ editorState }) => {
      editorState.read(() => {
        const selection = $getSelection();

        // Only show suggestions when there's a valid range selection
        if (!$isRangeSelection(selection) || !selection.isCollapsed()) {
          setSuggestion('');
          return;
        }

        const anchorNode = selection.anchor.getNode();

        // Only trigger on text nodes
        if (!$isTextNode(anchorNode)) {
          setSuggestion('');
          return;
        }

        // Get the text content and cursor position
        const text = anchorNode.getTextContent();
        const offset = selection.anchor.offset;

        // Extract current line (text from last newline to cursor)
        const lineStart = text.lastIndexOf('\n', offset - 1) + 1;
        const currentLine = text.slice(lineStart, offset);

        // Clear any existing debounce timer
        if (debounceRef.current) {
          clearTimeout(debounceRef.current);
        }

        // Don't suggest for very short text
        if (currentLine.trim().length < 3) {
          setSuggestion('');
          return;
        }

        // Don't trigger immediately after sentence-ending punctuation without space
        const trimmedLine = currentLine.trimEnd();
        if (trimmedLine.length > 0 && '.!?'.includes(trimmedLine[trimmedLine.length - 1])) {
          setSuggestion('');
          return;
        }

        // Don't request if we already have a suggestion for this exact text
        if (currentLine === lastCompletedTextRef.current) {
          return;
        }

        // Extract more context: previous sentence or two for better suggestions
        const getContextBeforeLine = () => {
          // Get text before current line (up to 200 chars)
          const beforeLine = text.slice(Math.max(0, lineStart - 200), lineStart).trim();

          // Find the last 1-2 complete sentences
          const sentences = beforeLine.match(/[^.!?]+[.!?]+/g);
          if (sentences && sentences.length > 0) {
            // Return last 1-2 sentences as context
            return sentences.slice(-2).join(' ').trim();
          }

          return beforeLine;
        };

        const additionalContext = getContextBeforeLine();

        // Debounce API call (500ms)
        debounceRef.current = setTimeout(async () => {
          try {
            // Cancel any in-flight request
            if (abortControllerRef.current) {
              abortControllerRef.current.abort();
            }
            abortControllerRef.current = new AbortController();

            // Get completion from backend with context
            const completion = await autocompleteService.getCompletion(
              currentLine,
              additionalContext || undefined
            );

            if (completion && completion.trim()) {
              setSuggestion(completion);
              lastCompletedTextRef.current = currentLine; // Remember we completed for this text

              // Get cursor position and styling for ghost text
              const domSelection = window.getSelection();
              if (domSelection && domSelection.rangeCount > 0) {
                const range = domSelection.getRangeAt(0);

                // Create a temporary span at cursor position to get exact coordinates
                const tempSpan = document.createElement('span');
                tempSpan.textContent = '\u200B'; // Zero-width space
                range.insertNode(tempSpan);
                const rect = tempSpan.getBoundingClientRect();
                tempSpan.remove();

                // Get the computed style from the current text element
                const parentElement = range.startContainer.parentElement;
                const computedStyle = parentElement ? window.getComputedStyle(parentElement) : null;

                // Get the computed style from the current text element
                const fontSize = computedStyle?.fontSize || '16px';
                const lineHeight = computedStyle?.lineHeight || '1.5';

                const style = {
                  top: rect.top,
                  left: rect.left,
                  fontSize: fontSize,
                  lineHeight: lineHeight,
                };
                setGhostTextStyle(style);
              }
            } else {
              setSuggestion('');
              setGhostTextStyle(null);
            }
          } catch (error: any) {
            // Ignore abort errors
            if (error.name !== 'AbortError' && error.name !== 'CanceledError') {
              console.error('Autocomplete error:', error);
            }
            setSuggestion('');
          }
        }, 500);
      });
    });
  }, [editor]);

  // Handle keyboard interactions
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Accept suggestion with Tab
      if (suggestion && event.key === 'Tab') {
        event.preventDefault();
        event.stopPropagation();

        editor.update(() => {
          const selection = $getSelection();
          if (!$isRangeSelection(selection)) return;

          // Insert the suggestion as real text at cursor position
          selection.insertText(suggestion);
          setSuggestion('');
          setGhostTextStyle(null);
          lastCompletedTextRef.current = ''; // Reset after accepting
        });

        return true;
      }

      // Dismiss suggestion on Escape
      if (suggestion && event.key === 'Escape') {
        event.preventDefault();
        setSuggestion('');
        setGhostTextStyle(null);
        lastCompletedTextRef.current = ''; // Reset after dismissing
        return true;
      }

      // Dismiss on any typing key (except modifiers)
      if (
        suggestion &&
        event.key !== 'Shift' &&
        event.key !== 'Control' &&
        event.key !== 'Alt' &&
        event.key !== 'Meta' &&
        event.key !== 'CapsLock' &&
        event.key.length === 1 // Only dismiss on actual character keys
      ) {
        setSuggestion('');
        setGhostTextStyle(null);
        lastCompletedTextRef.current = ''; // Reset when typing continues
      }

      return false;
    };

    // Register at capture phase to intercept before other handlers
    return editor.registerRootListener((rootElement, prevRootElement) => {
      if (prevRootElement) {
        prevRootElement.removeEventListener('keydown', handleKeyDown, true);
      }
      if (rootElement) {
        rootElement.addEventListener('keydown', handleKeyDown, true);
      }
    });
  }, [editor, suggestion]);

  // Clean up on unmount
  useEffect(() => {
    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  // Render ghost text overlay
  if (!suggestion || !ghostTextStyle) {
    return null;
  }

  return (
    <span
      className="pointer-events-none text-gray-400"
      style={{
        position: 'fixed',
        top: ghostTextStyle.top,
        left: ghostTextStyle.left,
        fontSize: ghostTextStyle.fontSize,
        lineHeight: ghostTextStyle.lineHeight,
        fontFamily: 'inherit',
        opacity: 0.6,
        zIndex: 1000,
        whiteSpace: 'pre',
        transform: 'translateY(-8px)',
      }}
    >
      {suggestion}
    </span>
  );
}
