/**
 * React Query hooks for document operations.
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { documentService } from '@/services/documentService';

/**
 * Hook to get list of documents.
 */
export function useDocuments() {
  return useQuery({
    queryKey: ['documents'],
    queryFn: () => documentService.getDocuments(),
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
