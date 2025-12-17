/**
 * Tests for ChatPage component - focusing on new features
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@/test/utils';
import userEvent from '@testing-library/user-event';
import { ChatPage } from './ChatPage';
import { chatService } from '@/services/chatService';
import * as useChat from '@/hooks/useChat';

// Mock scrollIntoView
Element.prototype.scrollIntoView = vi.fn();

// Mock chat service
vi.mock('@/services/chatService', () => ({
  chatService: {
    sendMessageStream: vi.fn(),
    getAgents: vi.fn(),
    getTokenUsage: vi.fn().mockResolvedValue({
      total_tokens: 100,
      limit: 32768,
      usage_percent: 0.3,
      remaining: 32668,
      is_warning: false,
      is_critical: false,
      messages_count: 2,
      message_tokens: [],
    }),
  },
}));

// Mock useChat hooks
vi.mock('@/hooks/useChat', () => ({
  useConversations: vi.fn(),
  useConversation: vi.fn(),
  useSendMessage: vi.fn(),
  useDeleteConversation: vi.fn(),
  useUpdateConversation: vi.fn(),
}));

// Mock theme context
vi.mock('@/contexts/ThemeContext', () => ({
  useTheme: () => ({
    theme: 'light',
    toggleTheme: vi.fn(),
  }),
}));

// Mock keyboard shortcuts hook
vi.mock('@/hooks/useKeyboardShortcuts', () => ({
  useKeyboardShortcuts: () => {},
}));

// Mock export utils
vi.mock('@/utils/exportMarkdown', () => ({
  downloadConversationAsMarkdown: vi.fn(),
}));

describe('ChatPage - New Features', () => {
  const mockSendMessageStream = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();

    // Setup default mocks
    vi.mocked(useChat.useConversations).mockReturnValue({
      data: { conversations: [], total: 0 },
      isLoading: false,
      error: null,
    } as any);

    vi.mocked(useChat.useConversation).mockReturnValue({
      data: null,
      isLoading: false,
      error: null,
    } as any);

    vi.mocked(useChat.useSendMessage).mockReturnValue({
      mutate: vi.fn(),
      mutateAsync: vi.fn(),
    } as any);

    vi.mocked(useChat.useDeleteConversation).mockReturnValue({
      mutate: vi.fn(),
    } as any);

    vi.mocked(useChat.useUpdateConversation).mockReturnValue({
      mutate: vi.fn(),
    } as any);

    vi.mocked(chatService.sendMessageStream).mockImplementation(mockSendMessageStream);
  });

  describe('Loading States Feature', () => {
    it('should display loading status messages during streaming', async () => {
      const user = userEvent.setup();

      // Mock sendMessageStream to simulate status updates
      mockSendMessageStream.mockImplementation(async (
        request,
        onChunk,
        onSources,
        onConversationId,
        onDone,
        onError,
        onSuggestedQuestions,
        onAgent,
        onStatus
      ) => {
        // Simulate status progression
        onStatus?.('Analyzing your question...');
        await new Promise(resolve => setTimeout(resolve, 50));
        onStatus?.('Searching knowledge base...');
        await new Promise(resolve => setTimeout(resolve, 50));
        onStatus?.('Found 2 relevant sources...');
        await new Promise(resolve => setTimeout(resolve, 50));
        onStatus?.('Generating answer...');
        await new Promise(resolve => setTimeout(resolve, 50));

        // Simulate response
        onConversationId('test-conversation-id');
        onChunk('Test response');
        onDone('test-message-id');
      });

      render(<ChatPage />);

      // Find and fill the input
      const input = screen.getByPlaceholderText(/ask a question/i);
      await user.type(input, 'What is AI?');
      await user.keyboard('{Enter}');

      // Check that status messages appear
      await waitFor(() => {
        expect(screen.getByText(/analyzing your question/i)).toBeInTheDocument();
      });

      await waitFor(() => {
        expect(screen.getByText(/searching knowledge base/i)).toBeInTheDocument();
      });

      await waitFor(() => {
        expect(screen.getByText(/found 2 relevant sources/i)).toBeInTheDocument();
      });

      await waitFor(() => {
        expect(screen.getByText(/generating answer/i)).toBeInTheDocument();
      });
    });

    it('should show animated dots with loading status', async () => {
      const user = userEvent.setup();

      mockSendMessageStream.mockImplementation(async (
        request,
        onChunk,
        onSources,
        onConversationId,
        onDone,
        onError,
        onSuggestedQuestions,
        onAgent,
        onStatus
      ) => {
        onStatus?.('Processing...');
        await new Promise(resolve => setTimeout(resolve, 100));
        onConversationId('test-conversation-id');
        onDone('test-message-id');
      });

      render(<ChatPage />);

      const input = screen.getByPlaceholderText(/ask a question/i);
      await user.type(input, 'Test question');
      await user.keyboard('{Enter}');

      // Check for animated dots (they should be in the DOM with specific classes)
      await waitFor(() => {
        const dots = document.querySelectorAll('.animate-bounce');
        expect(dots.length).toBeGreaterThanOrEqual(3); // 3 animated dots
      });
    });

    it('should clear status when streaming completes', async () => {
      const user = userEvent.setup();

      mockSendMessageStream.mockImplementation(async (
        request,
        onChunk,
        onSources,
        onConversationId,
        onDone,
        onError,
        onSuggestedQuestions,
        onAgent,
        onStatus
      ) => {
        onStatus?.('Generating answer...');
        await new Promise(resolve => setTimeout(resolve, 50));
        onConversationId('test-conversation-id');
        onChunk('Complete response');
        onDone('test-message-id');
      });

      render(<ChatPage />);

      const input = screen.getByPlaceholderText(/ask a question/i);
      await user.type(input, 'Test');
      await user.keyboard('{Enter}');

      // Status should appear
      await waitFor(() => {
        expect(screen.getByText(/generating answer/i)).toBeInTheDocument();
      });

      // Status should disappear after completion
      await waitFor(() => {
        expect(screen.queryByText(/generating answer/i)).not.toBeInTheDocument();
      }, { timeout: 2000 });
    });
  });

  describe('Notes Toggle Feature', () => {
    it('should render notes toggle button with default state (notes excluded)', () => {
      render(<ChatPage />);

      const notesToggle = screen.getByRole('button', { name: /reputable sources only.*no notes/i });
      expect(notesToggle).toBeInTheDocument();
    });

    it('should toggle notes inclusion when button is clicked', async () => {
      const user = userEvent.setup();

      render(<ChatPage />);

      const notesToggle = screen.getByRole('button', { name: /reputable sources only.*no notes/i });

      // Initially should show "no notes"
      expect(notesToggle).toHaveTextContent(/reputable sources only/i);

      // Click to enable notes
      await user.click(notesToggle);

      // Should now show "including notes"
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /including personal notes/i })).toBeInTheDocument();
      });

      // Click again to disable notes
      await user.click(screen.getByRole('button', { name: /including personal notes/i }));

      // Should go back to "no notes"
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /reputable sources only.*no notes/i })).toBeInTheDocument();
      });
    });

    it('should pass include_notes parameter when notes toggle is enabled', async () => {
      const user = userEvent.setup();

      mockSendMessageStream.mockImplementation(async (
        request,
        onChunk,
        onSources,
        onConversationId,
        onDone
      ) => {
        onConversationId('test-conversation-id');
        onChunk('Response');
        onDone('test-message-id');
      });

      render(<ChatPage />);

      // Enable notes toggle
      const notesToggle = screen.getByRole('button', { name: /reputable sources only.*no notes/i });
      await user.click(notesToggle);

      // Wait for toggle to update
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /including personal notes/i })).toBeInTheDocument();
      });

      // Send a message
      const input = screen.getByPlaceholderText(/ask a question/i);
      await user.type(input, 'Test with notes');
      await user.keyboard('{Enter}');

      // Verify that sendMessageStream was called with include_notes: true
      await waitFor(() => {
        expect(mockSendMessageStream).toHaveBeenCalledWith(
          expect.objectContaining({
            message: 'Test with notes',
            include_notes: true,
          }),
          expect.any(Function), // onChunk
          expect.any(Function), // onSources
          expect.any(Function), // onConversationId
          expect.any(Function), // onDone
          expect.any(Function), // onError
          expect.any(Function), // onSuggestedQuestions
          expect.any(Function), // onAgent
          expect.any(Function), // onStatus
          expect.any(Function), // onToolCall
          expect.any(Function)  // onToolResult
        );
      });
    });

    it('should pass include_notes: false when notes toggle is disabled (default)', async () => {
      const user = userEvent.setup();

      mockSendMessageStream.mockImplementation(async (
        request,
        onChunk,
        onSources,
        onConversationId,
        onDone
      ) => {
        onConversationId('test-conversation-id');
        onChunk('Response');
        onDone('test-message-id');
      });

      render(<ChatPage />);

      // Send a message without enabling notes
      const input = screen.getByPlaceholderText(/ask a question/i);
      await user.type(input, 'Test without notes');
      await user.keyboard('{Enter}');

      // Verify that sendMessageStream was called with include_notes: false
      await waitFor(() => {
        expect(mockSendMessageStream).toHaveBeenCalledWith(
          expect.objectContaining({
            message: 'Test without notes',
            include_notes: false,
          }),
          expect.any(Function), // onChunk
          expect.any(Function), // onSources
          expect.any(Function), // onConversationId
          expect.any(Function), // onDone
          expect.any(Function), // onError
          expect.any(Function), // onSuggestedQuestions
          expect.any(Function), // onAgent
          expect.any(Function), // onStatus
          expect.any(Function), // onToolCall
          expect.any(Function)  // onToolResult
        );
      });
    });
  });

  describe('Combined Features', () => {
    it('should show loading states and respect notes toggle simultaneously', async () => {
      const user = userEvent.setup();

      mockSendMessageStream.mockImplementation(async (
        request,
        onChunk,
        onSources,
        onConversationId,
        onDone,
        onError,
        onSuggestedQuestions,
        onAgent,
        onStatus
      ) => {
        // Verify include_notes is true
        expect(request.include_notes).toBe(true);

        // Show status
        onStatus?.('Analyzing your question...');
        await new Promise(resolve => setTimeout(resolve, 50));
        onConversationId('test-conversation-id');
        onChunk('Response with notes');
        onDone('test-message-id');
      });

      render(<ChatPage />);

      // Enable notes toggle
      const notesToggle = screen.getByRole('button', { name: /reputable sources only.*no notes/i });
      await user.click(notesToggle);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /including personal notes/i })).toBeInTheDocument();
      });

      // Send message
      const input = screen.getByPlaceholderText(/ask a question/i);
      await user.type(input, 'Test both features');
      await user.keyboard('{Enter}');

      // Should show loading status
      await waitFor(() => {
        expect(screen.getByText(/analyzing your question/i)).toBeInTheDocument();
      });

      // Should have called with include_notes: true
      expect(mockSendMessageStream).toHaveBeenCalledWith(
        expect.objectContaining({
          include_notes: true,
        }),
        expect.any(Function), // onChunk
        expect.any(Function), // onSources
        expect.any(Function), // onConversationId
        expect.any(Function), // onDone
        expect.any(Function), // onError
        expect.any(Function), // onSuggestedQuestions
        expect.any(Function), // onAgent
        expect.any(Function), // onStatus
        expect.any(Function), // onToolCall
        expect.any(Function)  // onToolResult
      );
    });
  });
});
