/**
 * Plugin to auto-convert text patterns to lists
 * - "- " converts to bullet list
 * - "1. " or "1) " converts to numbered list
 */
import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';
import { useEffect } from 'react';
import {
  $getSelection,
  $isRangeSelection,
  $isTextNode,
  COMMAND_PRIORITY_LOW,
  KEY_SPACE_COMMAND,
} from 'lexical';
import {
  INSERT_UNORDERED_LIST_COMMAND,
  INSERT_ORDERED_LIST_COMMAND,
} from '@lexical/list';

export function AutoListPlugin(): null {
  const [editor] = useLexicalComposerContext();

  useEffect(() => {
    return editor.registerCommand(
      KEY_SPACE_COMMAND,
      () => {
        const selection = $getSelection();
        if (!$isRangeSelection(selection)) return false;

        const anchorNode = selection.anchor.getNode();
        if (!$isTextNode(anchorNode)) return false;

        const textContent = anchorNode.getTextContent();
        const anchorOffset = selection.anchor.offset;

        // Check for "- " pattern (bullet list)
        if (textContent === '-' && anchorOffset === 1) {
          // Clear the "-" and convert to bullet list
          anchorNode.setTextContent('');

          // Dispatch after clearing text
          setTimeout(() => {
            editor.dispatchCommand(INSERT_UNORDERED_LIST_COMMAND, undefined);
          }, 0);

          return true; // Prevent default space behavior
        }

        // Check for "1. " or "1) " pattern (numbered list)
        const numberedPattern1 = /^(\d+)\.$/;
        const numberedPattern2 = /^(\d+)\)$/;

        if (
          (numberedPattern1.test(textContent) || numberedPattern2.test(textContent)) &&
          anchorOffset === textContent.length
        ) {
          // Clear the pattern and convert to numbered list
          anchorNode.setTextContent('');

          // Dispatch after clearing text
          setTimeout(() => {
            editor.dispatchCommand(INSERT_ORDERED_LIST_COMMAND, undefined);
          }, 0);

          return true; // Prevent default space behavior
        }

        return false; // Allow default space behavior
      },
      COMMAND_PRIORITY_LOW
    );
  }, [editor]);

  return null;
}
