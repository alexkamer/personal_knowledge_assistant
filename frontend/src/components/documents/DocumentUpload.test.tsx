/**
 * Tests for DocumentUpload component
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@/test/utils';
import userEvent from '@testing-library/user-event';
import { DocumentUpload } from './DocumentUpload';
import * as useDocumentsHook from '@/hooks/useDocuments';

// Mock the useUploadDocument hook
vi.mock('@/hooks/useDocuments', () => ({
  useUploadDocument: vi.fn(),
}));

describe('DocumentUpload', () => {
  const mockMutateAsync = vi.fn();
  const mockUploadDocument = {
    mutateAsync: mockMutateAsync,
    isPending: false,
    isError: false,
    isSuccess: false,
    reset: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(useDocumentsHook, 'useUploadDocument').mockReturnValue(mockUploadDocument as any);
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
        expect(dropZone.className).toContain('border-blue-500');
        expect(dropZone.className).toContain('bg-blue-50');
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
        expect(dropZone.className).toContain('border-stone-300');
        expect(dropZone.className).toContain('bg-white');
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

      expect(screen.getByText('Uploading...')).toBeInTheDocument();
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

      expect(screen.getByText('Document uploaded successfully!')).toBeInTheDocument();
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
});
