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

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export const chatService = {
  /**
   * Send a message and get AI response.
   */
  async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    const response = await apiClient.post<ChatResponse>('/chat/', request);
    return response.data;
  },

  /**
   * Send a message and get streaming AI response using Server-Sent Events.
   */
  async sendMessageStream(
    request: ChatRequest,
    onChunk: (chunk: string) => void,
    onSources: (sources: any[]) => void,
    onConversationId: (conversationId: string) => void,
    onDone: (messageId: string) => void,
    onError: (error: string) => void
  ): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

    if (!reader) {
      throw new Error('Response body is null');
    }

    try {
      while (true) {
        const { done, value } = await reader.read();

        if (done) {
          break;
        }

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));

              switch (data.type) {
                case 'conversation_id':
                  onConversationId(data.conversation_id);
                  break;
                case 'sources':
                  onSources(data.sources);
                  break;
                case 'chunk':
                  onChunk(data.content);
                  break;
                case 'done':
                  onDone(data.message_id);
                  break;
                case 'error':
                  onError(data.error);
                  break;
              }
            } catch (e) {
              console.error('Failed to parse SSE data:', e);
            }
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
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
