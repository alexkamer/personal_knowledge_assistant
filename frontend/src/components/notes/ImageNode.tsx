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
} from 'lexical';

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

function ImageComponent({ src, altText }: { src: string; altText: string }): JSX.Element {
  return (
    <img
      src={src}
      alt={altText}
      style={{
        maxWidth: '100%',
        height: 'auto',
        display: 'block',
        margin: '1rem 0',
        borderRadius: '0.375rem',
      }}
    />
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
    return <ImageComponent src={this.__src} altText={this.__altText} />;
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
