/**
 * Tests for TokenUsage component
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@/test/utils';
import { TokenUsage } from './TokenUsage';
import { chatService } from '@/services/chatService';

// Mock the chat service
vi.mock('@/services/chatService', () => ({
  chatService: {
    getTokenUsage: vi.fn(),
  },
}));

describe('TokenUsage', () => {
  const mockConversationId = 'test-conversation-123';
  const mockGetTokenUsage = vi.mocked(chatService.getTokenUsage);

  const mockUsageData = {
    total_tokens: 1000,
    limit: 32768,
    usage_percent: 3.05,
    remaining: 31768,
    is_warning: false,
    is_critical: false,
    messages_count: 4,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Rendering', () => {
    it('should render token usage information', async () => {
      mockGetTokenUsage.mockResolvedValue(mockUsageData);

      render(<TokenUsage conversationId={mockConversationId} />);

      await waitFor(() => {
        expect(screen.getByText('Context')).toBeInTheDocument();
        expect(screen.getByText('3.0%')).toBeInTheDocument();
        expect(screen.getByText('1,000')).toBeInTheDocument();
        expect(screen.getByText('32,768')).toBeInTheDocument();
      });
    });

    it('should not render when conversationId is null', () => {
      const { container } = render(<TokenUsage conversationId={null} />);

      expect(container.firstChild).toBeNull();
    });

    it('should render progress bar with correct width', async () => {
      mockGetTokenUsage.mockResolvedValue(mockUsageData);

      const { container } = render(<TokenUsage conversationId={mockConversationId} />);

      await waitFor(() => {
        const progressBar = container.querySelector('[style*="width"]');
        expect(progressBar).toHaveStyle({ width: '3.05%' });
      });
    });

    it('should format large numbers with locale separators', async () => {
      mockGetTokenUsage.mockResolvedValue({
        ...mockUsageData,
        total_tokens: 25000,
        limit: 131072,
      });

      render(<TokenUsage conversationId={mockConversationId} />);

      await waitFor(() => {
        expect(screen.getByText('25,000')).toBeInTheDocument();
        expect(screen.getByText('131,072')).toBeInTheDocument();
      });
    });
  });

  describe('Loading State', () => {
    it('should not render while loading', async () => {
      mockGetTokenUsage.mockImplementation(() => new Promise(() => {})); // Never resolves

      const { container } = render(<TokenUsage conversationId={mockConversationId} />);

      expect(container.firstChild).toBeNull();
    });
  });

  describe('Error State', () => {
    it('should show error message when fetch fails', async () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      mockGetTokenUsage.mockRejectedValue(new Error('Network error'));

      render(<TokenUsage conversationId={mockConversationId} />);

      await waitFor(() => {
        expect(screen.getByText('Failed to load token usage')).toBeInTheDocument();
      });

      consoleErrorSpy.mockRestore();
    });

    it('should log error to console', async () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      const error = new Error('API error');
      mockGetTokenUsage.mockRejectedValue(error);

      render(<TokenUsage conversationId={mockConversationId} />);

      await waitFor(() => {
        expect(consoleErrorSpy).toHaveBeenCalledWith('Failed to fetch token usage:', error);
      });

      consoleErrorSpy.mockRestore();
    });
  });

  describe('Model Prop', () => {
    it('should use default model if not specified', async () => {
      mockGetTokenUsage.mockResolvedValue(mockUsageData);

      render(<TokenUsage conversationId={mockConversationId} />);

      await waitFor(() => {
        expect(mockGetTokenUsage).toHaveBeenCalledWith(mockConversationId, 'qwen2.5:14b');
      });
    });

    it('should use custom model when specified', async () => {
      mockGetTokenUsage.mockResolvedValue(mockUsageData);

      render(<TokenUsage conversationId={mockConversationId} model="phi-4:14b" />);

      await waitFor(() => {
        expect(mockGetTokenUsage).toHaveBeenCalledWith(mockConversationId, 'phi-4:14b');
      });
    });
  });

  describe('Color States - Normal (Green)', () => {
    it('should display green color for normal usage', async () => {
      mockGetTokenUsage.mockResolvedValue(mockUsageData);

      const { container } = render(<TokenUsage conversationId={mockConversationId} />);

      await waitFor(() => {
        const progressBar = container.querySelector('.bg-green-500');
        expect(progressBar).toBeInTheDocument();

        const percentage = screen.getByText('3.0%');
        expect(percentage).toHaveClass('text-green-700', 'dark:text-green-300');
      });
    });

    it('should not show warning or critical badges for normal usage', async () => {
      mockGetTokenUsage.mockResolvedValue(mockUsageData);

      render(<TokenUsage conversationId={mockConversationId} />);

      await waitFor(() => {
        expect(screen.queryByText('Warning')).not.toBeInTheDocument();
        expect(screen.queryByText('Critical')).not.toBeInTheDocument();
      });
    });
  });

  describe('Color States - Warning (Yellow)', () => {
    it('should display yellow color for warning usage', async () => {
      mockGetTokenUsage.mockResolvedValue({
        ...mockUsageData,
        total_tokens: 23000,
        usage_percent: 70.19,
        is_warning: true,
        is_critical: false,
      });

      const { container } = render(<TokenUsage conversationId={mockConversationId} />);

      await waitFor(() => {
        const progressBar = container.querySelector('.bg-yellow-500');
        expect(progressBar).toBeInTheDocument();

        const percentage = screen.getByText('70.2%');
        expect(percentage).toHaveClass('text-yellow-700', 'dark:text-yellow-300');
      });
    });

    it('should show warning badge for warning usage', async () => {
      mockGetTokenUsage.mockResolvedValue({
        ...mockUsageData,
        usage_percent: 75,
        is_warning: true,
        is_critical: false,
      });

      render(<TokenUsage conversationId={mockConversationId} />);

      await waitFor(() => {
        expect(screen.getByText('Warning')).toBeInTheDocument();
        expect(screen.queryByText('Critical')).not.toBeInTheDocument();
      });
    });
  });

  describe('Color States - Critical (Red)', () => {
    it('should display red color for critical usage', async () => {
      mockGetTokenUsage.mockResolvedValue({
        ...mockUsageData,
        total_tokens: 30000,
        usage_percent: 91.55,
        is_warning: true,
        is_critical: true,
      });

      const { container } = render(<TokenUsage conversationId={mockConversationId} />);

      await waitFor(() => {
        const progressBar = container.querySelector('.bg-red-500');
        expect(progressBar).toBeInTheDocument();

        const percentage = screen.getByText('91.5%');
        expect(percentage).toHaveClass('text-red-700', 'dark:text-red-300');
      });
    });

    it('should show critical badge for critical usage', async () => {
      mockGetTokenUsage.mockResolvedValue({
        ...mockUsageData,
        usage_percent: 95,
        is_warning: true,
        is_critical: true,
      });

      render(<TokenUsage conversationId={mockConversationId} />);

      await waitFor(() => {
        expect(screen.getByText('Critical')).toBeInTheDocument();
        expect(screen.queryByText('Warning')).not.toBeInTheDocument();
      });
    });

    it('should prioritize critical over warning when both are true', async () => {
      mockGetTokenUsage.mockResolvedValue({
        ...mockUsageData,
        usage_percent: 95,
        is_warning: true,
        is_critical: true,
      });

      render(<TokenUsage conversationId={mockConversationId} />);

      await waitFor(() => {
        expect(screen.getByText('Critical')).toBeInTheDocument();
        expect(screen.queryByText('Warning')).not.toBeInTheDocument();
      });
    });
  });

  describe('Progress Bar Capping', () => {
    it('should cap progress bar at 100% even if usage exceeds limit', async () => {
      mockGetTokenUsage.mockResolvedValue({
        ...mockUsageData,
        total_tokens: 35000,
        usage_percent: 106.81,
        is_critical: true,
      });

      const { container } = render(<TokenUsage conversationId={mockConversationId} />);

      await waitFor(() => {
        const progressBar = container.querySelector('[style*="width"]');
        expect(progressBar).toHaveStyle({ width: '100%' });
      });
    });
  });

  describe('useEffect Behavior', () => {
    it('should fetch token usage when conversationId changes', async () => {
      mockGetTokenUsage.mockResolvedValue(mockUsageData);

      const { rerender } = render(<TokenUsage conversationId={mockConversationId} />);

      await waitFor(() => {
        expect(mockGetTokenUsage).toHaveBeenCalledTimes(1);
      });

      const newConversationId = 'new-conversation-456';
      rerender(<TokenUsage conversationId={newConversationId} />);

      await waitFor(() => {
        expect(mockGetTokenUsage).toHaveBeenCalledTimes(2);
        expect(mockGetTokenUsage).toHaveBeenLastCalledWith(newConversationId, 'qwen2.5:14b');
      });
    });

    it('should fetch token usage when model changes', async () => {
      mockGetTokenUsage.mockResolvedValue(mockUsageData);

      const { rerender } = render(
        <TokenUsage conversationId={mockConversationId} model="qwen2.5:14b" />
      );

      await waitFor(() => {
        expect(mockGetTokenUsage).toHaveBeenCalledTimes(1);
      });

      rerender(<TokenUsage conversationId={mockConversationId} model="phi-4:14b" />);

      await waitFor(() => {
        expect(mockGetTokenUsage).toHaveBeenCalledTimes(2);
        expect(mockGetTokenUsage).toHaveBeenLastCalledWith(mockConversationId, 'phi-4:14b');
      });
    });

    it('should clear usage when conversationId becomes null', async () => {
      mockGetTokenUsage.mockResolvedValue(mockUsageData);

      const { rerender, container } = render(<TokenUsage conversationId={mockConversationId} />);

      await waitFor(() => {
        expect(screen.getByText('Context')).toBeInTheDocument();
      });

      rerender(<TokenUsage conversationId={null} />);

      expect(container.firstChild).toBeNull();
    });
  });

  describe('Percentage Formatting', () => {
    it('should round percentage to 1 decimal place', async () => {
      mockGetTokenUsage.mockResolvedValue({
        ...mockUsageData,
        usage_percent: 3.456,
      });

      render(<TokenUsage conversationId={mockConversationId} />);

      await waitFor(() => {
        expect(screen.getByText('3.5%')).toBeInTheDocument();
      });
    });

    it('should handle zero percent', async () => {
      mockGetTokenUsage.mockResolvedValue({
        ...mockUsageData,
        total_tokens: 0,
        usage_percent: 0,
      });

      render(<TokenUsage conversationId={mockConversationId} />);

      await waitFor(() => {
        expect(screen.getByText('0.0%')).toBeInTheDocument();
      });
    });

    it('should handle 100 percent', async () => {
      mockGetTokenUsage.mockResolvedValue({
        ...mockUsageData,
        total_tokens: 32768,
        usage_percent: 100,
        is_critical: true,
      });

      render(<TokenUsage conversationId={mockConversationId} />);

      await waitFor(() => {
        expect(screen.getByText('100.0%')).toBeInTheDocument();
      });
    });
  });

  describe('Accessibility', () => {
    it('should have descriptive text labels', async () => {
      mockGetTokenUsage.mockResolvedValue(mockUsageData);

      render(<TokenUsage conversationId={mockConversationId} />);

      await waitFor(() => {
        expect(screen.getByText('Context')).toBeInTheDocument();
      });
    });

    it('should render warning icon with proper SVG attributes', async () => {
      mockGetTokenUsage.mockResolvedValue({
        ...mockUsageData,
        is_warning: true,
      });

      const { container } = render(<TokenUsage conversationId={mockConversationId} />);

      await waitFor(() => {
        const svg = container.querySelector('svg');
        expect(svg).toHaveAttribute('fill', 'currentColor');
        expect(svg).toHaveAttribute('viewBox', '0 0 20 20');
      });
    });
  });

  describe('Edge Cases', () => {
    it('should handle very small token counts', async () => {
      mockGetTokenUsage.mockResolvedValue({
        ...mockUsageData,
        total_tokens: 1,
        usage_percent: 0.003,
      });

      render(<TokenUsage conversationId={mockConversationId} />);

      await waitFor(() => {
        expect(screen.getByText('1')).toBeInTheDocument();
        expect(screen.getByText('0.0%')).toBeInTheDocument();
      });
    });

    it('should handle very large token counts', async () => {
      mockGetTokenUsage.mockResolvedValue({
        ...mockUsageData,
        total_tokens: 1000000,
        limit: 2000000,
        usage_percent: 50,
      });

      render(<TokenUsage conversationId={mockConversationId} />);

      await waitFor(() => {
        expect(screen.getByText('1,000,000')).toBeInTheDocument();
        expect(screen.getByText('2,000,000')).toBeInTheDocument();
      });
    });

    it('should handle empty string conversationId as falsy', () => {
      const { container } = render(<TokenUsage conversationId="" />);

      expect(container.firstChild).toBeNull();
    });
  });
});
