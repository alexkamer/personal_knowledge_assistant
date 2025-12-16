/**
 * Tests for documentService
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { documentService } from './documentService';
import { apiClient } from './api';
import type { Document, DocumentContent, DocumentListResponse } from '@/types/document';

// Mock the api module
vi.mock('./api', () => ({
  apiClient: {
    post: vi.fn(),
    get: vi.fn(),
    delete: vi.fn(),
  },
}));

describe('documentService', () => {
  const mockApiClient = vi.mocked(apiClient);

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('uploadDocument', () => {
    it('should upload a document file', async () => {
      const mockFile = new File(['content'], 'test.pdf', { type: 'application/pdf' });
      const mockDocument: Document = {
        id: 'doc-1',
        filename: 'test.pdf',
        file_type: 'pdf',
        file_size: 1024,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      };

      mockApiClient.post.mockResolvedValue({ data: mockDocument } as any);

      const result = await documentService.uploadDocument(mockFile);

      expect(mockApiClient.post).toHaveBeenCalledWith(
        '/documents/',
        expect.any(FormData),
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );
      expect(result).toEqual(mockDocument);
    });

    it('should handle upload errors', async () => {
      const mockFile = new File(['content'], 'test.pdf', { type: 'application/pdf' });
      const error = new Error('Upload failed');

      mockApiClient.post.mockRejectedValue(error);

      await expect(documentService.uploadDocument(mockFile)).rejects.toThrow('Upload failed');
    });

    it('should upload different file types', async () => {
      const mockFile = new File(['markdown content'], 'test.md', { type: 'text/markdown' });
      const mockDocument: Document = {
        id: 'doc-2',
        filename: 'test.md',
        file_type: 'md',
        file_size: 512,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      };

      mockApiClient.post.mockResolvedValue({ data: mockDocument } as any);

      const result = await documentService.uploadDocument(mockFile);

      expect(result.file_type).toBe('md');
    });
  });

  describe('getDocuments', () => {
    it('should fetch documents with default pagination', async () => {
      const mockResponse: DocumentListResponse = {
        documents: [
          {
            id: 'doc-1',
            filename: 'test1.pdf',
            file_type: 'pdf',
            file_size: 1024,
            created_at: '2024-01-01T00:00:00Z',
            updated_at: '2024-01-01T00:00:00Z',
          },
        ],
        total: 1,
      };

      mockApiClient.get.mockResolvedValue({ data: mockResponse } as any);

      const result = await documentService.getDocuments();

      expect(mockApiClient.get).toHaveBeenCalledWith('/documents/', {
        params: { skip: 0, limit: 100 },
      });
      expect(result).toEqual(mockResponse);
    });

    it('should fetch documents with custom pagination', async () => {
      const mockResponse: DocumentListResponse = {
        documents: [],
        total: 0,
      };

      mockApiClient.get.mockResolvedValue({ data: mockResponse } as any);

      await documentService.getDocuments(10, 50);

      expect(mockApiClient.get).toHaveBeenCalledWith('/documents/', {
        params: { skip: 10, limit: 50 },
      });
    });

    it('should handle empty document list', async () => {
      const mockResponse: DocumentListResponse = {
        documents: [],
        total: 0,
      };

      mockApiClient.get.mockResolvedValue({ data: mockResponse } as any);

      const result = await documentService.getDocuments();

      expect(result.documents).toEqual([]);
      expect(result.total).toBe(0);
    });

    it('should throw error on API failure', async () => {
      const error = new Error('Network Error');
      mockApiClient.get.mockRejectedValue(error);

      await expect(documentService.getDocuments()).rejects.toThrow('Network Error');
    });
  });

  describe('getDocument', () => {
    it('should fetch a specific document', async () => {
      const mockDocument: DocumentContent = {
        id: 'doc-1',
        filename: 'test.pdf',
        file_type: 'pdf',
        file_size: 1024,
        content: 'Document content',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      };

      mockApiClient.get.mockResolvedValue({ data: mockDocument } as any);

      const result = await documentService.getDocument('doc-1');

      expect(mockApiClient.get).toHaveBeenCalledWith('/documents/doc-1');
      expect(result).toEqual(mockDocument);
    });

    it('should handle document not found', async () => {
      const error = new Error('Document not found');
      mockApiClient.get.mockRejectedValue(error);

      await expect(documentService.getDocument('nonexistent')).rejects.toThrow(
        'Document not found'
      );
    });

    it('should fetch document with empty content', async () => {
      const mockDocument: DocumentContent = {
        id: 'doc-1',
        filename: 'empty.txt',
        file_type: 'txt',
        file_size: 0,
        content: '',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      };

      mockApiClient.get.mockResolvedValue({ data: mockDocument } as any);

      const result = await documentService.getDocument('doc-1');

      expect(result.content).toBe('');
    });
  });

  describe('deleteDocument', () => {
    it('should delete a document', async () => {
      mockApiClient.delete.mockResolvedValue({} as any);

      await documentService.deleteDocument('doc-1');

      expect(mockApiClient.delete).toHaveBeenCalledWith('/documents/doc-1');
    });

    it('should handle deletion errors', async () => {
      const error = new Error('Delete failed');
      mockApiClient.delete.mockRejectedValue(error);

      await expect(documentService.deleteDocument('doc-1')).rejects.toThrow('Delete failed');
    });

    it('should delete document with special characters in ID', async () => {
      mockApiClient.delete.mockResolvedValue({} as any);

      await documentService.deleteDocument('doc-123-abc-xyz');

      expect(mockApiClient.delete).toHaveBeenCalledWith('/documents/doc-123-abc-xyz');
    });

    it('should not return anything on successful deletion', async () => {
      mockApiClient.delete.mockResolvedValue({} as any);

      const result = await documentService.deleteDocument('doc-1');

      expect(result).toBeUndefined();
    });
  });
});
