/**
 * API service for document operations.
 */
import type { Document, DocumentContent, DocumentListResponse } from '@/types/document';
import { apiClient } from './api';

export const documentService = {
  /**
   * Upload a new document file.
   */
  async uploadDocument(file: File): Promise<Document> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await apiClient.post<Document>('/documents/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  /**
   * Get list of all documents.
   */
  async getDocuments(
    skip = 0,
    limit = 100,
    category?: string,
    sortBy = 'created_at',
    sortOrder = 'desc'
  ): Promise<DocumentListResponse> {
    const response = await apiClient.get<DocumentListResponse>('/documents/', {
      params: {
        skip,
        limit,
        ...(category && { category }),
        sort_by: sortBy,
        sort_order: sortOrder,
      },
    });
    return response.data;
  },

  /**
   * Get list of all available categories.
   */
  async getCategories(): Promise<string[]> {
    const response = await apiClient.get<string[]>('/documents/categories/list');
    return response.data;
  },

  /**
   * Get a specific document with its content.
   */
  async getDocument(id: string): Promise<DocumentContent> {
    const response = await apiClient.get<DocumentContent>(`/documents/${id}`);
    return response.data;
  },

  /**
   * Delete a document.
   */
  async deleteDocument(id: string): Promise<void> {
    await apiClient.delete(`/documents/${id}`);
  },

  /**
   * Create a document from a URL.
   */
  async createDocumentFromURL(url: string): Promise<Document> {
    const response = await apiClient.post<Document>('/documents/from-url', { url });
    return response.data;
  },
};
