/**
 * Tests for MarkdownRenderer component
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@/test/utils';
import userEvent from '@testing-library/user-event';
import { MarkdownRenderer } from './MarkdownRenderer';

describe('MarkdownRenderer', () => {
  // Mock clipboard API
  const mockWriteText = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    mockWriteText.mockResolvedValue(undefined);

    // Mock clipboard API
    Object.defineProperty(navigator, 'clipboard', {
      value: {
        writeText: mockWriteText,
      },
      writable: true,
      configurable: true,
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Basic Rendering', () => {
    it('should render plain text content', () => {
      render(<MarkdownRenderer content="Hello world" />);

      expect(screen.getByText('Hello world')).toBeInTheDocument();
    });

    it('should render with custom className', () => {
      const { container } = render(<MarkdownRenderer content="Test" className="custom-class" />);

      const prose = container.querySelector('.prose');
      expect(prose).toHaveClass('custom-class');
    });

    it('should apply prose styling classes', () => {
      const { container } = render(<MarkdownRenderer content="Test" />);

      const prose = container.querySelector('.prose');
      expect(prose).toHaveClass('prose', 'prose-sm', 'dark:prose-invert', 'max-w-none');
    });
  });

  describe('Markdown Elements', () => {
    it('should render headings', () => {
      const content = '# Heading 1\n## Heading 2\n### Heading 3';
      render(<MarkdownRenderer content={content} />);

      expect(screen.getByText('Heading 1')).toBeInTheDocument();
      expect(screen.getByText('Heading 2')).toBeInTheDocument();
      expect(screen.getByText('Heading 3')).toBeInTheDocument();
    });

    it('should render bold text', () => {
      render(<MarkdownRenderer content="This is **bold** text" />);

      const boldElement = screen.getByText('bold');
      expect(boldElement.tagName).toBe('STRONG');
    });

    it('should render italic text', () => {
      render(<MarkdownRenderer content="This is *italic* text" />);

      const italicElement = screen.getByText('italic');
      expect(italicElement.tagName).toBe('EM');
    });

    it('should render unordered lists', () => {
      const content = '- Item 1\n- Item 2\n- Item 3';
      render(<MarkdownRenderer content={content} />);

      expect(screen.getByText('Item 1')).toBeInTheDocument();
      expect(screen.getByText('Item 2')).toBeInTheDocument();
      expect(screen.getByText('Item 3')).toBeInTheDocument();
    });

    it('should render ordered lists', () => {
      const content = '1. First\n2. Second\n3. Third';
      render(<MarkdownRenderer content={content} />);

      expect(screen.getByText('First')).toBeInTheDocument();
      expect(screen.getByText('Second')).toBeInTheDocument();
      expect(screen.getByText('Third')).toBeInTheDocument();
    });

    it('should render links with target blank', () => {
      render(<MarkdownRenderer content="[Google](https://google.com)" />);

      const link = screen.getByText('Google');
      expect(link).toHaveAttribute('href', 'https://google.com');
      expect(link).toHaveAttribute('target', '_blank');
      expect(link).toHaveAttribute('rel', 'noopener noreferrer');
    });

    it('should render blockquotes', () => {
      render(<MarkdownRenderer content="> This is a quote" />);

      expect(screen.getByText('This is a quote')).toBeInTheDocument();
    });
  });

  describe('GFM (GitHub Flavored Markdown)', () => {
    it('should render strikethrough text', () => {
      render(<MarkdownRenderer content="~~strikethrough~~" />);

      const strikeElement = screen.getByText(/strikethrough/);
      expect(strikeElement).toBeInTheDocument();
    });

    it('should render tables', () => {
      const content = `
| Header 1 | Header 2 |
|----------|----------|
| Cell 1   | Cell 2   |
`;
      render(<MarkdownRenderer content={content} />);

      expect(screen.getByText('Header 1')).toBeInTheDocument();
      expect(screen.getByText('Header 2')).toBeInTheDocument();
      expect(screen.getByText('Cell 1')).toBeInTheDocument();
      expect(screen.getByText('Cell 2')).toBeInTheDocument();
    });

    it('should render task lists', () => {
      const content = '- [ ] Unchecked\n- [x] Checked';
      render(<MarkdownRenderer content={content} />);

      expect(screen.getByText('Unchecked')).toBeInTheDocument();
      expect(screen.getByText('Checked')).toBeInTheDocument();
    });
  });

  describe('Inline Code', () => {
    it('should render text with inline code', () => {
      render(<MarkdownRenderer content="Use `const` for constants" />);

      // The text should be rendered
      expect(screen.getByText(/for constants/)).toBeInTheDocument();
    });

    it('should have code elements in the document', () => {
      const { container } = render(<MarkdownRenderer content="Use `inline` code" />);

      const code = container.querySelector('code');
      expect(code).toBeInTheDocument();
    });
  });

  describe('Code Blocks', () => {
    it('should render code blocks', () => {
      const content = '```\nconst x = 1;\n```';
      render(<MarkdownRenderer content={content} />);

      expect(screen.getByText(/const/)).toBeInTheDocument();
    });

    it('should render code blocks with language', () => {
      const content = '```javascript\nconst x = 1;\n```';
      render(<MarkdownRenderer content={content} />);

      expect(screen.getByText(/const/)).toBeInTheDocument();
    });

    it('should show copy button for code blocks', () => {
      const content = '```\ncode\n```';
      render(<MarkdownRenderer content={content} />);

      const copyButton = screen.getByTitle('Copy code');
      expect(copyButton).toBeInTheDocument();
    });
  });

  describe('Copy Functionality', () => {
    it('should show copy button for code blocks', () => {
      const content = '```\nconst x = 1;\n```';
      render(<MarkdownRenderer content={content} />);

      const copyButton = screen.getByTitle('Copy code');
      expect(copyButton).toBeInTheDocument();
    });

    it('should have clickable copy button', () => {
      const content = '```\ncode\n```';
      render(<MarkdownRenderer content={content} />);

      const copyButton = screen.getByTitle('Copy code');
      expect(copyButton).toHaveAttribute('title', 'Copy code');
      expect(copyButton.tagName).toBe('BUTTON');
    });
  });

  describe('Syntax Highlighting', () => {
    it('should apply syntax highlighting to code blocks', () => {
      const content = '```javascript\nconst x = 1;\n```';
      const { container } = render(<MarkdownRenderer content={content} />);

      // SyntaxHighlighter creates a code element with specific class
      const code = container.querySelector('code.language-javascript');
      expect(code).toBeInTheDocument();
    });

    it('should use text language for code without specified language', () => {
      const content = '```\nplain code\n```';
      const { container } = render(<MarkdownRenderer content={content} />);

      const code = container.querySelector('code.language-text');
      expect(code).toBeInTheDocument();
    });

    it('should handle multiple code blocks', () => {
      const content = '```\nblock 1\n```\n\n```\nblock 2\n```';
      render(<MarkdownRenderer content={content} />);

      expect(screen.getByText(/block 1/)).toBeInTheDocument();
      expect(screen.getByText(/block 2/)).toBeInTheDocument();

      const copyButtons = screen.getAllByTitle('Copy code');
      expect(copyButtons).toHaveLength(2);
    });
  });

  describe('Custom Styling', () => {
    it('should apply custom heading styles', () => {
      const { container } = render(<MarkdownRenderer content="# Heading" />);

      const h1 = container.querySelector('h1');
      expect(h1).toHaveClass('text-2xl', 'font-bold');
    });

    it('should apply custom paragraph styles', () => {
      const { container } = render(<MarkdownRenderer content="Paragraph text" />);

      const p = container.querySelector('p');
      expect(p).toHaveClass('my-2', 'leading-relaxed');
    });

    it('should apply custom list styles', () => {
      const { container } = render(<MarkdownRenderer content="- Item" />);

      const ul = container.querySelector('ul');
      expect(ul).toHaveClass('list-disc', 'list-inside');
    });

    it('should apply custom blockquote styles', () => {
      const { container } = render(<MarkdownRenderer content="> Quote" />);

      const blockquote = container.querySelector('blockquote');
      expect(blockquote).toHaveClass('border-l-4', 'pl-4', 'italic');
    });

    it('should apply custom table styles', () => {
      const content = `
| A | B |
|---|---|
| 1 | 2 |
`;
      const { container } = render(<MarkdownRenderer content={content} />);

      const th = container.querySelector('th');
      expect(th).toHaveClass('bg-gray-100', 'dark:bg-gray-800');
    });
  });

  describe('Edge Cases', () => {
    it('should render empty string', () => {
      const { container } = render(<MarkdownRenderer content="" />);

      const prose = container.querySelector('.prose');
      expect(prose).toBeInTheDocument();
    });

    it('should handle very long content', () => {
      const longContent = 'word '.repeat(1000);
      render(<MarkdownRenderer content={longContent} />);

      expect(screen.getByText(/word/)).toBeInTheDocument();
    });

    it('should handle special characters', () => {
      render(<MarkdownRenderer content={'Special: <>&"\''} />);

      expect(screen.getByText(/Special:/)).toBeInTheDocument();
    });

    it('should handle multiple markdown features together', () => {
      const content = `
# Title

This is **bold** and *italic* text.

- List item 1
- List item 2

\`\`\`javascript
const x = 1;
\`\`\`

[Link](https://example.com)
`;
      render(<MarkdownRenderer content={content} />);

      expect(screen.getByText('Title')).toBeInTheDocument();
      expect(screen.getByText('bold')).toBeInTheDocument();
      expect(screen.getByText('italic')).toBeInTheDocument();
      expect(screen.getByText('List item 1')).toBeInTheDocument();
      expect(screen.getByText(/const/)).toBeInTheDocument();
      expect(screen.getByText('Link')).toBeInTheDocument();
    });

    it('should handle code blocks with various languages', () => {
      const content = `
\`\`\`python
def hello():
    print("hi")
\`\`\`

\`\`\`typescript
const x: number = 1;
\`\`\`
`;
      render(<MarkdownRenderer content={content} />);

      // Check that code elements exist
      expect(screen.getByText(/def/)).toBeInTheDocument();
      expect(screen.getByText(/hello/)).toBeInTheDocument();
      expect(screen.getByText(/const/)).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have accessible link attributes', () => {
      render(<MarkdownRenderer content="[Link](https://example.com)" />);

      const link = screen.getByText('Link');
      expect(link).toHaveAttribute('rel', 'noopener noreferrer');
    });

    it('should have title on copy button', () => {
      render(<MarkdownRenderer content="```\ncode\n```" />);

      const button = screen.getByTitle('Copy code');
      expect(button).toHaveAttribute('title', 'Copy code');
    });
  });
});
