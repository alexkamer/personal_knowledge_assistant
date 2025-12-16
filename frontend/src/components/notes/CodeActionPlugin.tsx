/**
 * Plugin to handle code block keyboard actions
 * Allows exiting code blocks with Cmd/Ctrl+Enter or by pressing Enter twice at the end
 */
import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';
import { useEffect } from 'react';
import {
  $getSelection,
  $isRangeSelection,
  $createParagraphNode,
  COMMAND_PRIORITY_LOW,
  KEY_ENTER_COMMAND,
} from 'lexical';
import { $isCodeNode } from '@lexical/code';

export function CodeActionPlugin(): null {
  const [editor] = useLexicalComposerContext();

  useEffect(() => {
    // Handle Cmd/Ctrl+Enter to exit code block
    return editor.registerCommand(
      KEY_ENTER_COMMAND,
      (event: KeyboardEvent | null) => {
        const selection = $getSelection();
        if (!$isRangeSelection(selection)) {
          return false;
        }

        const anchorNode = selection.anchor.getNode();
        const codeNode = anchorNode.getParent();

        // Check if we're in a code block
        if (!$isCodeNode(codeNode)) {
          return false;
        }

        // If Cmd/Ctrl+Enter, exit the code block
        if (event && (event.metaKey || event.ctrlKey)) {
          event.preventDefault();

          // Create a new paragraph after the code block
          const newParagraph = $createParagraphNode();
          codeNode.insertAfter(newParagraph);
          newParagraph.select();

          return true;
        }

        return false;
      },
      COMMAND_PRIORITY_LOW
    );
  }, [editor]);

  return null;
}
