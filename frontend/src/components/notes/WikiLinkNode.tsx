/**
 * WikiLinkNode - Custom Lexical node for [[Note Title]] style links
 * Renders as clickable links that navigate to other notes
 */
import {
  DecoratorNode,
  LexicalNode,
  NodeKey,
  SerializedLexicalNode,
  Spread,
} from 'lexical';

export type SerializedWikiLinkNode = Spread<
  {
    noteTitle: string;
    noteId: string | null;
  },
  SerializedLexicalNode
>;

export class WikiLinkNode extends DecoratorNode<JSX.Element> {
  __noteTitle: string;
  __noteId: string | null;

  static getType(): string {
    return 'wikilink';
  }

  static clone(node: WikiLinkNode): WikiLinkNode {
    return new WikiLinkNode(node.__noteTitle, node.__noteId, node.__key);
  }

  constructor(noteTitle: string, noteId: string | null = null, key?: NodeKey) {
    super(key);
    this.__noteTitle = noteTitle;
    this.__noteId = noteId;
  }

  createDOM(): HTMLElement {
    const span = document.createElement('span');
    span.className = 'wiki-link-wrapper';
    return span;
  }

  updateDOM(): false {
    return false;
  }

  static importJSON(serializedNode: SerializedWikiLinkNode): WikiLinkNode {
    const node = $createWikiLinkNode(
      serializedNode.noteTitle,
      serializedNode.noteId
    );
    return node;
  }

  exportJSON(): SerializedWikiLinkNode {
    return {
      noteTitle: this.__noteTitle,
      noteId: this.__noteId,
      type: 'wikilink',
      version: 1,
    };
  }

  getNoteTitle(): string {
    return this.__noteTitle;
  }

  getNoteId(): string | null {
    return this.__noteId;
  }

  setNoteId(noteId: string | null): void {
    const writable = this.getWritable();
    writable.__noteId = noteId;
  }

  decorate(): JSX.Element {
    return (
      <WikiLinkComponent
        noteTitle={this.__noteTitle}
        noteId={this.__noteId}
        nodeKey={this.__key}
      />
    );
  }

  getTextContent(): string {
    return `[[${this.__noteTitle}]]`;
  }
}

export function $createWikiLinkNode(
  noteTitle: string,
  noteId: string | null = null
): WikiLinkNode {
  return new WikiLinkNode(noteTitle, noteId);
}

export function $isWikiLinkNode(
  node: LexicalNode | null | undefined
): node is WikiLinkNode {
  return node instanceof WikiLinkNode;
}

interface WikiLinkComponentProps {
  noteTitle: string;
  noteId: string | null;
  nodeKey: NodeKey;
}

function WikiLinkComponent({
  noteTitle,
  noteId,
}: WikiLinkComponentProps) {
  const handleClick = (e: React.MouseEvent) => {
    e.preventDefault();
    if (noteId) {
      // Dispatch custom event that the parent can listen to
      const event = new CustomEvent('navigate-to-note', {
        detail: { noteId, noteTitle },
        bubbles: true,
      });
      e.currentTarget.dispatchEvent(event);
    }
  };

  return (
    <span
      onClick={handleClick}
      className={`
        inline-flex items-center gap-1 px-1.5 py-0.5 rounded
        cursor-pointer transition-colors
        ${
          noteId
            ? 'bg-blue-50 text-blue-700 hover:bg-blue-100 border border-blue-200'
            : 'bg-stone-100 text-stone-600 hover:bg-stone-200 border border-stone-300 border-dashed'
        }
      `}
      title={noteId ? `Go to: ${noteTitle}` : `Note not found: ${noteTitle}`}
    >
      <span className="text-xs">[[</span>
      <span className="font-medium">{noteTitle}</span>
      <span className="text-xs">]]</span>
    </span>
  );
}
