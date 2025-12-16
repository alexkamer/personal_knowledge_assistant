/**
 * Plugin to handle image resize via custom events
 */
import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';
import { useEffect } from 'react';
import { $getNodeByKey } from 'lexical';
import { $isImageNode } from './ImageNode';

export function ImageResizePlugin(): null {
  const [editor] = useLexicalComposerContext();

  useEffect(() => {
    const handleResize = (event: Event) => {
      const customEvent = event as CustomEvent<{ nodeKey: string; width: number; height: number }>;
      const { nodeKey, width, height } = customEvent.detail;

      editor.update(() => {
        const node = $getNodeByKey(nodeKey);
        if ($isImageNode(node)) {
          node.setWidthAndHeight(width, height);
        }
      });
    };

    window.addEventListener('lexical-resize-image', handleResize);

    return () => {
      window.removeEventListener('lexical-resize-image', handleResize);
    };
  }, [editor]);

  return null;
}
