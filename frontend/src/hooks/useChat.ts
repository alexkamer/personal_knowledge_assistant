/**
 * React Query hooks for chat operations.
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import type { ChatRequest } from '@/types/chat';
import { chatService } from '@/services/chatService';

/**
 * Hook to get list of conversations.
 */
export function useConversations() {
  return useQuery({
    queryKey: ['conversations'],
    queryFn: () => chatService.getConversations(),
  });
}

/**
 * Hook to get a specific conversation with messages.
 */
export function useConversation(id: string | null) {
  return useQuery({
    queryKey: ['conversations', id],
    queryFn: () => chatService.getConversation(id!),
    enabled: !!id,
  });
}

/**
 * Hook to send a chat message.
 */
export function useSendMessage() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: ChatRequest) => chatService.sendMessage(request),
    onSuccess: (data) => {
      // Invalidate conversations list
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
      // Invalidate the specific conversation
      queryClient.invalidateQueries({ queryKey: ['conversations', data.conversation_id] });
    },
  });
}

/**
 * Hook to update a conversation.
 */
export function useUpdateConversation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: { title?: string; summary?: string; is_pinned?: boolean } }) =>
      chatService.updateConversation(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
      queryClient.invalidateQueries({ queryKey: ['conversations', variables.id] });
    },
  });
}

/**
 * Hook to delete a conversation.
 */
export function useDeleteConversation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => chatService.deleteConversation(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
    },
  });
}
