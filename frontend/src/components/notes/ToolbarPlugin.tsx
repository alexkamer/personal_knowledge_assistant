/**
 * Floating formatting toolbar for Lexical editor
 * Appears above selected text with formatting options
 */
import { useCallback, useEffect, useRef, useState } from 'react';
import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';
import {
  $getSelection,
  $isRangeSelection,
  FORMAT_TEXT_COMMAND,
  SELECTION_CHANGE_COMMAND,
  COMMAND_PRIORITY_LOW,
} from 'lexical';
import { $isLinkNode, TOGGLE_LINK_COMMAND } from '@lexical/link';
import {
  Bold,
  Italic,
  Underline,
  Code,
  Link as LinkIcon,
  Strikethrough,
} from 'lucide-react';

export function ToolbarPlugin() {
  const [editor] = useLexicalComposerContext();
  const toolbarRef = useRef<HTMLDivElement>(null);
  const [isVisible, setIsVisible] = useState(false);
  const [isBold, setIsBold] = useState(false);
  const [isItalic, setIsItalic] = useState(false);
  const [isUnderline, setIsUnderline] = useState(false);
  const [isStrikethrough, setIsStrikethrough] = useState(false);
  const [isCode, setIsCode] = useState(false);
  const [isLink, setIsLink] = useState(false);

  const updateToolbar = useCallback(() => {
    const selection = $getSelection();

    if ($isRangeSelection(selection)) {
      // Show toolbar only if text is selected
      const hasSelection = !selection.isCollapsed();
      setIsVisible(hasSelection);

      if (hasSelection) {
        // Update button states based on current format
        setIsBold(selection.hasFormat('bold'));
        setIsItalic(selection.hasFormat('italic'));
        setIsUnderline(selection.hasFormat('underline'));
        setIsStrikethrough(selection.hasFormat('strikethrough'));
        setIsCode(selection.hasFormat('code'));

        // Check if selection is within a link
        const node = selection.anchor.getNode();
        const parent = node.getParent();
        setIsLink($isLinkNode(parent) || $isLinkNode(node));
      }
    } else {
      setIsVisible(false);
    }
  }, []);

  const positionToolbar = useCallback(() => {
    const selection = window.getSelection();
    const toolbarElement = toolbarRef.current;

    if (
      !selection ||
      !toolbarElement ||
      selection.rangeCount === 0 ||
      selection.isCollapsed
    ) {
      return;
    }

    const range = selection.getRangeAt(0);
    const rect = range.getBoundingClientRect();

    // Position toolbar above the selection
    const top = rect.top - toolbarElement.offsetHeight - 8;
    const left = rect.left + rect.width / 2 - toolbarElement.offsetWidth / 2;

    toolbarElement.style.top = `${top + window.scrollY}px`;
    toolbarElement.style.left = `${Math.max(8, left + window.scrollX)}px`;
  }, []);

  useEffect(() => {
    return editor.registerUpdateListener(({ editorState }) => {
      editorState.read(() => {
        updateToolbar();
        if (isVisible) {
          // Delay positioning slightly to ensure DOM is updated
          setTimeout(positionToolbar, 0);
        }
      });
    });
  }, [editor, updateToolbar, positionToolbar, isVisible]);

  useEffect(() => {
    return editor.registerCommand(
      SELECTION_CHANGE_COMMAND,
      () => {
        updateToolbar();
        if (isVisible) {
          setTimeout(positionToolbar, 0);
        }
        return false;
      },
      COMMAND_PRIORITY_LOW
    );
  }, [editor, updateToolbar, positionToolbar, isVisible]);

  const formatText = (format: 'bold' | 'italic' | 'underline' | 'strikethrough' | 'code') => {
    editor.dispatchCommand(FORMAT_TEXT_COMMAND, format);
  };

  const insertLink = () => {
    if (!isLink) {
      const url = prompt('Enter URL:');
      if (url) {
        editor.dispatchCommand(TOGGLE_LINK_COMMAND, url);
      }
    } else {
      // Remove link
      editor.dispatchCommand(TOGGLE_LINK_COMMAND, null);
    }
  };

  if (!isVisible) {
    return null;
  }

  return (
    <div
      ref={toolbarRef}
      className="fixed z-50 bg-stone-900 text-white rounded-lg shadow-xl p-1 flex gap-1 items-center"
    >
      <ToolbarButton
        onClick={() => formatText('bold')}
        active={isBold}
        title="Bold (Cmd+B)"
        icon={<Bold size={18} />}
      />
      <ToolbarButton
        onClick={() => formatText('italic')}
        active={isItalic}
        title="Italic (Cmd+I)"
        icon={<Italic size={18} />}
      />
      <ToolbarButton
        onClick={() => formatText('underline')}
        active={isUnderline}
        title="Underline (Cmd+U)"
        icon={<Underline size={18} />}
      />
      <ToolbarButton
        onClick={() => formatText('strikethrough')}
        active={isStrikethrough}
        title="Strikethrough (Cmd+Shift+X)"
        icon={<Strikethrough size={18} />}
      />
      <div className="w-px h-6 bg-stone-700 mx-1" />
      <ToolbarButton
        onClick={() => formatText('code')}
        active={isCode}
        title="Inline Code (Cmd+E)"
        icon={<Code size={18} />}
      />
      <ToolbarButton
        onClick={insertLink}
        active={isLink}
        title="Link (Cmd+K)"
        icon={<LinkIcon size={18} />}
      />
    </div>
  );
}

interface ToolbarButtonProps {
  onClick: () => void;
  active: boolean;
  title: string;
  icon: React.ReactNode;
}

function ToolbarButton({ onClick, active, title, icon }: ToolbarButtonProps) {
  return (
    <button
      onClick={onClick}
      title={title}
      className={`
        p-2 rounded hover:bg-stone-800 transition-colors
        ${active ? 'bg-blue-600 text-white' : 'text-stone-300'}
      `}
    >
      {icon}
    </button>
  );
}
