/**
 * Lexical-based outliner editor - RemNote-style WYSIWYG
 * True rich text editing with no raw markdown visible
 */
import { useEffect } from 'react';
import { LexicalComposer } from '@lexical/react/LexicalComposer';
import { RichTextPlugin } from '@lexical/react/LexicalRichTextPlugin';
import { ContentEditable } from '@lexical/react/LexicalContentEditable';
import { HistoryPlugin } from '@lexical/react/LexicalHistoryPlugin';
import { OnChangePlugin } from '@lexical/react/LexicalOnChangePlugin';
import { LexicalErrorBoundary } from '@lexical/react/LexicalErrorBoundary';
import {
  $getRoot,
  $createParagraphNode,
  $createTextNode,
  EditorState,
  LexicalEditor,
  ParagraphNode,
  TextNode,
  LineBreakNode,
  FORMAT_TEXT_COMMAND,
  COMMAND_PRIORITY_LOW,
} from 'lexical';
import { HeadingNode, QuoteNode, $createHeadingNode } from '@lexical/rich-text';
import { ListNode, ListItemNode } from '@lexical/list';
import { ListPlugin } from '@lexical/react/LexicalListPlugin';
import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';
import { $setBlocksType } from '@lexical/selection';
import { $getSelection, $isRangeSelection } from 'lexical';
import { LexicalSlashCommandPlugin } from './LexicalSlashCommandPlugin';

interface LexicalOutlinerEditorProps {
  initialContent?: string;
  onChange: (content: string) => void;
  placeholder?: string;
}

// Theme configuration for styling
const theme = {
  paragraph: 'mb-1',
  text: {
    bold: 'font-bold',
    italic: 'italic',
    underline: 'underline',
  },
  heading: {
    h1: 'text-3xl font-bold text-gray-900 mb-2',
    h2: 'text-2xl font-semibold text-gray-800 mb-2',
    h3: 'text-xl font-medium text-gray-700 mb-1',
  },
  list: {
    ul: 'list-none',
    listitem: 'ml-6 relative',
  },
};

// Plugin to handle keyboard shortcuts
function KeyboardShortcutsPlugin() {
  const [editor] = useLexicalComposerContext();

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      const { key, ctrlKey, metaKey, shiftKey } = event;
      const isMod = ctrlKey || metaKey;

      if (isMod && !shiftKey) {
        if (key === 'b') {
          event.preventDefault();
          editor.dispatchCommand(FORMAT_TEXT_COMMAND, 'bold');
          return true;
        } else if (key === 'i') {
          event.preventDefault();
          editor.dispatchCommand(FORMAT_TEXT_COMMAND, 'italic');
          return true;
        } else if (key === 'u') {
          event.preventDefault();
          editor.dispatchCommand(FORMAT_TEXT_COMMAND, 'underline');
          return true;
        }
      }

      return false;
    };

    return editor.registerRootListener((rootElement, prevRootElement) => {
      if (prevRootElement) {
        prevRootElement.removeEventListener('keydown', handleKeyDown);
      }
      if (rootElement) {
        rootElement.addEventListener('keydown', handleKeyDown);
      }
    });
  }, [editor]);

  return null;
}

// Plugin to serialize editor state to JSON string
function OnChangeSerializerPlugin({ onChange }: { onChange: (content: string) => void }) {
  const [editor] = useLexicalComposerContext();

  const handleChange = (editorState: EditorState, editor: LexicalEditor) => {
    editorState.read(() => {
      const json = editorState.toJSON();
      onChange(JSON.stringify(json));
    });
  };

  return <OnChangePlugin onChange={handleChange} />;
}

// Plugin to initialize content from JSON
function InitialContentPlugin({ content }: { content?: string }) {
  const [editor] = useLexicalComposerContext();

  useEffect(() => {
    if (content) {
      try {
        const editorState = editor.parseEditorState(content);
        editor.setEditorState(editorState);
      } catch (error) {
        // If not valid JSON, treat as plain text
        editor.update(() => {
          const root = $getRoot();
          root.clear();
          const paragraph = $createParagraphNode();
          paragraph.append($createTextNode(content));
          root.append(paragraph);
        });
      }
    }
  }, []); // Only run on mount

  return null;
}


export function LexicalOutlinerEditor({
  initialContent,
  onChange,
  placeholder = 'Start typing...',
}: LexicalOutlinerEditorProps) {
  const initialConfig = {
    namespace: 'OutlinerEditor',
    theme,
    onError: (error: Error) => {
      console.error('Lexical error:', error);
    },
    nodes: [
      HeadingNode,
      QuoteNode,
      ListNode,
      ListItemNode,
      ParagraphNode,
      TextNode,
      LineBreakNode,
    ],
  };

  return (
    <div className="lexical-editor-container">
      <LexicalComposer initialConfig={initialConfig}>
        <div className="relative p-6 min-h-[400px]">
          <RichTextPlugin
            contentEditable={
              <ContentEditable
                className="outline-none min-h-[400px] focus:outline-none"
                aria-placeholder={placeholder}
                placeholder={
                  <div className="absolute top-6 left-6 text-gray-400 pointer-events-none">
                    {placeholder}
                  </div>
                }
              />
            }
            ErrorBoundary={LexicalErrorBoundary}
          />
          <HistoryPlugin />
          <ListPlugin />
          <KeyboardShortcutsPlugin />
          <OnChangeSerializerPlugin onChange={onChange} />
          <InitialContentPlugin content={initialContent} />
          <LexicalSlashCommandPlugin />
        </div>
      </LexicalComposer>
    </div>
  );
}
