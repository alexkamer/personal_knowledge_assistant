/**
 * Tests for ChatInput component
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@/test/utils';
import userEvent from '@testing-library/user-event';
import { ChatInput } from './ChatInput';

describe('ChatInput', () => {
  const mockOnSend = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Rendering', () => {
    it('should render the textarea with default placeholder', () => {
      render(<ChatInput onSend={mockOnSend} />);

      expect(screen.getByPlaceholderText('Ask a question about your notes and documents...')).toBeInTheDocument();
    });

    it('should render with custom placeholder', () => {
      render(<ChatInput onSend={mockOnSend} placeholder="Custom placeholder" />);

      expect(screen.getByPlaceholderText('Custom placeholder')).toBeInTheDocument();
    });

    it('should render the send button', () => {
      render(<ChatInput onSend={mockOnSend} />);

      expect(screen.getByLabelText('Send message')).toBeInTheDocument();
    });

    it('should render helper text', () => {
      render(<ChatInput onSend={mockOnSend} />);

      expect(screen.getByText('Press Enter to send, Shift+Enter for new line')).toBeInTheDocument();
    });

    it('should have 3 rows for textarea', () => {
      render(<ChatInput onSend={mockOnSend} />);

      const textarea = screen.getByPlaceholderText('Ask a question about your notes and documents...');
      expect(textarea).toHaveAttribute('rows', '3');
    });
  });

  describe('Input Handling', () => {
    it('should update textarea value when typing', async () => {
      const user = userEvent.setup();
      render(<ChatInput onSend={mockOnSend} />);

      const textarea = screen.getByPlaceholderText('Ask a question about your notes and documents...');
      await user.type(textarea, 'Hello world');

      expect(textarea).toHaveValue('Hello world');
    });

    it('should allow multiline input with Shift+Enter', async () => {
      const user = userEvent.setup();
      render(<ChatInput onSend={mockOnSend} />);

      const textarea = screen.getByPlaceholderText('Ask a question about your notes and documents...');
      await user.type(textarea, 'Line 1{Shift>}{Enter}{/Shift}Line 2');

      expect(textarea).toHaveValue('Line 1\nLine 2');
      expect(mockOnSend).not.toHaveBeenCalled();
    });
  });

  describe('Message Submission', () => {
    it('should call onSend when Enter key is pressed', async () => {
      const user = userEvent.setup();
      render(<ChatInput onSend={mockOnSend} />);

      const textarea = screen.getByPlaceholderText('Ask a question about your notes and documents...');
      await user.type(textarea, 'Test message{Enter}');

      expect(mockOnSend).toHaveBeenCalledWith('Test message');
      expect(mockOnSend).toHaveBeenCalledTimes(1);
    });

    it('should call onSend when send button is clicked', async () => {
      const user = userEvent.setup();
      render(<ChatInput onSend={mockOnSend} />);

      const textarea = screen.getByPlaceholderText('Ask a question about your notes and documents...');
      await user.type(textarea, 'Test message');

      const sendButton = screen.getByLabelText('Send message');
      await user.click(sendButton);

      expect(mockOnSend).toHaveBeenCalledWith('Test message');
      expect(mockOnSend).toHaveBeenCalledTimes(1);
    });

    it('should clear textarea after sending', async () => {
      const user = userEvent.setup();
      render(<ChatInput onSend={mockOnSend} />);

      const textarea = screen.getByPlaceholderText('Ask a question about your notes and documents...');
      await user.type(textarea, 'Test message{Enter}');

      await waitFor(() => {
        expect(textarea).toHaveValue('');
      });
    });

    it('should trim whitespace before sending', async () => {
      const user = userEvent.setup();
      render(<ChatInput onSend={mockOnSend} />);

      const textarea = screen.getByPlaceholderText('Ask a question about your notes and documents...');
      await user.type(textarea, '  Test message  {Enter}');

      expect(mockOnSend).toHaveBeenCalledWith('Test message');
    });

    it('should not send empty messages', async () => {
      const user = userEvent.setup();
      render(<ChatInput onSend={mockOnSend} />);

      const textarea = screen.getByPlaceholderText('Ask a question about your notes and documents...');
      await user.type(textarea, '{Enter}');

      expect(mockOnSend).not.toHaveBeenCalled();
    });

    it('should not send whitespace-only messages', async () => {
      const user = userEvent.setup();
      render(<ChatInput onSend={mockOnSend} />);

      const textarea = screen.getByPlaceholderText('Ask a question about your notes and documents...');
      await user.type(textarea, '   {Enter}');

      expect(mockOnSend).not.toHaveBeenCalled();
    });
  });

  describe('Disabled State', () => {
    it('should disable textarea when disabled prop is true', () => {
      render(<ChatInput onSend={mockOnSend} disabled={true} />);

      const textarea = screen.getByPlaceholderText('Ask a question about your notes and documents...');
      expect(textarea).toBeDisabled();
    });

    it('should disable send button when disabled prop is true', () => {
      render(<ChatInput onSend={mockOnSend} disabled={true} />);

      const sendButton = screen.getByLabelText('Send message');
      expect(sendButton).toBeDisabled();
    });

    it('should disable send button when textarea is empty', () => {
      render(<ChatInput onSend={mockOnSend} />);

      const sendButton = screen.getByLabelText('Send message');
      expect(sendButton).toBeDisabled();
    });

    it('should enable send button when textarea has content', async () => {
      const user = userEvent.setup();
      render(<ChatInput onSend={mockOnSend} />);

      const textarea = screen.getByPlaceholderText('Ask a question about your notes and documents...');
      const sendButton = screen.getByLabelText('Send message');

      expect(sendButton).toBeDisabled();

      await user.type(textarea, 'Test');

      expect(sendButton).toBeEnabled();
    });

    it('should not call onSend when disabled', async () => {
      const user = userEvent.setup();
      render(<ChatInput onSend={mockOnSend} disabled={true} />);

      const textarea = screen.getByPlaceholderText('Ask a question about your notes and documents...');
      await user.type(textarea, 'Test message{Enter}');

      expect(mockOnSend).not.toHaveBeenCalled();
    });
  });

  describe('Form Submission', () => {
    it('should prevent default form submission', async () => {
      const user = userEvent.setup();
      const mockSubmit = vi.fn((e) => e.preventDefault());

      const { container } = render(<ChatInput onSend={mockOnSend} />);
      const form = container.querySelector('form');

      if (form) {
        form.addEventListener('submit', mockSubmit);
      }

      const textarea = screen.getByPlaceholderText('Ask a question about your notes and documents...');
      await user.type(textarea, 'Test{Enter}');

      await waitFor(() => {
        expect(mockOnSend).toHaveBeenCalled();
      });
    });
  });

  describe('Keyboard Shortcuts', () => {
    it('should send message on Enter key without Shift', async () => {
      const user = userEvent.setup();
      render(<ChatInput onSend={mockOnSend} />);

      const textarea = screen.getByPlaceholderText('Ask a question about your notes and documents...');
      await user.type(textarea, 'Test{Enter}');

      expect(mockOnSend).toHaveBeenCalledWith('Test');
    });

    it('should not send message on Shift+Enter', async () => {
      const user = userEvent.setup();
      render(<ChatInput onSend={mockOnSend} />);

      const textarea = screen.getByPlaceholderText('Ask a question about your notes and documents...');
      await user.type(textarea, 'Test{Shift>}{Enter}{/Shift}');

      expect(mockOnSend).not.toHaveBeenCalled();
      expect(textarea).toHaveValue('Test\n');
    });
  });

  describe('Accessibility', () => {
    it('should have proper aria-label for send button', () => {
      render(<ChatInput onSend={mockOnSend} />);

      const sendButton = screen.getByLabelText('Send message');
      expect(sendButton).toHaveAttribute('aria-label', 'Send message');
    });

    it('should have accessible button type', () => {
      render(<ChatInput onSend={mockOnSend} />);

      const sendButton = screen.getByLabelText('Send message');
      expect(sendButton).toHaveAttribute('type', 'submit');
    });

    it('should be keyboard navigable', async () => {
      const user = userEvent.setup();
      render(<ChatInput onSend={mockOnSend} />);

      const textarea = screen.getByPlaceholderText('Ask a question about your notes and documents...');

      // Tab should focus textarea
      await user.tab();
      expect(textarea).toHaveFocus();

      // Type message
      await user.keyboard('Test message');

      // Tab should move to send button
      await user.tab();
      const sendButton = screen.getByLabelText('Send message');
      expect(sendButton).toHaveFocus();
    });
  });

  describe('Edge Cases', () => {
    it('should handle very long messages', async () => {
      const user = userEvent.setup();
      render(<ChatInput onSend={mockOnSend} />);

      const longMessage = 'a'.repeat(1000);
      const textarea = screen.getByPlaceholderText('Ask a question about your notes and documents...');
      await user.type(textarea, longMessage);

      const sendButton = screen.getByLabelText('Send message');
      await user.click(sendButton);

      expect(mockOnSend).toHaveBeenCalledWith(longMessage);
    });

    it('should handle special characters', async () => {
      const user = userEvent.setup();
      render(<ChatInput onSend={mockOnSend} />);

      const specialMessage = '!@#$%^&*()_+-={}[]|:;"<>,.?/~`';
      const textarea = screen.getByPlaceholderText('Ask a question about your notes and documents...');

      await user.click(textarea);
      await user.paste(specialMessage);

      const sendButton = screen.getByLabelText('Send message');
      await user.click(sendButton);

      expect(mockOnSend).toHaveBeenCalledWith(specialMessage);
    });

    it('should handle rapid submissions', async () => {
      const user = userEvent.setup();
      render(<ChatInput onSend={mockOnSend} />);

      const textarea = screen.getByPlaceholderText('Ask a question about your notes and documents...');

      await user.type(textarea, 'Message 1{Enter}');
      await user.type(textarea, 'Message 2{Enter}');
      await user.type(textarea, 'Message 3{Enter}');

      expect(mockOnSend).toHaveBeenCalledTimes(3);
      expect(mockOnSend).toHaveBeenNthCalledWith(1, 'Message 1');
      expect(mockOnSend).toHaveBeenNthCalledWith(2, 'Message 2');
      expect(mockOnSend).toHaveBeenNthCalledWith(3, 'Message 3');
    });
  });
});
