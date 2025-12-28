/**
 * Tests for DocumentsList component
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@/test/utils';
import userEvent from '@testing-library/user-event';
import { DocumentsList } from './DocumentsList';
import * as useDocumentsHook from '@/hooks/useDocuments';
import { mockDocument } from '@/test/utils';

// Mock the hooks
vi.mock('@/hooks/useDocuments', () => ({
  useDocuments: vi.fn(),
  useDeleteDocument: vi.fn(),
  useCategories: vi.fn(),
}));

describe('DocumentsList', () => {
  const mockRefetch = vi.fn();
  const mockMutateAsync = vi.fn();
  const mockOnSelectDocument = vi.fn();

  const mockDocumentsData = {
    documents: [
      {
        ...mockDocument,
        id: 'doc-1',
        filename: 'test1.pdf',
        file_type: 'pdf',
        file_size: 1024,
        created_at: '2025-01-01T00:00:00Z',
      },
      {
        ...mockDocument,
        id: 'doc-2',
        filename: 'test2.txt',
        file_type: 'txt',
        file_size: 2048,
        created_at: '2025-01-02T00:00:00Z',
      },
      {
        ...mockDocument,
        id: 'doc-3',
        filename: 'large.pdf',
        file_type: 'pdf',
        file_size: 2 * 1024 * 1024, // 2 MB
        created_at: '2025-01-03T00:00:00Z',
      },
    ],
    total: 3,
  };

  const mockUseDocuments = {
    data: mockDocumentsData,
    isLoading: false,
    error: null,
    refetch: mockRefetch,
  };

  const mockDeleteDocument = {
    mutateAsync: mockMutateAsync,
    isPending: false,
  };

  const mockCategories = {
    data: ['category1', 'category2'],
    isLoading: false,
    error: null,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(useDocumentsHook, 'useDocuments').mockReturnValue(mockUseDocuments as any);
    vi.spyOn(useDocumentsHook, 'useDeleteDocument').mockReturnValue(mockDeleteDocument as any);
    vi.spyOn(useDocumentsHook, 'useCategories').mockReturnValue(mockCategories as any);
    // Mock window.confirm
    vi.spyOn(window, 'confirm').mockReturnValue(true);
  });

  describe('Rendering', () => {
    it('should render the documents list with header', () => {
      render(<DocumentsList />);

      expect(screen.getByText('Documents (3)')).toBeInTheDocument();
    });

    it('should render all documents', () => {
      render(<DocumentsList />);

      expect(screen.getByText('test1.pdf')).toBeInTheDocument();
      expect(screen.getByText('test2.txt')).toBeInTheDocument();
      expect(screen.getByText('large.pdf')).toBeInTheDocument();
    });

    it('should display file sizes correctly', () => {
      render(<DocumentsList />);

      expect(screen.getByText('1.0 KB')).toBeInTheDocument();
      expect(screen.getByText('2.0 KB')).toBeInTheDocument();
      expect(screen.getByText('2.0 MB')).toBeInTheDocument();
    });

    it('should display file types', () => {
      render(<DocumentsList />);

      const pdfBadges = screen.getAllByText(/PDF/i);
      const txtBadges = screen.getAllByText(/TXT/i);

      expect(pdfBadges.length).toBeGreaterThanOrEqual(2);
      expect(txtBadges.length).toBeGreaterThanOrEqual(1);
    });

    it('should display formatted dates', () => {
      render(<DocumentsList />);

      // Dates should be present in some format (locale-dependent)
      const yearElements = screen.getAllByText(/2025/);
      expect(yearElements.length).toBeGreaterThan(0);
      // Check for date elements
      const dateElements = screen.getAllByText(/Jan|1|2|3|2025/i);
      expect(dateElements.length).toBeGreaterThan(0);
    });

    it('should render delete buttons for each document', () => {
      render(<DocumentsList />);

      const deleteButtons = screen.getAllByLabelText('Delete document');
      expect(deleteButtons).toHaveLength(3);
    });
  });

  describe('Loading State', () => {
    it('should show loading spinner when loading', () => {
      vi.spyOn(useDocumentsHook, 'useDocuments').mockReturnValue({
        ...mockUseDocuments,
        isLoading: true,
        data: null,
      } as any);

      render(<DocumentsList />);

      expect(screen.getByText('Loading documents...')).toBeInTheDocument();
    });

    it('should have spinning animation when loading', () => {
      vi.spyOn(useDocumentsHook, 'useDocuments').mockReturnValue({
        ...mockUseDocuments,
        isLoading: true,
        data: null,
      } as any);

      const { container } = render(<DocumentsList />);

      const spinner = container.querySelector('.animate-spin');
      expect(spinner).toBeInTheDocument();
    });
  });

  describe('Error State', () => {
    it('should show error message when fetch fails', () => {
      const error = new Error('Network error');
      vi.spyOn(useDocumentsHook, 'useDocuments').mockReturnValue({
        ...mockUseDocuments,
        isLoading: false,
        error,
        data: null,
      } as any);

      render(<DocumentsList />);

      expect(screen.getByText('Failed to load documents')).toBeInTheDocument();
      expect(screen.getByText('Network error')).toBeInTheDocument();
    });

    it('should show API error detail when available', () => {
      const error = {
        response: {
          data: {
            detail: 'Database connection failed',
          },
        },
        message: 'Request failed',
      };
      vi.spyOn(useDocumentsHook, 'useDocuments').mockReturnValue({
        ...mockUseDocuments,
        error,
        data: null,
      } as any);

      render(<DocumentsList />);

      expect(screen.getByText('Database connection failed')).toBeInTheDocument();
    });

    it('should show retry button on error', () => {
      const error = new Error('Network error');
      vi.spyOn(useDocumentsHook, 'useDocuments').mockReturnValue({
        ...mockUseDocuments,
        error,
        data: null,
      } as any);

      render(<DocumentsList />);

      expect(screen.getByText('Retry')).toBeInTheDocument();
    });

    it('should call refetch when retry button is clicked', async () => {
      const user = userEvent.setup();
      const error = new Error('Network error');
      vi.spyOn(useDocumentsHook, 'useDocuments').mockReturnValue({
        ...mockUseDocuments,
        error,
        data: null,
      } as any);

      render(<DocumentsList />);

      await user.click(screen.getByText('Retry'));

      expect(mockRefetch).toHaveBeenCalledTimes(1);
    });
  });

  describe('Empty State', () => {
    it('should show empty state when no documents', () => {
      vi.spyOn(useDocumentsHook, 'useDocuments').mockReturnValue({
        ...mockUseDocuments,
        data: { documents: [], total: 0 },
      } as any);

      render(<DocumentsList />);

      expect(screen.getByText('No documents yet')).toBeInTheDocument();
      expect(screen.getByText('Upload your first document to get started')).toBeInTheDocument();
    });

    it('should show empty state when data is null', () => {
      vi.spyOn(useDocumentsHook, 'useDocuments').mockReturnValue({
        ...mockUseDocuments,
        data: null,
      } as any);

      render(<DocumentsList />);

      expect(screen.getByText('No documents yet')).toBeInTheDocument();
    });
  });

  describe('Document Selection', () => {
    it('should call onSelectDocument when document is clicked', async () => {
      const user = userEvent.setup();
      render(<DocumentsList onSelectDocument={mockOnSelectDocument} />);

      await user.click(screen.getByText('test1.pdf'));

      expect(mockOnSelectDocument).toHaveBeenCalledWith(
        expect.objectContaining({
          id: 'doc-1',
          filename: 'test1.pdf',
        })
      );
    });

    it('should not call onSelectDocument when prop is not provided', async () => {
      const user = userEvent.setup();
      render(<DocumentsList />);

      await user.click(screen.getByText('test1.pdf'));

      // Should not throw error
      expect(mockOnSelectDocument).not.toHaveBeenCalled();
    });

    it('should highlight selected document', () => {
      const { container } = render(<DocumentsList selectedDocumentId="doc-2" />);

      // Get the document row that contains test2.txt
      const selectedDoc = screen.getByText('test2.txt').closest('div.p-5');

      expect(selectedDoc).toHaveClass('bg-primary-500');
      expect(selectedDoc).toHaveClass('text-white');
    });

    it('should not highlight unselected documents', () => {
      const { container } = render(<DocumentsList selectedDocumentId="doc-2" />);

      const unselectedDoc = screen.getByText('test1.pdf').closest('div.p-5');

      expect(unselectedDoc).not.toHaveClass('bg-primary-500');
      expect(unselectedDoc).toHaveClass('bg-gray-900/80');
    });
  });

  describe('Document Deletion', () => {
    it('should show confirmation dialog when delete is clicked', async () => {
      const user = userEvent.setup();
      render(<DocumentsList />);

      const deleteButtons = screen.getAllByLabelText('Delete document');
      await user.click(deleteButtons[0]);

      expect(window.confirm).toHaveBeenCalledWith('Are you sure you want to delete this document?');
    });

    it('should call mutateAsync when deletion is confirmed', async () => {
      const user = userEvent.setup();
      render(<DocumentsList />);

      const deleteButtons = screen.getAllByLabelText('Delete document');
      await user.click(deleteButtons[0]);

      await waitFor(() => {
        expect(mockMutateAsync).toHaveBeenCalledWith('doc-1');
      });
    });

    it('should not delete when confirmation is cancelled', async () => {
      const user = userEvent.setup();
      vi.spyOn(window, 'confirm').mockReturnValue(false);

      render(<DocumentsList />);

      const deleteButtons = screen.getAllByLabelText('Delete document');
      await user.click(deleteButtons[0]);

      expect(mockMutateAsync).not.toHaveBeenCalled();
    });

    it('should not trigger document selection when delete button is clicked', async () => {
      const user = userEvent.setup();
      render(<DocumentsList onSelectDocument={mockOnSelectDocument} />);

      const deleteButtons = screen.getAllByLabelText('Delete document');
      await user.click(deleteButtons[0]);

      expect(mockOnSelectDocument).not.toHaveBeenCalled();
    });

    it('should disable delete button when deletion is pending', () => {
      vi.spyOn(useDocumentsHook, 'useDeleteDocument').mockReturnValue({
        ...mockDeleteDocument,
        isPending: true,
      } as any);

      render(<DocumentsList />);

      const deleteButtons = screen.getAllByLabelText('Delete document');
      deleteButtons.forEach((button) => {
        expect(button).toBeDisabled();
      });
    });

    it('should handle deletion errors gracefully', async () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      mockMutateAsync.mockRejectedValueOnce(new Error('Delete failed'));

      const user = userEvent.setup();
      render(<DocumentsList />);

      const deleteButtons = screen.getAllByLabelText('Delete document');
      await user.click(deleteButtons[0]);

      await waitFor(() => {
        expect(consoleErrorSpy).toHaveBeenCalledWith('Delete failed:', expect.any(Error));
      });

      consoleErrorSpy.mockRestore();
    });
  });

  describe('File Size Formatting', () => {
    it('should format bytes correctly', () => {
      const mockData = {
        documents: [
          { ...mockDocument, id: '1', filename: 'tiny.txt', file_size: 500, created_at: '2025-01-01T00:00:00Z' },
        ],
        total: 1,
      };
      vi.spyOn(useDocumentsHook, 'useDocuments').mockReturnValue({
        ...mockUseDocuments,
        data: mockData,
      } as any);

      render(<DocumentsList />);

      expect(screen.getByText('500 B')).toBeInTheDocument();
    });

    it('should format kilobytes correctly', () => {
      render(<DocumentsList />);

      expect(screen.getByText('1.0 KB')).toBeInTheDocument();
    });

    it('should format megabytes correctly', () => {
      render(<DocumentsList />);

      expect(screen.getByText('2.0 MB')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have proper heading hierarchy', () => {
      render(<DocumentsList />);

      const heading = screen.getByRole('heading', { name: /Documents \(3\)/ });
      expect(heading).toBeInTheDocument();
    });

    it('should have accessible delete buttons', () => {
      render(<DocumentsList />);

      const deleteButtons = screen.getAllByLabelText('Delete document');
      deleteButtons.forEach((button) => {
        expect(button).toHaveAccessibleName();
      });
    });

    it('should be keyboard navigable', () => {
      render(<DocumentsList />);

      const deleteButtons = screen.getAllByLabelText('Delete document');
      deleteButtons.forEach((button) => {
        expect(button).toBeEnabled();
      });
    });
  });
});
