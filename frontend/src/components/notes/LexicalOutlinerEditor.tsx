/**
 * Lexical-based outliner editor - RemNote-style WYSIWYG
 * True rich text editing with no raw markdown visible
 */
import { useEffect, useRef } from 'react';
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
import { CodeNode, CodeHighlightNode } from '@lexical/code';
import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';
import { $setBlocksType } from '@lexical/selection';
import { $getSelection, $isRangeSelection } from 'lexical';
import { LexicalSlashCommandPlugin } from './LexicalSlashCommandPlugin';
import { ImageNode } from './ImageNode';
import { ImagePlugin } from './ImagePlugin';
import { ImageResizePlugin } from './ImageResizePlugin';
import { CodeHighlightPlugin } from './CodeHighlightPlugin';

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
  code: 'bg-gray-900 text-gray-100 font-mono text-sm p-4 rounded-lg my-2 block overflow-x-auto',
  codeHighlight: {
    atrule: 'text-purple-400',
    attr: 'text-blue-400',
    boolean: 'text-purple-400',
    builtin: 'text-yellow-400',
    cdata: 'text-gray-400',
    char: 'text-green-400',
    class: 'text-yellow-400',
    'class-name': 'text-yellow-400',
    comment: 'text-gray-500',
    constant: 'text-purple-400',
    deleted: 'text-red-400',
    doctype: 'text-gray-400',
    entity: 'text-yellow-400',
    function: 'text-blue-400',
    important: 'text-red-400',
    inserted: 'text-green-400',
    keyword: 'text-purple-400',
    namespace: 'text-yellow-400',
    number: 'text-orange-400',
    operator: 'text-gray-300',
    prolog: 'text-gray-400',
    property: 'text-blue-400',
    punctuation: 'text-gray-400',
    regex: 'text-green-400',
    selector: 'text-green-400',
    string: 'text-green-400',
    symbol: 'text-purple-400',
    tag: 'text-red-400',
    url: 'text-blue-400',
    variable: 'text-blue-400',
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
      const jsonString = JSON.stringify(json);

      // Debug: log if there are images
      if (jsonString.includes('"type":"image"')) {
        console.log('Saving content with images, size:', jsonString.length);
      }

      onChange(jsonString);
    });
  };

  return <OnChangePlugin onChange={handleChange} />;
}

// Plugin to initialize content from JSON - runs once on mount
function InitialContentPlugin({ content }: { content?: string }) {
  const [editor] = useLexicalComposerContext();

  useEffect(() => {
    // Initialize content once when component mounts
    if (content) {
      // Debug: log if loading images
      if (content.includes('"type":"image"')) {
        console.log('Loading note with images, content size:', content.length);
      }

      try {
        const editorState = editor.parseEditorState(content);
        editor.setEditorState(editorState);
      } catch (error) {
        console.error('Error parsing editor state:', error);
        // If not valid JSON, treat as plain text
        editor.update(() => {
          const root = $getRoot();
          root.clear();
          const paragraph = $createParagraphNode();
          paragraph.append($createTextNode(content));
          root.append(paragraph);
        });
      }
    } else {
      // If no content, initialize with empty paragraph
      editor.update(() => {
        const root = $getRoot();
        root.clear();
        const paragraph = $createParagraphNode();
        root.append(paragraph);
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Only run once on mount

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
      CodeNode,
      CodeHighlightNode,
      ParagraphNode,
      TextNode,
      LineBreakNode,
      ImageNode,
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
          <CodeHighlightPlugin />
          <OnChangeSerializerPlugin onChange={onChange} />
          <InitialContentPlugin content={initialContent} />
          <LexicalSlashCommandPlugin />
          <ImagePlugin />
          <ImageResizePlugin />
        </div>
      </LexicalComposer>
    </div>
  );
}
