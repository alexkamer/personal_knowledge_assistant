/**
 * Markdown renderer component with syntax highlighting and copy functionality.
 */
import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Check, Copy } from 'lucide-react';
import type { SourceCitation } from '@/types/chat';
import 'katex/dist/katex.min.css';

interface MarkdownRendererProps {
  content: string;
  className?: string;
  sources?: SourceCitation[];
  onSourceClick?: (source: SourceCitation) => void;
}

// Helper to parse text and replace [N] or (Source N) with clickable citations
function parseCitations(text: string, sources?: SourceCitation[], onSourceClick?: (source: SourceCitation) => void): React.ReactNode {
  if (!sources || !onSourceClick) {
    return text;
  }

  // Match citation patterns: [1], [2], (Source 1), (Source 2), etc.
  const citationPattern = /\[(\d+)\]|\(Source\s+(\d+)\)/g;
  const parts: React.ReactNode[] = [];
  let lastIndex = 0;
  let match;

  while ((match = citationPattern.exec(text)) !== null) {
    const fullMatch = match[0];
    // Extract number from either [N] or (Source N) format
    const numberStr = match[1] || match[2];
    const citationNumber = parseInt(numberStr, 10);

    // Add text before citation
    if (match.index > lastIndex) {
      parts.push(text.substring(lastIndex, match.index));
    }

    // Find the source by citation number
    const source = sources.find(s => s.index === citationNumber);

    if (source) {
      // Add clickable citation
      parts.push(
        <sup
          key={`cite-${match.index}`}
          onClick={(e) => {
            e.preventDefault();
            e.stopPropagation();
            onSourceClick(source);
          }}
          className="inline-flex items-center justify-center w-5 h-5 text-xs font-medium text-primary-600 dark:text-primary-400 bg-primary-50 dark:bg-primary-900/20 hover:bg-primary-100 dark:hover:bg-primary-900/30 rounded cursor-pointer transition-colors ml-0.5"
          title={source.source_title}
        >
          {citationNumber}
        </sup>
      );
    } else {
      // Keep the original text if source not found
      parts.push(fullMatch);
    }

    lastIndex = match.index + fullMatch.length;
  }

  // Add remaining text
  if (lastIndex < text.length) {
    parts.push(text.substring(lastIndex));
  }

  return parts.length > 0 ? parts : text;
}

interface CodeProps {
  node?: any;
  inline?: boolean;
  className?: string;
  children?: React.ReactNode;
}

function CodeBlock({ inline, className, children, ...props }: CodeProps) {
  const [copied, setCopied] = useState(false);
  const match = /language-(\w+)/.exec(className || '');
  const language = match ? match[1] : '';
  const code = String(children).replace(/\n$/, '');

  const handleCopy = async () => {
    await navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Render inline code (single backticks in markdown)
  if (inline) {
    return (
      <code
        className="px-1.5 py-0.5 bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-200 rounded text-sm font-mono"
        {...props}
      >
        {children}
      </code>
    );
  }

  // Check if this is truly a code block or just a short snippet without language
  // If it's a single line without a language specified and under 100 chars, treat as inline
  const isShortSnippet = !language && !code.includes('\n') && code.length < 100;

  if (isShortSnippet) {
    return (
      <code
        className="px-1.5 py-0.5 bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-200 rounded text-sm font-mono"
        {...props}
      >
        {children}
      </code>
    );
  }

  // Render code block with syntax highlighting and copy button
  return (
    <div className="relative group my-4">
      <button
        onClick={handleCopy}
        className="absolute right-2 top-2 p-2 bg-gray-700 hover:bg-gray-600 text-white rounded opacity-0 group-hover:opacity-100 transition-opacity z-10"
        title="Copy code"
      >
        {copied ? <Check size={16} /> : <Copy size={16} />}
      </button>
      <SyntaxHighlighter
        style={vscDarkPlus}
        language={language || 'text'}
        PreTag="div"
        className="rounded-lg !bg-gray-900 dark:!bg-gray-950"
        customStyle={{
          margin: 0,
          padding: '1rem',
          fontSize: '0.875rem',
        }}
        {...props}
      >
        {code}
      </SyntaxHighlighter>
    </div>
  );
}

export function MarkdownRenderer({ content, className = '', sources, onSourceClick }: MarkdownRendererProps) {
  return (
    <div className={`prose prose-sm dark:prose-invert max-w-none ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkMath]}
        rehypePlugins={[rehypeKatex]}
        components={{
          code: CodeBlock,
          // Custom link styling
          a: ({ node, ...props }) => (
            <a
              {...props}
              className="text-blue-600 dark:text-blue-400 hover:underline"
              target="_blank"
              rel="noopener noreferrer"
            />
          ),
          // Custom list styling
          ul: ({ node, ...props }) => (
            <ul className="list-disc list-inside space-y-1 my-2" {...props} />
          ),
          ol: ({ node, ...props }) => (
            <ol className="list-decimal list-inside space-y-1 my-2" {...props} />
          ),
          // Custom heading styling
          h1: ({ node, ...props }) => (
            <h1 className="text-2xl font-bold mt-6 mb-4" {...props} />
          ),
          h2: ({ node, ...props }) => (
            <h2 className="text-xl font-bold mt-5 mb-3" {...props} />
          ),
          h3: ({ node, ...props }) => (
            <h3 className="text-lg font-bold mt-4 mb-2" {...props} />
          ),
          // Custom paragraph styling with citation parsing
          p: ({ node, children, ...props }) => {
            // Extract text content from children recursively
            const extractText = (node: React.ReactNode): string => {
              if (typeof node === 'string') return node;
              if (typeof node === 'number') return String(node);
              if (Array.isArray(node)) return node.map(extractText).join('');
              if (node && typeof node === 'object' && 'props' in node) {
                return extractText(node.props.children);
              }
              return '';
            };

            const textContent = extractText(children);
            const parsedContent = parseCitations(textContent, sources, onSourceClick);

            return (
              <p className="my-2 leading-relaxed" {...props}>
                {parsedContent}
              </p>
            );
          },
          // Custom blockquote styling
          blockquote: ({ node, ...props }) => (
            <blockquote
              className="border-l-4 border-gray-300 dark:border-gray-700 pl-4 italic my-4"
              {...props}
            />
          ),
          // Custom table styling
          table: ({ node, ...props }) => (
            <div className="overflow-x-auto my-4">
              <table
                className="min-w-full border border-gray-300 dark:border-gray-700"
                {...props}
              />
            </div>
          ),
          th: ({ node, ...props }) => (
            <th
              className="border border-gray-300 dark:border-gray-700 bg-gray-100 dark:bg-gray-800 px-4 py-2 text-left font-semibold"
              {...props}
            />
          ),
          td: ({ node, ...props }) => (
            <td
              className="border border-gray-300 dark:border-gray-700 px-4 py-2"
              {...props}
            />
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
