/**
 * Renders formatted text with markdown and HTML styling
 * Converts markdown syntax to visual formatting
 */
import React from 'react';

interface FormatRendererProps {
  content: string;
  className?: string;
}

export function FormatRenderer({ content, className = '' }: FormatRendererProps) {
  // Parse and render the content with formatting
  const renderContent = () => {
    let rendered = content;

    // Check for heading levels first (must be at start of line)
    const headingMatch = rendered.match(/^(#{1,3})\s+(.*)$/);
    if (headingMatch) {
      const level = headingMatch[1].length;
      const text = headingMatch[2];

      // Render heading with appropriate size
      const sizeClasses = {
        1: 'text-3xl font-bold text-stone-900',
        2: 'text-2xl font-semibold text-stone-800',
        3: 'text-xl font-medium text-stone-700',
      };

      return (
        <div className={`${sizeClasses[level as 1 | 2 | 3]} ${className}`}>
          {renderInlineFormatting(text)}
        </div>
      );
    }

    // Regular text with inline formatting
    return (
      <div className={className}>
        {renderInlineFormatting(rendered)}
      </div>
    );
  };

  // Render inline formatting (bold, italic, underline, colors)
  const renderInlineFormatting = (text: string): React.ReactNode => {
    const parts: React.ReactNode[] = [];
    let currentIndex = 0;
    const patterns = [
      // HTML color/highlight spans
      { regex: /<span style="([^"]+)">([^<]+)<\/span>/g, type: 'span' },
      // Bold: **text**
      { regex: /\*\*([^*]+)\*\*/g, type: 'bold' },
      // Italic: *text*
      { regex: /\*([^*]+)\*/g, type: 'italic' },
      // Underline: __text__
      { regex: /__([^_]+)__/g, type: 'underline' },
    ];

    // Find all matches
    const matches: Array<{ index: number; length: number; element: React.ReactNode }> = [];

    patterns.forEach((pattern) => {
      const regex = new RegExp(pattern.regex.source, 'g');
      let match;

      while ((match = regex.exec(text)) !== null) {
        let element: React.ReactNode;

        if (pattern.type === 'span') {
          const style = match[1];
          const content = match[2];
          // Parse style attribute
          const styleObj: Record<string, string> = {};
          style.split(';').forEach((s) => {
            const [key, value] = s.split(':').map((x) => x.trim());
            if (key && value) {
              styleObj[key] = value;
            }
          });
          element = <span key={match.index} style={styleObj}>{content}</span>;
        } else if (pattern.type === 'bold') {
          element = <strong key={match.index}>{match[1]}</strong>;
        } else if (pattern.type === 'italic') {
          element = <em key={match.index}>{match[1]}</em>;
        } else if (pattern.type === 'underline') {
          element = <u key={match.index}>{match[1]}</u>;
        }

        matches.push({
          index: match.index,
          length: match[0].length,
          element: element!,
        });
      }
    });

    // Sort matches by index
    matches.sort((a, b) => a.index - b.index);

    // Build the final output
    matches.forEach((match) => {
      // Add text before this match
      if (match.index > currentIndex) {
        parts.push(text.substring(currentIndex, match.index));
      }

      // Add the formatted element
      parts.push(match.element);

      currentIndex = match.index + match.length;
    });

    // Add remaining text
    if (currentIndex < text.length) {
      parts.push(text.substring(currentIndex));
    }

    return parts.length > 0 ? parts : text;
  };

  return <>{renderContent()}</>;
}
