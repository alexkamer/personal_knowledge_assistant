/**
 * Tests for ErrorBoundary component
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@/test/utils';
import userEvent from '@testing-library/user-event';
import ErrorBoundary from './ErrorBoundary';

// Component that throws an error
function ThrowError({ shouldThrow }: { shouldThrow?: boolean }) {
  if (shouldThrow) {
    throw new Error('Test error');
  }
  return <div>No error</div>;
}

describe('ErrorBoundary', () => {
  let consoleErrorSpy: any;

  beforeEach(() => {
    // Mock console.error to avoid cluttering test output
    consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    consoleErrorSpy.mockRestore();
  });

  describe('Normal Rendering', () => {
    it('should render children when there is no error', () => {
      render(
        <ErrorBoundary>
          <div>Test content</div>
        </ErrorBoundary>
      );

      expect(screen.getByText('Test content')).toBeInTheDocument();
    });

    it('should not show error UI when children render successfully', () => {
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={false} />
        </ErrorBoundary>
      );

      expect(screen.getByText('No error')).toBeInTheDocument();
      expect(screen.queryByText('Something went wrong')).not.toBeInTheDocument();
    });
  });

  describe('Error Handling', () => {
    it('should catch errors and display error UI', () => {
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      );

      expect(screen.getByText('Something went wrong')).toBeInTheDocument();
      expect(screen.queryByText('No error')).not.toBeInTheDocument();
    });

    it('should log errors to console', () => {
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      );

      expect(consoleErrorSpy).toHaveBeenCalled();
    });

    it('should display custom fallback title', () => {
      render(
        <ErrorBoundary fallbackTitle="Custom Error Title">
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      );

      expect(screen.getByText('Custom Error Title')).toBeInTheDocument();
    });

    it('should display default fallback title when not provided', () => {
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      );

      expect(screen.getByText('Something went wrong')).toBeInTheDocument();
    });
  });

  describe('Error UI Elements', () => {
    it('should display error icon', () => {
      const { container } = render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      );

      // AlertTriangle icon should be present
      const icon = container.querySelector('.text-red-600');
      expect(icon).toBeInTheDocument();
    });

    it('should display error message', () => {
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      );

      expect(
        screen.getByText(/An unexpected error occurred/i)
      ).toBeInTheDocument();
    });

    it('should display Try Again button', () => {
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      );

      expect(screen.getByText('Try Again')).toBeInTheDocument();
    });

    it('should display Reload Page button', () => {
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      );

      expect(screen.getByText('Reload Page')).toBeInTheDocument();
    });
  });

  describe('Development Mode Error Details', () => {
    it('should show error details in development mode', () => {
      // Set DEV mode
      vi.stubEnv('DEV', true);

      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      );

      expect(screen.getByText(/Test error/)).toBeInTheDocument();

      vi.unstubAllEnvs();
    });

    it('should show stack trace in development mode', () => {
      vi.stubEnv('DEV', true);

      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      );

      expect(screen.getByText('Stack trace')).toBeInTheDocument();

      vi.unstubAllEnvs();
    });

    it('should not show error details in production mode', () => {
      vi.stubEnv('DEV', false);

      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      );

      expect(screen.queryByText(/Test error/)).not.toBeInTheDocument();

      vi.unstubAllEnvs();
    });
  });

  describe('Reset Functionality', () => {
    it('should reset error state when Try Again is clicked', async () => {
      const user = userEvent.setup();
      let shouldThrow = true;

      function ToggleError() {
        if (shouldThrow) {
          throw new Error('Test error');
        }
        return <div>Success</div>;
      }

      render(
        <ErrorBoundary>
          <ToggleError />
        </ErrorBoundary>
      );

      expect(screen.getByText('Something went wrong')).toBeInTheDocument();

      // Change error condition
      shouldThrow = false;

      const tryAgainButton = screen.getByText('Try Again');
      await user.click(tryAgainButton);

      await waitFor(() => {
        expect(screen.getByText('Success')).toBeInTheDocument();
      });
    });

    it('should call onReset callback when provided', async () => {
      const user = userEvent.setup();
      const mockOnReset = vi.fn();

      render(
        <ErrorBoundary onReset={mockOnReset}>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      );

      const tryAgainButton = screen.getByText('Try Again');
      await user.click(tryAgainButton);

      expect(mockOnReset).toHaveBeenCalledTimes(1);
    });

    it('should not throw when onReset is not provided', async () => {
      const user = userEvent.setup();

      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      );

      const tryAgainButton = screen.getByText('Try Again');
      await user.click(tryAgainButton);

      // Should not throw error
      expect(screen.getByText('Something went wrong')).toBeInTheDocument();
    });
  });

  describe('Reload Functionality', () => {
    it('should reload page when Reload Page button is clicked', async () => {
      const user = userEvent.setup();
      const mockReload = vi.fn();
      Object.defineProperty(window, 'location', {
        value: { reload: mockReload },
        writable: true,
      });

      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      );

      const reloadButton = screen.getByText('Reload Page');
      await user.click(reloadButton);

      expect(mockReload).toHaveBeenCalledTimes(1);
    });
  });

  describe('Styling and Layout', () => {
    it('should apply correct container styles', () => {
      const { container } = render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      );

      const errorContainer = container.querySelector('.min-h-\\[400px\\]');
      expect(errorContainer).toBeInTheDocument();
    });

    it('should apply button styles', () => {
      const { container } = render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      );

      const tryAgainButton = container.querySelector('.bg-blue-600');
      expect(tryAgainButton).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('should handle errors thrown during rendering', () => {
      function ThrowDuringRender() {
        throw new Error('Rendering error');
      }

      render(
        <ErrorBoundary>
          <ThrowDuringRender />
        </ErrorBoundary>
      );

      expect(screen.getByText('Something went wrong')).toBeInTheDocument();
    });

    it('should handle multiple children', () => {
      render(
        <ErrorBoundary>
          <div>Child 1</div>
          <div>Child 2</div>
        </ErrorBoundary>
      );

      expect(screen.getByText('Child 1')).toBeInTheDocument();
      expect(screen.getByText('Child 2')).toBeInTheDocument();
    });

    it('should handle nested error boundaries', () => {
      render(
        <ErrorBoundary fallbackTitle="Outer Error">
          <ErrorBoundary fallbackTitle="Inner Error">
            <ThrowError shouldThrow={true} />
          </ErrorBoundary>
        </ErrorBoundary>
      );

      // Inner boundary should catch the error
      expect(screen.getByText('Inner Error')).toBeInTheDocument();
      expect(screen.queryByText('Outer Error')).not.toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have accessible button elements', () => {
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      );

      const tryAgainButton = screen.getByText('Try Again');
      const reloadButton = screen.getByText('Reload Page');

      expect(tryAgainButton.tagName).toBe('BUTTON');
      expect(reloadButton.tagName).toBe('BUTTON');
    });

    it('should have readable error messages', () => {
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      );

      const errorMessage = screen.getByText(/An unexpected error occurred/i);
      expect(errorMessage).toBeInTheDocument();
    });
  });
});
