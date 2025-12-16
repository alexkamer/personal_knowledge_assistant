/**
 * Plugin to handle hyperlinks in the editor
 * Supports creating and editing links with Cmd+K shortcut
 */
import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';
import { useEffect, useState, useCallback, useRef } from 'react';
import {
  $getSelection,
  $isRangeSelection,
  $createTextNode,
  $setSelection,
  COMMAND_PRIORITY_LOW,
  KEY_MODIFIER_COMMAND,
  RangeSelection,
} from 'lexical';
import { $isLinkNode, TOGGLE_LINK_COMMAND, $createLinkNode, toggleLink } from '@lexical/link';
import { ExternalLink } from 'lucide-react';

export function LinkPlugin(): JSX.Element | null {
  const [editor] = useLexicalComposerContext();
  const [showLinkDialog, setShowLinkDialog] = useState(false);
  const [linkUrl, setLinkUrl] = useState('');
  const [linkText, setLinkText] = useState('');
  const [isEditingLink, setIsEditingLink] = useState(false);
  const [selectedText, setSelectedText] = useState('');
  const savedSelectionRef = useRef<RangeSelection | null>(null);

  useEffect(() => {
    // Register Cmd+K keyboard shortcut
    return editor.registerCommand(
      KEY_MODIFIER_COMMAND,
      (payload) => {
        const event: KeyboardEvent = payload;
        if (event.key === 'k') {
          event.preventDefault();

          editor.update(() => {
            const selection = $getSelection();
            if (!$isRangeSelection(selection)) return;

            // Save the selection by storing the text and whether we have a selection
            const text = selection.getTextContent();

            // If there's selected text, we'll need to restore it
            if (text) {
              savedSelectionRef.current = selection.clone();
              setSelectedText(text);
              setLinkText(text);
            } else {
              savedSelectionRef.current = null;
              setSelectedText('');
              setLinkText('');
            }

            // Check if we're editing an existing link
            const node = selection.anchor.getNode();
            const parent = node.getParent();

            if ($isLinkNode(parent)) {
              setLinkUrl(parent.getURL());
              setIsEditingLink(true);
            } else {
              setLinkUrl('');
              setIsEditingLink(false);
            }
          });

          setShowLinkDialog(true);
          return true;
        }
        return false;
      },
      COMMAND_PRIORITY_LOW
    );
  }, [editor]);

  const handleCreateLink = useCallback(() => {
    if (!linkUrl) return;

    editor.update(() => {
      if (savedSelectionRef.current && selectedText) {
        // Restore the saved selection directly using $setSelection
        $setSelection(savedSelectionRef.current);

        // Use toggleLink directly instead of dispatching command
        toggleLink(linkUrl);
      } else {
        // If no selection, insert link with provided text
        const selection = $getSelection();
        if (!$isRangeSelection(selection)) return;

        const linkNode = $createLinkNode(linkUrl);
        const textNode = $createTextNode(linkText || linkUrl);
        linkNode.append(textNode);
        selection.insertNodes([linkNode]);
      }
    });

    setShowLinkDialog(false);
    setLinkUrl('');
    setLinkText('');
    setSelectedText('');
    savedSelectionRef.current = null;
  }, [editor, linkUrl, linkText, selectedText]);

  const handleRemoveLink = useCallback(() => {
    editor.dispatchCommand(TOGGLE_LINK_COMMAND, null);
    setShowLinkDialog(false);
    setLinkUrl('');
    setLinkText('');
    setSelectedText('');
  }, [editor]);

  if (!showLinkDialog) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl p-6 w-[500px]">
        <div className="flex items-center gap-2 mb-4">
          <ExternalLink size={20} className="text-blue-600" />
          <h3 className="text-lg font-semibold">
            {isEditingLink ? 'Edit Link' : 'Insert Link'}
          </h3>
        </div>

        <div className="space-y-4">
          {!selectedText && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Link Text
              </label>
              <input
                type="text"
                value={linkText}
                onChange={(e) => setLinkText(e.target.value)}
                placeholder="Enter link text"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                autoFocus={!isEditingLink}
              />
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              URL
            </label>
            <input
              type="url"
              value={linkUrl}
              onChange={(e) => setLinkUrl(e.target.value)}
              placeholder="https://example.com"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              autoFocus={isEditingLink || !!selectedText}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  handleCreateLink();
                } else if (e.key === 'Escape') {
                  e.preventDefault();
                  setShowLinkDialog(false);
                  setLinkUrl('');
                  setLinkText('');
                  setSelectedText('');
                }
              }}
            />
          </div>

          <div className="flex gap-2 justify-end">
            {isEditingLink && (
              <button
                onClick={handleRemoveLink}
                className="px-4 py-2 text-red-600 hover:bg-red-50 rounded-md transition-colors"
              >
                Remove Link
              </button>
            )}
            <button
              onClick={() => {
                setShowLinkDialog(false);
                setLinkUrl('');
                setLinkText('');
                setSelectedText('');
              }}
              className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-md transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleCreateLink}
              disabled={!linkUrl}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed"
            >
              {isEditingLink ? 'Update' : 'Insert'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
