/**
 * Plugin to make links clickable with Cmd/Ctrl+Click
 */
import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';
import { useEffect } from 'react';
import { $isLinkNode } from '@lexical/link';

export function ClickableLinkPlugin(): null {
  const [editor] = useLexicalComposerContext();

  useEffect(() => {
    const handleClick = (event: MouseEvent) => {
      const target = event.target as HTMLElement;
      const linkElement = target.closest('a');

      if (linkElement) {
        // Cmd/Ctrl+Click to open link in new tab
        if (event.metaKey || event.ctrlKey) {
          event.preventDefault();
          const href = linkElement.getAttribute('href');
          if (href) {
            window.open(href, '_blank', 'noopener,noreferrer');
          }
        } else {
          // Prevent default link behavior so we can edit
          event.preventDefault();
        }
      }
    };

    return editor.registerRootListener((rootElement, prevRootElement) => {
      if (prevRootElement) {
        prevRootElement.removeEventListener('click', handleClick);
      }
      if (rootElement) {
        rootElement.addEventListener('click', handleClick);
      }
    });
  }, [editor]);

  return null;
}
