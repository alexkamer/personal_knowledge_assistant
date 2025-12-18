/**
 * React Query hooks for document operations.
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { documentService } from '@/services/documentService';

/**
 * Hook to get list of documents with filtering and sorting.
 */
export function useDocuments(
  category?: string,
  sortBy: string = 'created_at',
  sortOrder: string = 'desc'
) {
  return useQuery({
    queryKey: ['documents', category, sortBy, sortOrder],
    queryFn: () => documentService.getDocuments(0, 100, category, sortBy, sortOrder),
  });
}

/**
 * Hook to get list of categories.
 */
export function useCategories() {
  return useQuery({
    queryKey: ['categories'],
    queryFn: () => documentService.getCategories(),
  });
}

/**
 * Hook to get a specific document with content.
 */
export function useDocument(id: string | null) {
  return useQuery({
    queryKey: ['documents', id],
    queryFn: () => documentService.getDocument(id!),
    enabled: !!id,
  });
}

/**
 * Hook to upload a document.
 */
export function useUploadDocument() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (file: File) => documentService.uploadDocument(file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
  });
}

/**
 * Hook to delete a document.
 */
export function useDeleteDocument() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => documentService.deleteDocument(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
  });
}

/**
 * Hook to create a document from a URL.
 */
export function useCreateDocumentFromURL() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (url: string) => documentService.createDocumentFromURL(url),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
  });
}
