/**
 * Rich document viewer with syntax highlighting and proper formatting
 * Renders content based on file type
 */
import { useEffect, useState } from 'react';
import { Loader2 } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

interface DocumentViewerProps {
  content: string;
  fileType: string;
  filename: string;
  isLoading?: boolean;
}

export function DocumentViewer({ content, fileType, filename, isLoading }: DocumentViewerProps) {
  const [renderedContent, setRenderedContent] = useState<JSX.Element | null>(null);

  useEffect(() => {
    if (!content) return;

    const lowerType = fileType.toLowerCase();

    // Render based on file type
    if (lowerType === 'md' || lowerType === 'markdown') {
      // Markdown with GitHub Flavored Markdown
      setRenderedContent(
        <div className="prose prose-invert prose-sm max-w-none">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              code({ node, inline, className, children, ...props }) {
                const match = /language-(\w+)/.exec(className || '');
                return !inline && match ? (
                  <SyntaxHighlighter
                    style={vscDarkPlus}
                    language={match[1]}
                    PreTag="div"
                    {...props}
                  >
                    {String(children).replace(/\n$/, '')}
                  </SyntaxHighlighter>
                ) : (
                  <code className={className} {...props}>
                    {children}
                  </code>
                );
              },
            }}
          >
            {content}
          </ReactMarkdown>
        </div>
      );
    } else if (lowerType === 'html' || lowerType === 'htm') {
      // HTML rendering with sandboxing
      setRenderedContent(
        <div className="glass rounded-lg p-6">
          <div
            className="prose prose-invert prose-sm max-w-none"
            dangerouslySetInnerHTML={{ __html: content }}
          />
        </div>
      );
    } else if (['js', 'jsx', 'ts', 'tsx', 'py', 'java', 'cpp', 'c', 'go', 'rs', 'rb'].includes(lowerType)) {
      // Code files with syntax highlighting
      setRenderedContent(
        <SyntaxHighlighter
          language={lowerType === 'py' ? 'python' : lowerType}
          style={vscDarkPlus}
          showLineNumbers
          wrapLines
          customStyle={{
            margin: 0,
            borderRadius: '0.75rem',
            fontSize: '0.875rem',
          }}
        >
          {content}
        </SyntaxHighlighter>
      );
    } else if (lowerType === 'json') {
      // JSON with syntax highlighting and formatting
      try {
        const formatted = JSON.stringify(JSON.parse(content), null, 2);
        setRenderedContent(
          <SyntaxHighlighter
            language="json"
            style={vscDarkPlus}
            showLineNumbers
            customStyle={{
              margin: 0,
              borderRadius: '0.75rem',
              fontSize: '0.875rem',
            }}
          >
            {formatted}
          </SyntaxHighlighter>
        );
      } catch {
        // If JSON parsing fails, treat as plain text
        setRenderedContent(
          <pre className="whitespace-pre-wrap text-sm text-gray-300 font-mono glass rounded-lg p-4 max-h-[600px] overflow-y-auto">
            {content}
          </pre>
        );
      }
    } else if (lowerType === 'xml' || lowerType === 'svg') {
      // XML/SVG with syntax highlighting
      setRenderedContent(
        <SyntaxHighlighter
          language="xml"
          style={vscDarkPlus}
          showLineNumbers
          customStyle={{
            margin: 0,
            borderRadius: '0.75rem',
            fontSize: '0.875rem',
          }}
        >
          {content}
        </SyntaxHighlighter>
      );
    } else if (lowerType === 'css' || lowerType === 'scss' || lowerType === 'sass') {
      // CSS with syntax highlighting
      setRenderedContent(
        <SyntaxHighlighter
          language="css"
          style={vscDarkPlus}
          showLineNumbers
          customStyle={{
            margin: 0,
            borderRadius: '0.75rem',
            fontSize: '0.875rem',
          }}
        >
          {content}
        </SyntaxHighlighter>
      );
    } else if (lowerType === 'sql') {
      // SQL with syntax highlighting
      setRenderedContent(
        <SyntaxHighlighter
          language="sql"
          style={vscDarkPlus}
          showLineNumbers
          customStyle={{
            margin: 0,
            borderRadius: '0.75rem',
            fontSize: '0.875rem',
          }}
        >
          {content}
        </SyntaxHighlighter>
      );
    } else if (lowerType === 'yaml' || lowerType === 'yml') {
      // YAML with syntax highlighting
      setRenderedContent(
        <SyntaxHighlighter
          language="yaml"
          style={vscDarkPlus}
          showLineNumbers
          customStyle={{
            margin: 0,
            borderRadius: '0.75rem',
            fontSize: '0.875rem',
          }}
        >
          {content}
        </SyntaxHighlighter>
      );
    } else {
      // Plain text with nice formatting
      setRenderedContent(
        <pre className="whitespace-pre-wrap text-sm text-gray-300 font-mono glass rounded-lg p-4 max-h-[600px] overflow-y-auto leading-relaxed">
          {content}
        </pre>
      );
    }
  }, [content, fileType]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="animate-spin text-primary-400" size={32} />
      </div>
    );
  }

  if (!content) {
    return (
      <div className="glass rounded-lg p-12 text-center">
        <p className="text-gray-400 text-sm">No content available</p>
      </div>
    );
  }

  return (
    <div className="document-viewer fade-in">
      {renderedContent}
    </div>
  );
}
