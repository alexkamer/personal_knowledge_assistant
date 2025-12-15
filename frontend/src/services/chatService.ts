/**
 * API service for chat and conversation operations.
 */
import type {
  ChatRequest,
  ChatResponse,
  Conversation,
  ConversationListResponse,
  ConversationWithMessages,
} from '@/types/chat';
import { apiClient } from './api';

export const chatService = {
  /**
   * Send a message and get AI response.
   */
  async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    const response = await apiClient.post<ChatResponse>('/chat/', request);
    return response.data;
  },

  /**
   * Get list of all conversations.
   */
  async getConversations(skip = 0, limit = 100): Promise<ConversationListResponse> {
    const response = await apiClient.get<ConversationListResponse>('/chat/conversations/', {
      params: { skip, limit },
    });
    return response.data;
  },

  /**
   * Get a conversation with its full message history.
   */
  async getConversation(id: string): Promise<ConversationWithMessages> {
    const response = await apiClient.get<ConversationWithMessages>(
      `/chat/conversations/${id}`
    );
    return response.data;
  },

  /**
   * Update a conversation (title or summary).
   */
  async updateConversation(
    id: string,
    data: { title?: string; summary?: string }
  ): Promise<Conversation> {
    const response = await apiClient.patch<Conversation>(
      `/chat/conversations/${id}`,
      data
    );
    return response.data;
  },

  /**
   * Delete a conversation.
   */
  async deleteConversation(id: string): Promise<void> {
    await apiClient.delete(`/chat/conversations/${id}`);
  },
};
