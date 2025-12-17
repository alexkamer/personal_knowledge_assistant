/**
 * Outliner-based note editor inspired by RemNote
 * - Block-based editing with bullets
 * - Always inline-editable
 * - Enter to create new block, Tab to indent, Shift+Tab to outdent
 * - Slash commands for formatting
 * - Text selection formatting toolbar
 */
import { useState, useRef, useEffect } from 'react';
import { SlashCommandMenu } from './SlashCommandMenu';
import { FormattingToolbar } from './FormattingToolbar';

interface Block {
  id: string;
  content: string;
  indent: number;
}

interface OutlinerEditorProps {
  initialBlocks?: Block[];
  onChange: (blocks: Block[]) => void;
  placeholder?: string;
}

export function OutlinerEditor({ initialBlocks = [], onChange, placeholder }: OutlinerEditorProps) {
  const [blocks, setBlocks] = useState<Block[]>(
    initialBlocks.length > 0 ? initialBlocks : [{ id: generateId(), content: '', indent: 0 }]
  );
  const [_focusedBlockId, setFocusedBlockId] = useState<string | null>(null);
  const inputRefs = useRef<{ [key: string]: HTMLTextAreaElement }>({});

  // Slash command menu state
  const [slashMenuPosition, setSlashMenuPosition] = useState<{ top: number; left: number } | null>(null);
  const [slashMenuBlockId, setSlashMenuBlockId] = useState<string | null>(null);

  // Formatting toolbar state
  const [toolbarPosition, setToolbarPosition] = useState<{ top: number; left: number } | null>(null);
  const [selectedText, setSelectedText] = useState<{ blockId: string; start: number; end: number } | null>(null);

  useEffect(() => {
    onChange(blocks);
  }, [blocks]);

  function generateId() {
    return `block_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  // Apply formatting to selected text or current word
  const applyFormatting = (format: string, value?: string) => {
    if (!selectedText) return;

    const blockIndex = blocks.findIndex((b) => b.id === selectedText.blockId);
    if (blockIndex === -1) return;

    const block = blocks[blockIndex];
    const before = block.content.substring(0, selectedText.start);
    const text = block.content.substring(selectedText.start, selectedText.end);
    const after = block.content.substring(selectedText.end);

    let formattedText = text;

    switch (format) {
      case 'bold':
        formattedText = `**${text}**`;
        break;
      case 'italic':
        formattedText = `*${text}*`;
        break;
      case 'underline':
        formattedText = `__${text}__`;
        break;
      case 'color':
        if (value) {
          formattedText = `<span style="color: ${value}">${text}</span>`;
        }
        break;
      case 'highlight':
        if (value) {
          formattedText = `<span style="background-color: ${value}">${text}</span>`;
        }
        break;
    }

    const newContent = before + formattedText + after;
    const newBlocks = [...blocks];
    newBlocks[blockIndex] = { ...block, content: newContent };
    setBlocks(newBlocks);

    // Clear selection and toolbar
    setSelectedText(null);
    setToolbarPosition(null);
  };

  // Handle slash command selection
  const handleSlashCommand = (command: any) => {
    if (!slashMenuBlockId) return;

    const blockIndex = blocks.findIndex((b) => b.id === slashMenuBlockId);
    if (blockIndex === -1) return;

    const block = blocks[blockIndex];
    const element = inputRefs.current[slashMenuBlockId];
    if (!element) return;

    // Remove the "/" from the content
    let newContent = block.content.replace(/\/$/, '');

    // Apply command formatting
    switch (command.id) {
      case 'bold':
        newContent = newContent + ''; // User will type, we'll wrap later
        break;
      case 'italic':
        newContent = newContent + '';
        break;
      case 'underline':
        newContent = newContent + '';
        break;
      case 'heading1':
      case 'heading2':
      case 'heading3':
        // For headings, just set the content as-is, user will type
        break;
      default:
        break;
    }

    const newBlocks = [...blocks];
    newBlocks[blockIndex] = { ...block, content: newContent };
    setBlocks(newBlocks);

    // Close slash menu
    setSlashMenuPosition(null);
    setSlashMenuBlockId(null);

    // Keep element focused for continued typing
    setTimeout(() => {
      if (element) {
        element.focus();
        // Move cursor to end
        const _range = document.createRange();
        const sel = window.getSelection();
        _range.selectNodeContents(element);
        _range.collapse(false);
        sel?.removeAllRanges();
        sel?.addRange(_range);
      }
    }, 50);
  };

  const handleKeyDown = (e: any, blockId: string, blockIndex: number) => {
    const block = blocks[blockIndex];
    const element = e.currentTarget;

    // Handle keyboard shortcuts for formatting
    if ((e.metaKey || e.ctrlKey) && !e.shiftKey) {
      if (e.key === 'b' || e.key === 'i' || e.key === 'u') {
        e.preventDefault();
        const selection = window.getSelection();
        if (selection && selection.toString().length > 0) {
          // Get selection range - we only need start/end for setSelectedText
          const start = 0; // We'll work with the full selection
          const end = selection.toString().length;
          setSelectedText({ blockId, start, end });
          if (e.key === 'b') applyFormatting('bold');
          else if (e.key === 'i') applyFormatting('italic');
          else if (e.key === 'u') applyFormatting('underline');
        }
        return;
      }
    }

    // Detect "/" for slash command menu
    if (e.key === '/') {
      setTimeout(() => {
        const _rect = element.getBoundingClientRect();
        setSlashMenuPosition({
          top: _rect.top + window.scrollY,
          left: _rect.left + window.scrollX,
        });
        setSlashMenuBlockId(blockId);
      }, 0);
    } else if (slashMenuPosition) {
      // Close slash menu on any other key (except navigation keys)
      if (e.key !== 'ArrowDown' && e.key !== 'ArrowUp' && e.key !== 'Enter' && e.key !== 'Escape') {
        setSlashMenuPosition(null);
        setSlashMenuBlockId(null);
      }
    }

    if (e.key === 'Enter' && !e.shiftKey) {
      // If slash menu is open, let the menu handle it
      if (slashMenuPosition) {
        e.preventDefault();
        return;
      }
      e.preventDefault();
      // Create new block below
      const newBlock: Block = {
        id: generateId(),
        content: '',
        indent: block.indent,
      };
      const newBlocks = [...blocks];
      newBlocks.splice(blockIndex + 1, 0, newBlock);
      setBlocks(newBlocks);
      setTimeout(() => {
        const nextElement = inputRefs.current[newBlock.id];
        if (nextElement) {
          nextElement.focus();
        }
      }, 0);
    } else if (e.key === 'Tab') {
      e.preventDefault();
      if (e.shiftKey) {
        // Outdent (Shift+Tab)
        if (block.indent > 0) {
          const newBlocks = [...blocks];
          newBlocks[blockIndex] = { ...block, indent: block.indent - 1 };
          setBlocks(newBlocks);
        }
      } else {
        // Indent (Tab)
        const newBlocks = [...blocks];
        newBlocks[blockIndex] = { ...block, indent: block.indent + 1 };
        setBlocks(newBlocks);
      }
    } else if (e.key === 'Backspace' && block.content === '') {
      e.preventDefault();
      // Delete empty block
      if (blocks.length > 1) {
        const newBlocks = blocks.filter((_, i) => i !== blockIndex);
        setBlocks(newBlocks);
        // Focus previous block
        if (blockIndex > 0) {
          const prevBlock = blocks[blockIndex - 1];
          setTimeout(() => {
            const textarea = inputRefs.current[prevBlock.id];
            if (textarea) {
              textarea.focus();
              textarea.setSelectionRange(textarea.value.length, textarea.value.length);
            }
          }, 0);
        }
      }
    } else if (e.key === 'ArrowUp' && blockIndex > 0) {
      const textarea = e.currentTarget;
      const cursorPosition = textarea.selectionStart;
      if (cursorPosition === 0) {
        e.preventDefault();
        inputRefs.current[blocks[blockIndex - 1].id]?.focus();
      }
    } else if (e.key === 'ArrowDown' && blockIndex < blocks.length - 1) {
      const textarea = e.currentTarget;
      const cursorPosition = textarea.selectionStart;
      if (cursorPosition === textarea.value.length) {
        e.preventDefault();
        inputRefs.current[blocks[blockIndex + 1].id]?.focus();
      }
    }
  };

  const handleChange = (blockId: string, newContent: string) => {
    const newBlocks = blocks.map((block) =>
      block.id === blockId ? { ...block, content: newContent } : block
    );
    setBlocks(newBlocks);
  };

  // Handle text selection for formatting toolbar
  const handleMouseUp = (_e: React.MouseEvent<HTMLDivElement>, blockId: string) => {
    const selection = window.getSelection();
    if (!selection || selection.toString().length === 0) {
      setToolbarPosition(null);
      setSelectedText(null);
      return;
    }

    const selectionText = selection.toString();
    const start = 0;
    const end = selectionText.length;

    // Get selection position for toolbar
    const selectionRect = selection.getRangeAt(0).getBoundingClientRect();

    if (selectionRect) {
      setToolbarPosition({
        top: selectionRect.top + window.scrollY,
        left: selectionRect.left + window.scrollX + selectionRect.width / 2,
      });
      setSelectedText({ blockId, start, end });
    }
  };

  return (
    <div className="outliner-editor space-y-1 p-6 min-h-[400px] relative">
      {blocks.map((block, index) => (
        <div
          key={block.id}
          className="flex items-center group"
          style={{ paddingLeft: `${block.indent * 24}px` }}
        >
          {/* Bullet */}
          <div className="flex-shrink-0 w-6 flex items-center justify-center">
            <div className="w-1.5 h-1.5 rounded-full bg-stone-400 group-hover:bg-blue-500 transition-colors" />
          </div>

          {/* ContentEditable with formatted preview */}
          <div
            ref={(el) => {
              if (el) inputRefs.current[block.id] = el as any;
            }}
            contentEditable
            suppressContentEditableWarning
            onInput={(e) => {
              const text = e.currentTarget.textContent || '';
              handleChange(block.id, text);
            }}
            onKeyDown={(e) => handleKeyDown(e, block.id, index)}
            onMouseUp={(e) => handleMouseUp(e, block.id)}
            onFocus={() => setFocusedBlockId(block.id)}
            onBlur={() => {
              // Don't blur if slash menu is open
              if (!slashMenuPosition) {
                setFocusedBlockId(null);
              }
              setToolbarPosition(null);
              setSelectedText(null);
            }}
            data-placeholder={index === 0 && block.content === '' ? placeholder || 'Start typing...' : ''}
            className="flex-1 outline-none bg-transparent text-stone-900 py-1 px-2 -ml-2 rounded hover:bg-stone-50 focus:bg-blue-50 focus:ring-2 focus:ring-blue-200 transition-colors min-h-[28px] empty:before:content-[attr(data-placeholder)] empty:before:text-stone-400"
          >
            {block.content}
          </div>
        </div>
      ))}

      {/* Slash Command Menu */}
      {slashMenuPosition && (
        <SlashCommandMenu
          position={slashMenuPosition}
          onSelect={handleSlashCommand}
          onClose={() => {
            setSlashMenuPosition(null);
            setSlashMenuBlockId(null);
          }}
        />
      )}

      {/* Formatting Toolbar */}
      {toolbarPosition && (
        <FormattingToolbar
          position={toolbarPosition}
          onFormat={applyFormatting}
          onClose={() => {
            setToolbarPosition(null);
            setSelectedText(null);
          }}
        />
      )}
    </div>
  );
}
