/**
 * Plugin to handle image paste events in Lexical editor
 */
import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';
import { useEffect } from 'react';
import { COMMAND_PRIORITY_LOW, PASTE_COMMAND } from 'lexical';
import { $getSelection, $isRangeSelection } from 'lexical';
import { $createImageNode } from './ImageNode';

export function ImagePlugin(): null {
  const [editor] = useLexicalComposerContext();

  useEffect(() => {
    return editor.registerCommand(
      PASTE_COMMAND,
      (event: ClipboardEvent) => {
        const clipboardData = event.clipboardData;

        if (!clipboardData) {
          return false;
        }

        // Check if clipboard contains files
        const files = clipboardData.files;

        if (files.length > 0) {
          // Check if any file is an image
          const imageFiles = Array.from(files).filter(file =>
            file.type.startsWith('image/')
          );

          if (imageFiles.length > 0) {
            event.preventDefault();

            // Process each image
            imageFiles.forEach((file) => {
              const reader = new FileReader();

              reader.onload = (e) => {
                const base64String = e.target?.result as string;

                editor.update(() => {
                  const selection = $getSelection();

                  if ($isRangeSelection(selection)) {
                    const imageNode = $createImageNode({
                      src: base64String,
                      altText: file.name || 'Pasted image',
                    });
                    selection.insertNodes([imageNode]);
                  }
                });
              };

              reader.readAsDataURL(file);
            });

            return true;
          }
        }

        // Also check for image URLs in clipboard
        const htmlData = clipboardData.getData('text/html');
        if (htmlData) {
          const parser = new DOMParser();
          const doc = parser.parseFromString(htmlData, 'text/html');
          const images = doc.querySelectorAll('img');

          if (images.length > 0) {
            event.preventDefault();

            images.forEach((img) => {
              const src = img.src;
              const alt = img.alt || 'Pasted image';

              editor.update(() => {
                const selection = $getSelection();

                if ($isRangeSelection(selection)) {
                  const imageNode = $createImageNode({
                    src,
                    altText: alt,
                  });
                  selection.insertNodes([imageNode]);
                }
              });
            });

            return true;
          }
        }

        return false;
      },
      COMMAND_PRIORITY_LOW
    );
  }, [editor]);

  return null;
}
