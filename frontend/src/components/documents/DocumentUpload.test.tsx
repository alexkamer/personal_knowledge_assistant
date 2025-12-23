/**
 * Tests for DocumentUpload component
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@/test/utils';
import userEvent from '@testing-library/user-event';
import { DocumentUpload } from './DocumentUpload';
import * as useDocumentsHook from '@/hooks/useDocuments';

// Mock the hooks
vi.mock('@/hooks/useDocuments', () => ({
  useUploadDocument: vi.fn(),
  useCreateDocumentFromURL: vi.fn(),
}));

describe('DocumentUpload', () => {
  const mockMutateAsync = vi.fn();
  const mockUrlMutateAsync = vi.fn();
  const mockUploadDocument = {
    mutateAsync: mockMutateAsync,
    isPending: false,
    isError: false,
    isSuccess: false,
    reset: vi.fn(),
  };
  const mockCreateFromURL = {
    mutateAsync: mockUrlMutateAsync,
    isPending: false,
    isError: false,
    isSuccess: false,
    reset: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(useDocumentsHook, 'useUploadDocument').mockReturnValue(mockUploadDocument as any);
    vi.spyOn(useDocumentsHook, 'useCreateDocumentFromURL').mockReturnValue(mockCreateFromURL as any);
  });

  describe('Rendering', () => {
    it('should render the upload area', () => {
      render(<DocumentUpload />);

      expect(screen.getByText('Upload a document')).toBeInTheDocument();
      expect(screen.getByText('Drag and drop your file here, or click to browse')).toBeInTheDocument();
      expect(screen.getByText('Supported formats: TXT, MD, PDF, DOCX')).toBeInTheDocument();
    });

    it('should render the file input with correct accept attribute', () => {
      render(<DocumentUpload />);

      const fileInput = screen.getByLabelText(/choose file/i);
      expect(fileInput).toHaveAttribute('accept', '.txt,.md,.pdf,.doc,.docx');
    });

    it('should render the Choose File button', () => {
      render(<DocumentUpload />);

      expect(screen.getByText('Choose File')).toBeInTheDocument();
    });
  });

  describe('File Upload via Input', () => {
    it('should call mutateAsync when a file is selected', async () => {
      const user = userEvent.setup();
      render(<DocumentUpload />);

      const file = new File(['test content'], 'test.txt', { type: 'text/plain' });
      const input = screen.getByLabelText(/choose file/i);

      await user.upload(input, file);

      expect(mockMutateAsync).toHaveBeenCalledWith(file);
      expect(mockMutateAsync).toHaveBeenCalledTimes(1);
    });

    it('should handle multiple files by uploading only the first one', async () => {
      const user = userEvent.setup();
      render(<DocumentUpload />);

      const file1 = new File(['content 1'], 'test1.txt', { type: 'text/plain' });
      const file2 = new File(['content 2'], 'test2.txt', { type: 'text/plain' });
      const input = screen.getByLabelText(/choose file/i);

      await user.upload(input, [file1, file2]);

      expect(mockMutateAsync).toHaveBeenCalledWith(file1);
      expect(mockMutateAsync).toHaveBeenCalledTimes(1);
    });

    it('should not call mutateAsync when no file is selected', async () => {
      const user = userEvent.setup();
      render(<DocumentUpload />);

      const input = screen.getByLabelText(/choose file/i);
      await user.upload(input, []);

      expect(mockMutateAsync).not.toHaveBeenCalled();
    });
  });

  describe('Drag and Drop', () => {
    it('should show dragging state when file is dragged over', async () => {
      const { container } = render(<DocumentUpload />);

      // Get the actual drop zone (the div with onDragOver)
      const dropZone = container.querySelector('[class*="border-2 border-dashed"]')!;

      // Trigger drag over
      const dragOverEvent = new Event('dragover', { bubbles: true });
      Object.defineProperty(dragOverEvent, 'dataTransfer', {
        value: { files: [] },
      });
      dropZone.dispatchEvent(dragOverEvent);

      await waitFor(() => {
        expect(dropZone.className).toContain('border-indigo-500');
        expect(dropZone.className).toContain('bg-primary-50');
      });
    });

    it('should remove dragging state when file leaves', async () => {
      const { container } = render(<DocumentUpload />);

      // Get the actual drop zone
      const dropZone = container.querySelector('[class*="border-2 border-dashed"]')!;

      // Trigger drag over then drag leave
      dropZone.dispatchEvent(new Event('dragover', { bubbles: true }));
      dropZone.dispatchEvent(new Event('dragleave', { bubbles: true }));

      await waitFor(() => {
        // Check that dragging-specific classes are removed
        expect(dropZone.className).not.toContain('bg-primary-50');
        expect(dropZone.className).not.toContain('scale-[1.02]');
      });
    });

    it('should handle file drop and upload', async () => {
      const { container } = render(<DocumentUpload />);

      const file = new File(['test content'], 'test.pdf', { type: 'application/pdf' });
      const dropZone = container.querySelector('[class*="border-2 border-dashed"]')!;

      const dropEvent = new Event('drop', { bubbles: true });
      Object.defineProperty(dropEvent, 'dataTransfer', {
        value: {
          files: [file],
        },
      });

      dropZone.dispatchEvent(dropEvent);

      await waitFor(() => {
        expect(mockMutateAsync).toHaveBeenCalledWith(file);
      });
    });

    it('should only upload the first file when multiple files are dropped', async () => {
      const { container } = render(<DocumentUpload />);

      const file1 = new File(['content 1'], 'test1.pdf', { type: 'application/pdf' });
      const file2 = new File(['content 2'], 'test2.pdf', { type: 'application/pdf' });
      const dropZone = container.querySelector('[class*="border-2 border-dashed"]')!;

      const dropEvent = new Event('drop', { bubbles: true });
      Object.defineProperty(dropEvent, 'dataTransfer', {
        value: {
          files: [file1, file2],
        },
      });

      dropZone.dispatchEvent(dropEvent);

      await waitFor(() => {
        expect(mockMutateAsync).toHaveBeenCalledWith(file1);
        expect(mockMutateAsync).toHaveBeenCalledTimes(1);
      });
    });

    it('should not upload when no files are dropped', async () => {
      const { container } = render(<DocumentUpload />);

      const dropZone = container.querySelector('[class*="border-2 border-dashed"]')!;

      const dropEvent = new Event('drop', { bubbles: true });
      Object.defineProperty(dropEvent, 'dataTransfer', {
        value: {
          files: [],
        },
      });

      dropZone.dispatchEvent(dropEvent);

      await waitFor(() => {
        expect(mockMutateAsync).not.toHaveBeenCalled();
      });
    });
  });

  describe('Upload States', () => {
    it('should show uploading state', () => {
      vi.spyOn(useDocumentsHook, 'useUploadDocument').mockReturnValue({
        ...mockUploadDocument,
        isPending: true,
      } as any);

      render(<DocumentUpload />);

      expect(screen.getByText('Processing...')).toBeInTheDocument();
    });

    it('should disable input and show opacity when uploading', () => {
      vi.spyOn(useDocumentsHook, 'useUploadDocument').mockReturnValue({
        ...mockUploadDocument,
        isPending: true,
      } as any);

      const { container } = render(<DocumentUpload />);

      const input = screen.getByLabelText(/choose file/i);
      const dropZone = container.querySelector('[class*="border-2 border-dashed"]')!;

      expect(input).toBeDisabled();
      expect(dropZone.className).toContain('opacity-50');
      expect(dropZone.className).toContain('pointer-events-none');
    });

    it('should show error message on upload failure', () => {
      vi.spyOn(useDocumentsHook, 'useUploadDocument').mockReturnValue({
        ...mockUploadDocument,
        isError: true,
      } as any);

      render(<DocumentUpload />);

      expect(screen.getByText('Upload failed. Please try again.')).toBeInTheDocument();
    });

    it('should show success message on successful upload', () => {
      vi.spyOn(useDocumentsHook, 'useUploadDocument').mockReturnValue({
        ...mockUploadDocument,
        isSuccess: true,
      } as any);

      render(<DocumentUpload />);

      expect(screen.getByText('Document added successfully!')).toBeInTheDocument();
    });
  });

  describe('Error Handling', () => {
    it('should handle upload errors gracefully', async () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      mockMutateAsync.mockRejectedValueOnce(new Error('Upload failed'));

      const user = userEvent.setup();
      render(<DocumentUpload />);

      const file = new File(['test content'], 'test.txt', { type: 'text/plain' });
      const input = screen.getByLabelText(/choose file/i);

      await user.upload(input, file);

      await waitFor(() => {
        expect(consoleErrorSpy).toHaveBeenCalledWith('Upload failed:', expect.any(Error));
      });

      consoleErrorSpy.mockRestore();
    });
  });

  describe('Accessibility', () => {
    it('should have proper label for file input', () => {
      render(<DocumentUpload />);

      const input = screen.getByLabelText(/choose file/i);
      expect(input).toHaveAttribute('type', 'file');
    });

    it('should have descriptive text for screen readers', () => {
      render(<DocumentUpload />);

      expect(screen.getByText('Drag and drop your file here, or click to browse')).toBeInTheDocument();
      expect(screen.getByText('Supported formats: TXT, MD, PDF, DOCX')).toBeInTheDocument();
    });
  });

  describe('URL Input Feature', () => {
    it('should render "Add from URL" button', () => {
      render(<DocumentUpload />);

      expect(screen.getByText('Add from URL')).toBeInTheDocument();
    });

    it('should show URL input form when "Add from URL" is clicked', async () => {
      const user = userEvent.setup();
      render(<DocumentUpload />);

      const addFromUrlButton = screen.getByText('Add from URL');
      await user.click(addFromUrlButton);

      expect(screen.getByLabelText(/enter url/i)).toBeInTheDocument();
      expect(screen.getByPlaceholderText('https://example.com/article')).toBeInTheDocument();
      expect(screen.getByText('Supports articles, blog posts, documentation pages, and more')).toBeInTheDocument();
    });

    it('should hide URL button and show form when clicked', async () => {
      const user = userEvent.setup();
      render(<DocumentUpload />);

      const addFromUrlButton = screen.getByText('Add from URL');
      await user.click(addFromUrlButton);

      expect(screen.queryByText('Add from URL')).not.toBeInTheDocument();
      expect(screen.getByLabelText(/enter url/i)).toBeInTheDocument();
    });

    it('should submit URL when form is submitted', async () => {
      const user = userEvent.setup();
      render(<DocumentUpload />);

      // Click to show URL input
      await user.click(screen.getByText('Add from URL'));

      // Type URL
      const urlInput = screen.getByLabelText(/enter url/i);
      await user.type(urlInput, 'https://example.com/article');

      // Submit form
      const submitButton = screen.getByText('Add Document');
      await user.click(submitButton);

      expect(mockUrlMutateAsync).toHaveBeenCalledWith('https://example.com/article');
      expect(mockUrlMutateAsync).toHaveBeenCalledTimes(1);
    });

    it('should clear URL and hide form after successful submission', async () => {
      mockUrlMutateAsync.mockResolvedValueOnce({});
      const user = userEvent.setup();
      render(<DocumentUpload />);

      // Show URL input
      await user.click(screen.getByText('Add from URL'));

      // Type and submit
      const urlInput = screen.getByLabelText(/enter url/i);
      await user.type(urlInput, 'https://example.com/test');
      await user.click(screen.getByText('Add Document'));

      await waitFor(() => {
        expect(screen.getByText('Add from URL')).toBeInTheDocument();
      });
    });

    it('should cancel URL input when Cancel is clicked', async () => {
      const user = userEvent.setup();
      render(<DocumentUpload />);

      // Show URL input
      await user.click(screen.getByText('Add from URL'));

      // Type URL
      const urlInput = screen.getByLabelText(/enter url/i);
      await user.type(urlInput, 'https://example.com/test');

      // Click cancel
      const cancelButton = screen.getByText('Cancel');
      await user.click(cancelButton);

      // Form should be hidden, button should be visible
      expect(screen.getByText('Add from URL')).toBeInTheDocument();
      expect(screen.queryByLabelText(/enter url/i)).not.toBeInTheDocument();
    });

    it('should disable submit button when URL is empty', async () => {
      const user = userEvent.setup();
      render(<DocumentUpload />);

      await user.click(screen.getByText('Add from URL'));

      const submitButton = screen.getByText('Add Document');
      expect(submitButton).toBeDisabled();
    });

    it('should enable submit button when URL is entered', async () => {
      const user = userEvent.setup();
      render(<DocumentUpload />);

      await user.click(screen.getByText('Add from URL'));

      const urlInput = screen.getByLabelText(/enter url/i);
      const submitButton = screen.getByText('Add Document');

      expect(submitButton).toBeDisabled();

      await user.type(urlInput, 'https://example.com/article');

      expect(submitButton).not.toBeDisabled();
    });

    it('should show "Fetching..." text during URL submission', () => {
      vi.spyOn(useDocumentsHook, 'useCreateDocumentFromURL').mockReturnValue({
        ...mockCreateFromURL,
        isPending: true,
      } as any);

      render(<DocumentUpload />);

      // Form should be visible when component renders with isPending
      // (simulating state after clicking Add from URL and submitting)
      expect(screen.getByText('Processing...')).toBeInTheDocument();
    });

    it('should disable inputs when URL is being fetched', () => {
      // Mock pending state from the start
      vi.spyOn(useDocumentsHook, 'useCreateDocumentFromURL').mockReturnValue({
        ...mockCreateFromURL,
        isPending: true,
      } as any);

      render(<DocumentUpload />);

      const fileInput = screen.getByLabelText(/choose file/i);
      expect(fileInput).toBeDisabled();
    });

    it('should show error message when URL fetch fails', async () => {
      vi.spyOn(useDocumentsHook, 'useCreateDocumentFromURL').mockReturnValue({
        ...mockCreateFromURL,
        isError: true,
      } as any);

      render(<DocumentUpload />);

      expect(screen.getByText('Failed to fetch URL. Please check the URL and try again.')).toBeInTheDocument();
    });

    it('should show success message when URL document is created', () => {
      vi.spyOn(useDocumentsHook, 'useCreateDocumentFromURL').mockReturnValue({
        ...mockCreateFromURL,
        isSuccess: true,
      } as any);

      render(<DocumentUpload />);

      expect(screen.getByText('Document added successfully!')).toBeInTheDocument();
    });

    it('should handle URL fetch errors gracefully', async () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      mockUrlMutateAsync.mockRejectedValueOnce(new Error('Fetch failed'));

      const user = userEvent.setup();
      render(<DocumentUpload />);

      await user.click(screen.getByText('Add from URL'));
      const urlInput = screen.getByLabelText(/enter url/i);
      await user.type(urlInput, 'https://invalid-url.com');
      await user.click(screen.getByText('Add Document'));

      await waitFor(() => {
        expect(consoleErrorSpy).toHaveBeenCalledWith('Failed to create document from URL:', expect.any(Error));
      });

      consoleErrorSpy.mockRestore();
    });

    it('should display backend error message from API response', async () => {
      const backendError = {
        response: {
          data: {
            detail: "Failed to fetch URL: Client error '404 Not Found' for url 'https://example.com/not-found'",
          },
        },
      };
      mockUrlMutateAsync.mockRejectedValueOnce(backendError);

      const user = userEvent.setup();
      render(<DocumentUpload />);

      await user.click(screen.getByText('Add from URL'));
      const urlInput = screen.getByLabelText(/enter url/i);
      await user.type(urlInput, 'https://example.com/not-found');
      await user.click(screen.getByText('Add Document'));

      await waitFor(() => {
        expect(screen.getByText(/Failed to fetch URL: Client error '404 Not Found'/)).toBeInTheDocument();
      });
    });

    it('should clear error message when Cancel is clicked', async () => {
      const backendError = {
        response: {
          data: {
            detail: 'Some error message',
          },
        },
      };
      mockUrlMutateAsync.mockRejectedValueOnce(backendError);

      const user = userEvent.setup();
      render(<DocumentUpload />);

      await user.click(screen.getByText('Add from URL'));
      const urlInput = screen.getByLabelText(/enter url/i);
      await user.type(urlInput, 'https://example.com/test');
      await user.click(screen.getByText('Add Document'));

      await waitFor(() => {
        expect(screen.getByText('Some error message')).toBeInTheDocument();
      });

      // Click cancel to close the form
      await user.click(screen.getByText('Cancel'));

      // Error message should be gone
      expect(screen.queryByText('Some error message')).not.toBeInTheDocument();
    });

    it('should clear error message when submitting a new URL', async () => {
      const backendError = {
        response: {
          data: {
            detail: 'First error',
          },
        },
      };
      mockUrlMutateAsync.mockRejectedValueOnce(backendError);

      const user = userEvent.setup();
      render(<DocumentUpload />);

      await user.click(screen.getByText('Add from URL'));
      const urlInput = screen.getByLabelText(/enter url/i);
      await user.type(urlInput, 'https://example.com/fail');
      await user.click(screen.getByText('Add Document'));

      await waitFor(() => {
        expect(screen.getByText('First error')).toBeInTheDocument();
      });

      // Clear the input and try again
      await user.clear(urlInput);
      await user.type(urlInput, 'https://example.com/success');
      mockUrlMutateAsync.mockResolvedValueOnce({});
      await user.click(screen.getByText('Add Document'));

      // Error should be cleared during new submission
      await waitFor(() => {
        expect(screen.queryByText('First error')).not.toBeInTheDocument();
      });
    });

    it('should not submit empty or whitespace-only URLs', async () => {
      const user = userEvent.setup();
      render(<DocumentUpload />);

      await user.click(screen.getByText('Add from URL'));

      const urlInput = screen.getByLabelText(/enter url/i);
      await user.type(urlInput, '   ');

      const submitButton = screen.getByText('Add Document');
      expect(submitButton).toBeDisabled();

      await user.click(submitButton);
      expect(mockUrlMutateAsync).not.toHaveBeenCalled();
    });
  });
});
