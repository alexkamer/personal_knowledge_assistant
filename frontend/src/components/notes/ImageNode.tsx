/**
 * Lexical ImageNode for displaying images in the editor
 */
import React from 'react';
import {
  DecoratorNode,
  NodeKey,
  LexicalNode,
  SerializedLexicalNode,
  Spread,
  $getNodeByKey,
} from 'lexical';
import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';

export interface ImagePayload {
  altText: string;
  src: string;
  width?: number;
  height?: number;
  key?: NodeKey;
}

export type SerializedImageNode = Spread<
  {
    altText: string;
    src: string;
    width?: number;
    height?: number;
  },
  SerializedLexicalNode
>;

function ImageComponent({
  src,
  altText,
  width,
  height,
  nodeKey
}: {
  src: string;
  altText: string;
  width?: number;
  height?: number;
  nodeKey: NodeKey;
}): JSX.Element {
  const [editor] = useLexicalComposerContext();
  const [size, setSize] = React.useState({
    width: width || 400,
    height: height || 300,
  });
  const [isResizing, setIsResizing] = React.useState(false);
  const [startPos, setStartPos] = React.useState({ x: 0, y: 0 });
  const [startSize, setStartSize] = React.useState({ width: 400, height: 300 });
  const imgRef = React.useRef<HTMLImageElement>(null);

  React.useEffect(() => {
    // Set initial size based on actual image dimensions if not already set
    if (!width && !height && imgRef.current && imgRef.current.naturalWidth) {
      const maxWidth = 800;
      const naturalWidth = imgRef.current.naturalWidth;
      const naturalHeight = imgRef.current.naturalHeight;
      const ratio = naturalHeight / naturalWidth;

      if (naturalWidth > maxWidth) {
        setSize({ width: maxWidth, height: maxWidth * ratio });
      } else {
        setSize({ width: naturalWidth, height: naturalHeight });
      }
    }
  }, [src, width, height]);

  const handleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsResizing(true);
    setStartPos({ x: e.clientX, y: e.clientY });
    setStartSize({ width: size.width, height: size.height });
  };

  React.useEffect(() => {
    if (!isResizing) return;

    let currentSize = size;

    const handleMouseMove = (e: MouseEvent) => {
      const deltaX = e.clientX - startPos.x;
      const newWidth = Math.max(100, Math.min(800, startSize.width + deltaX));
      const ratio = startSize.height / startSize.width;
      const newSize = { width: newWidth, height: newWidth * ratio };
      currentSize = newSize;
      setSize(newSize);
    };

    const handleMouseUp = () => {
      setIsResizing(false);
      // Update the node with the new size
      editor.update(() => {
        const node = $getNodeByKey(nodeKey);
        if ($isImageNode(node)) {
          node.setWidthAndHeight(currentSize.width, currentSize.height);
        }
      });
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isResizing, startPos, startSize, editor, nodeKey]);

  return (
    <div
      style={{
        position: 'relative',
        display: 'inline-block',
        margin: '1rem 0',
        cursor: isResizing ? 'ew-resize' : 'default',
      }}
    >
      <img
        ref={imgRef}
        src={src}
        alt={altText}
        style={{
          width: `${size.width}px`,
          height: `${size.height}px`,
          display: 'block',
          borderRadius: '0.375rem',
          userSelect: 'none',
        }}
        draggable={false}
      />
      <div
        onMouseDown={handleMouseDown}
        style={{
          position: 'absolute',
          right: '-4px',
          top: '0',
          bottom: '0',
          width: '8px',
          cursor: 'ew-resize',
          backgroundColor: isResizing ? 'rgba(59, 130, 246, 0.5)' : 'transparent',
          borderRadius: '0.25rem',
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.backgroundColor = 'rgba(59, 130, 246, 0.3)';
        }}
        onMouseLeave={(e) => {
          if (!isResizing) {
            e.currentTarget.style.backgroundColor = 'transparent';
          }
        }}
      />
    </div>
  );
}

export class ImageNode extends DecoratorNode<JSX.Element> {
  __src: string;
  __altText: string;
  __width?: number;
  __height?: number;

  static getType(): string {
    return 'image';
  }

  static clone(node: ImageNode): ImageNode {
    return new ImageNode(
      node.__src,
      node.__altText,
      node.__width,
      node.__height,
      node.__key
    );
  }

  constructor(
    src: string,
    altText: string,
    width?: number,
    height?: number,
    key?: NodeKey
  ) {
    super(key);
    this.__src = src;
    this.__altText = altText;
    this.__width = width;
    this.__height = height;
  }

  static importJSON(serializedNode: SerializedImageNode): ImageNode {
    const { altText, src, width, height } = serializedNode;
    return $createImageNode({
      altText,
      src,
      width,
      height,
    });
  }

  exportJSON(): SerializedImageNode {
    return {
      altText: this.getAltText(),
      src: this.getSrc(),
      width: this.__width,
      height: this.__height,
      type: 'image',
      version: 1,
    };
  }

  getSrc(): string {
    return this.__src;
  }

  getAltText(): string {
    return this.__altText;
  }

  setWidthAndHeight(width: number, height: number): void {
    const writable = this.getWritable();
    writable.__width = width;
    writable.__height = height;
  }

  createDOM(): HTMLElement {
    const span = document.createElement('span');
    span.style.display = 'inline-block';
    return span;
  }

  updateDOM(): false {
    return false;
  }

  decorate(): JSX.Element {
    return (
      <ImageComponent
        src={this.__src}
        altText={this.__altText}
        width={this.__width}
        height={this.__height}
        nodeKey={this.__key}
      />
    );
  }
}

export function $createImageNode({
  altText,
  src,
  width,
  height,
  key,
}: ImagePayload): ImageNode {
  return new ImageNode(src, altText, width, height, key);
}

export function $isImageNode(
  node: LexicalNode | null | undefined
): node is ImageNode {
  return node instanceof ImageNode;
}
