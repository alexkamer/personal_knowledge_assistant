/**
 * API service for chat and conversation operations.
 */
import type {
  ChatRequest,
  ChatResponse,
  ChunkDetail,
  Conversation,
  ConversationListResponse,
  ConversationWithMessages,
  ToolCall,
  ToolResult,
} from '@/types/chat';
import { apiClient } from './api';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export interface Agent {
  name: string;
  display_name: string;
  description: string;
}

export const chatService = {
  /**
   * Get list of available agents.
   */
  async getAgents(): Promise<Agent[]> {
    const response = await apiClient.get<Agent[]>('/chat/agents');
    return response.data;
  },

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
    request: ChatRequest & { files?: File[] },
    onChunk: (chunk: string) => void,
    onSources: (sources: any[]) => void,
    onConversationId: (conversationId: string) => void,
    onDone: (messageId: string) => void,
    onError: (error: string) => void,
    onSuggestedQuestions?: (questions: string[]) => void,
    onAgent?: (agent: Agent) => void,
    onStatus?: (status: string) => void,
    onToolCall?: (toolCall: ToolCall) => void,
    onToolResult?: (toolResult: ToolResult) => void
  ): Promise<void> {
    // Build FormData if files are included, otherwise use JSON
    const hasFiles = request.files && request.files.length > 0;
    let body: FormData | string;
    let headers: Record<string, string> = {};

    if (hasFiles) {
      // Use FormData for file uploads
      const formData = new FormData();
      formData.append('message', request.message);

      // Add files
      request.files!.forEach((file) => {
        formData.append('files', file);
      });

      // Add other parameters
      if (request.conversation_id) formData.append('conversation_id', request.conversation_id);
      if (request.conversation_title) formData.append('conversation_title', request.conversation_title);
      if (request.model) formData.append('model', request.model);
      if (request.top_k !== undefined) formData.append('top_k', request.top_k.toString());
      formData.append('include_web_search', request.include_web_search ? 'true' : 'false');
      formData.append('include_notes', request.include_notes ? 'true' : 'false');
      formData.append('socratic_mode', request.socratic_mode ? 'true' : 'false');
      formData.append('skip_rag', request.skip_rag ? 'true' : 'false');

      body = formData;
      // Don't set Content-Type header, browser will set it with boundary for multipart/form-data
    } else {
      // Use JSON for regular messages
      const { files, ...requestWithoutFiles } = request;
      body = JSON.stringify(requestWithoutFiles);
      headers['Content-Type'] = 'application/json';
    }

    const response = await fetch(`${API_BASE_URL}/chat/stream`, {
      method: 'POST',
      headers,
      body,
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
                case 'agent':
                  if (onAgent && data.agent) {
                    onAgent(data.agent);
                  }
                  break;
                case 'status':
                  if (onStatus && data.status) {
                    onStatus(data.status);
                  }
                  break;
                case 'sources':
                  onSources(data.sources);
                  break;
                case 'chunk':
                  onChunk(data.content);
                  break;
                case 'suggested_questions':
                  if (onSuggestedQuestions && data.questions) {
                    onSuggestedQuestions(data.questions);
                  }
                  break;
                case 'tool_call':
                  if (onToolCall && data.tool_call) {
                    onToolCall(data.tool_call);
                  }
                  break;
                case 'tool_result':
                  if (onToolResult && data.tool_result) {
                    onToolResult(data.tool_result);
                  }
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
   * Update a conversation (title, summary, or pinned status).
   */
  async updateConversation(
    id: string,
    data: { title?: string; summary?: string; is_pinned?: boolean }
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

  /**
   * Get token usage statistics for a conversation.
   */
  async getTokenUsage(conversationId: string, model = 'qwen2.5:14b'): Promise<{
    total_tokens: number;
    limit: number;
    usage_percent: number;
    remaining: number;
    is_warning: boolean;
    is_critical: boolean;
    messages_count: number;
    message_tokens: Array<{
      message_id: string;
      role: string;
      tokens: number;
      created_at: string;
    }>;
  }> {
    const response = await apiClient.get(
      `/chat/conversations/${conversationId}/token-usage`,
      { params: { model } }
    );
    return response.data;
  },

  /**
   * Get detailed information about a specific chunk.
   */
  async getChunkDetail(chunkId: string): Promise<ChunkDetail> {
    const response = await apiClient.get<ChunkDetail>(`/chunks/${chunkId}`);
    return response.data;
  },
};
