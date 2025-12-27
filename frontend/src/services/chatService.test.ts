/**
 * Tests for chatService
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { chatService, type Agent } from './chatService';
import { apiClient } from './api';
import type {
  ChatRequest,
  ChatResponse,
  ChunkDetail,
  Conversation,
  ConversationListResponse,
  ConversationWithMessages,
} from '@/types/chat';

// Mock the api module
vi.mock('./api', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}));

describe('chatService', () => {
  const mockApiClient = vi.mocked(apiClient);

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('getAgents', () => {
    it('should fetch available agents', async () => {
      const mockAgents: Agent[] = [
        {
          name: 'general',
          display_name: 'General Assistant',
          description: 'General purpose AI assistant',
        },
        {
          name: 'researcher',
          display_name: 'Research Assistant',
          description: 'Specialized in research tasks',
        },
      ];

      mockApiClient.get.mockResolvedValue({ data: mockAgents } as any);

      const result = await chatService.getAgents();

      expect(mockApiClient.get).toHaveBeenCalledWith('/chat/agents');
      expect(result).toEqual(mockAgents);
    });

    it('should handle empty agent list', async () => {
      mockApiClient.get.mockResolvedValue({ data: [] } as any);

      const result = await chatService.getAgents();

      expect(result).toEqual([]);
    });

    it('should throw error on API failure', async () => {
      const error = new Error('Network Error');
      mockApiClient.get.mockRejectedValue(error);

      await expect(chatService.getAgents()).rejects.toThrow('Network Error');
    });
  });

  describe('sendMessage', () => {
    it('should send a message and receive response', async () => {
      const request: ChatRequest = {
        query: 'What is TypeScript?',
        conversation_id: 'conv-1',
      };

      const mockResponse: ChatResponse = {
        message_id: 'msg-1',
        conversation_id: 'conv-1',
        response: 'TypeScript is a typed superset of JavaScript.',
        sources: [],
      };

      mockApiClient.post.mockResolvedValue({ data: mockResponse } as any);

      const result = await chatService.sendMessage(request);

      expect(mockApiClient.post).toHaveBeenCalledWith('/chat/', request);
      expect(result).toEqual(mockResponse);
    });

    it('should send message without conversation_id', async () => {
      const request: ChatRequest = {
        query: 'Hello',
      };

      const mockResponse: ChatResponse = {
        message_id: 'msg-1',
        conversation_id: 'new-conv',
        response: 'Hi there!',
        sources: [],
      };

      mockApiClient.post.mockResolvedValue({ data: mockResponse } as any);

      const result = await chatService.sendMessage(request);

      expect(result.conversation_id).toBe('new-conv');
    });

    it('should handle message with sources', async () => {
      const request: ChatRequest = {
        query: 'What are my notes about?',
      };

      const mockResponse: ChatResponse = {
        message_id: 'msg-1',
        conversation_id: 'conv-1',
        response: 'Your notes cover various topics.',
        sources: [
          {
            chunk_id: 'chunk-1',
            content: 'Note content',
            score: 0.95,
            source_type: 'note',
            source_id: 'note-1',
          },
        ],
      };

      mockApiClient.post.mockResolvedValue({ data: mockResponse } as any);

      const result = await chatService.sendMessage(request);

      expect(result.sources).toHaveLength(1);
      expect(result.sources[0].chunk_id).toBe('chunk-1');
    });

    it('should handle API errors', async () => {
      const request: ChatRequest = {
        query: 'Test',
      };

      const error = new Error('API Error');
      mockApiClient.post.mockRejectedValue(error);

      await expect(chatService.sendMessage(request)).rejects.toThrow('API Error');
    });
  });

  describe('getConversations', () => {
    it('should fetch conversations with default pagination', async () => {
      const mockResponse: ConversationListResponse = {
        conversations: [
          {
            id: 'conv-1',
            title: 'Test Conversation',
            created_at: '2024-01-01T00:00:00Z',
            updated_at: '2024-01-01T00:00:00Z',
          },
        ],
        total: 1,
      };

      mockApiClient.get.mockResolvedValue({ data: mockResponse } as any);

      const result = await chatService.getConversations();

      expect(mockApiClient.get).toHaveBeenCalledWith('/chat/conversations/', {
        params: { skip: 0, limit: 100 },
      });
      expect(result).toEqual(mockResponse);
    });

    it('should fetch conversations with custom pagination', async () => {
      const mockResponse: ConversationListResponse = {
        conversations: [],
        total: 0,
      };

      mockApiClient.get.mockResolvedValue({ data: mockResponse } as any);

      await chatService.getConversations(10, 50);

      expect(mockApiClient.get).toHaveBeenCalledWith('/chat/conversations/', {
        params: { skip: 10, limit: 50 },
      });
    });

    it('should handle empty conversation list', async () => {
      const mockResponse: ConversationListResponse = {
        conversations: [],
        total: 0,
      };

      mockApiClient.get.mockResolvedValue({ data: mockResponse } as any);

      const result = await chatService.getConversations();

      expect(result.conversations).toEqual([]);
      expect(result.total).toBe(0);
    });

    it('should throw error on API failure', async () => {
      const error = new Error('Network Error');
      mockApiClient.get.mockRejectedValue(error);

      await expect(chatService.getConversations()).rejects.toThrow('Network Error');
    });
  });

  describe('getConversation', () => {
    it('should fetch a specific conversation with messages', async () => {
      const mockConversation: ConversationWithMessages = {
        id: 'conv-1',
        title: 'Test Conversation',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
        messages: [
          {
            id: 'msg-1',
            role: 'user',
            content: 'Hello',
            created_at: '2024-01-01T00:00:00Z',
          },
          {
            id: 'msg-2',
            role: 'assistant',
            content: 'Hi there!',
            created_at: '2024-01-01T00:01:00Z',
          },
        ],
      };

      mockApiClient.get.mockResolvedValue({ data: mockConversation } as any);

      const result = await chatService.getConversation('conv-1');

      expect(mockApiClient.get).toHaveBeenCalledWith('/chat/conversations/conv-1');
      expect(result).toEqual(mockConversation);
      expect(result.messages).toHaveLength(2);
    });

    it('should handle conversation not found', async () => {
      const error = new Error('Conversation not found');
      mockApiClient.get.mockRejectedValue(error);

      await expect(chatService.getConversation('nonexistent')).rejects.toThrow(
        'Conversation not found'
      );
    });

    it('should fetch conversation with empty messages', async () => {
      const mockConversation: ConversationWithMessages = {
        id: 'conv-1',
        title: 'Empty Conversation',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
        messages: [],
      };

      mockApiClient.get.mockResolvedValue({ data: mockConversation } as any);

      const result = await chatService.getConversation('conv-1');

      expect(result.messages).toEqual([]);
    });
  });

  describe('updateConversation', () => {
    it('should update conversation title', async () => {
      const updateData = {
        title: 'Updated Title',
      };

      const mockUpdatedConversation: Conversation = {
        id: 'conv-1',
        title: 'Updated Title',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-02T00:00:00Z',
      };

      mockApiClient.patch.mockResolvedValue({ data: mockUpdatedConversation } as any);

      const result = await chatService.updateConversation('conv-1', updateData);

      expect(mockApiClient.patch).toHaveBeenCalledWith(
        '/chat/conversations/conv-1',
        updateData
      );
      expect(result).toEqual(mockUpdatedConversation);
    });

    it('should update conversation summary', async () => {
      const updateData = {
        summary: 'Updated summary',
      };

      const mockUpdatedConversation: Conversation = {
        id: 'conv-1',
        title: 'Test',
        summary: 'Updated summary',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-02T00:00:00Z',
      };

      mockApiClient.patch.mockResolvedValue({ data: mockUpdatedConversation } as any);

      const result = await chatService.updateConversation('conv-1', updateData);

      expect(result.summary).toBe('Updated summary');
    });

    it('should update both title and summary', async () => {
      const updateData = {
        title: 'New Title',
        summary: 'New summary',
      };

      const mockUpdatedConversation: Conversation = {
        id: 'conv-1',
        title: 'New Title',
        summary: 'New summary',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-02T00:00:00Z',
      };

      mockApiClient.patch.mockResolvedValue({ data: mockUpdatedConversation } as any);

      const result = await chatService.updateConversation('conv-1', updateData);

      expect(result.title).toBe('New Title');
      expect(result.summary).toBe('New summary');
    });

    it('should handle update errors', async () => {
      const updateData = {
        title: 'Error Title',
      };

      const error = new Error('Update failed');
      mockApiClient.patch.mockRejectedValue(error);

      await expect(chatService.updateConversation('conv-1', updateData)).rejects.toThrow(
        'Update failed'
      );
    });
  });

  describe('deleteConversation', () => {
    it('should delete a conversation', async () => {
      mockApiClient.delete.mockResolvedValue({} as any);

      await chatService.deleteConversation('conv-1');

      expect(mockApiClient.delete).toHaveBeenCalledWith('/chat/conversations/conv-1');
    });

    it('should handle deletion errors', async () => {
      const error = new Error('Delete failed');
      mockApiClient.delete.mockRejectedValue(error);

      await expect(chatService.deleteConversation('conv-1')).rejects.toThrow('Delete failed');
    });

    it('should not return anything on successful deletion', async () => {
      mockApiClient.delete.mockResolvedValue({} as any);

      const result = await chatService.deleteConversation('conv-1');

      expect(result).toBeUndefined();
    });
  });

  describe('getTokenUsage', () => {
    it('should fetch token usage for a conversation', async () => {
      const mockTokenUsage = {
        total_tokens: 1000,
        limit: 32768,
        usage_percent: 3.05,
        remaining: 31768,
        is_warning: false,
        is_critical: false,
        messages_count: 5,
        message_tokens: [
          {
            message_id: 'msg-1',
            role: 'user',
            tokens: 200,
            created_at: '2024-01-01T00:00:00Z',
          },
        ],
      };

      mockApiClient.get.mockResolvedValue({ data: mockTokenUsage } as any);

      const result = await chatService.getTokenUsage('conv-1');

      expect(mockApiClient.get).toHaveBeenCalledWith(
        '/chat/conversations/conv-1/token-usage',
        { params: { model: 'qwen2.5:14b' } }
      );
      expect(result).toEqual(mockTokenUsage);
    });

    it('should fetch token usage with custom model', async () => {
      const mockTokenUsage = {
        total_tokens: 500,
        limit: 16384,
        usage_percent: 3.05,
        remaining: 15884,
        is_warning: false,
        is_critical: false,
        messages_count: 2,
        message_tokens: [],
      };

      mockApiClient.get.mockResolvedValue({ data: mockTokenUsage } as any);

      await chatService.getTokenUsage('conv-1', 'llama3.2:3b');

      expect(mockApiClient.get).toHaveBeenCalledWith(
        '/chat/conversations/conv-1/token-usage',
        { params: { model: 'llama3.2:3b' } }
      );
    });

    it('should handle warning state token usage', async () => {
      const mockTokenUsage = {
        total_tokens: 26214,
        limit: 32768,
        usage_percent: 80.0,
        remaining: 6554,
        is_warning: true,
        is_critical: false,
        messages_count: 20,
        message_tokens: [],
      };

      mockApiClient.get.mockResolvedValue({ data: mockTokenUsage } as any);

      const result = await chatService.getTokenUsage('conv-1');

      expect(result.is_warning).toBe(true);
      expect(result.is_critical).toBe(false);
    });

    it('should handle critical state token usage', async () => {
      const mockTokenUsage = {
        total_tokens: 29491,
        limit: 32768,
        usage_percent: 90.0,
        remaining: 3277,
        is_warning: true,
        is_critical: true,
        messages_count: 30,
        message_tokens: [],
      };

      mockApiClient.get.mockResolvedValue({ data: mockTokenUsage } as any);

      const result = await chatService.getTokenUsage('conv-1');

      expect(result.is_warning).toBe(true);
      expect(result.is_critical).toBe(true);
    });

    it('should throw error on API failure', async () => {
      const error = new Error('Failed to fetch token usage');
      mockApiClient.get.mockRejectedValue(error);

      await expect(chatService.getTokenUsage('conv-1')).rejects.toThrow(
        'Failed to fetch token usage'
      );
    });
  });

  describe('getChunkDetail', () => {
    it('should fetch chunk details', async () => {
      const mockChunkDetail: ChunkDetail = {
        id: 'chunk-1',
        content: 'This is chunk content',
        source_type: 'note',
        source_id: 'note-1',
        source_title: 'Test Note',
        metadata: {
          position: 0,
          total_chunks: 5,
        },
      };

      mockApiClient.get.mockResolvedValue({ data: mockChunkDetail } as any);

      const result = await chatService.getChunkDetail('chunk-1');

      expect(mockApiClient.get).toHaveBeenCalledWith('/chunks/chunk-1');
      expect(result).toEqual(mockChunkDetail);
    });

    it('should fetch chunk from document source', async () => {
      const mockChunkDetail: ChunkDetail = {
        id: 'chunk-2',
        content: 'Document chunk content',
        source_type: 'document',
        source_id: 'doc-1',
        source_title: 'Test Document.pdf',
        metadata: {
          position: 1,
          total_chunks: 10,
        },
      };

      mockApiClient.get.mockResolvedValue({ data: mockChunkDetail } as any);

      const result = await chatService.getChunkDetail('chunk-2');

      expect(result.source_type).toBe('document');
    });

    it('should handle chunk not found', async () => {
      const error = new Error('Chunk not found');
      mockApiClient.get.mockRejectedValue(error);

      await expect(chatService.getChunkDetail('nonexistent')).rejects.toThrow('Chunk not found');
    });
  });

  describe('sendMessageStream', () => {
    let mockFetch: any;
    let originalFetch: typeof global.fetch;

    beforeEach(() => {
      originalFetch = global.fetch;
      mockFetch = vi.fn();
      global.fetch = mockFetch;
    });

    afterEach(() => {
      global.fetch = originalFetch;
    });

    it('should handle streaming response', async () => {
      const onChunk = vi.fn();
      const onSources = vi.fn();
      const onConversationId = vi.fn();
      const onDone = vi.fn();
      const onError = vi.fn();

      const mockStreamData = [
        'data: {"type":"conversation_id","conversation_id":"conv-1"}\n',
        'data: {"type":"sources","sources":[]}\n',
        'data: {"type":"chunk","content":"Hello"}\n',
        'data: {"type":"chunk","content":" world"}\n',
        'data: {"type":"done","message_id":"msg-1"}\n',
      ].join('');

      const mockReader = {
        read: vi
          .fn()
          .mockResolvedValueOnce({
            done: false,
            value: new TextEncoder().encode(mockStreamData),
          })
          .mockResolvedValueOnce({ done: true, value: undefined }),
        releaseLock: vi.fn(),
      };

      mockFetch.mockResolvedValue({
        ok: true,
        body: {
          getReader: () => mockReader,
        },
      });

      const request: ChatRequest = {
        query: 'Test',
      };

      // sendMessageStream returns AbortController, not Promise - wrap callbacks in Promise
      await new Promise<void>((resolve) => {
        chatService.sendMessageStream(
          request,
          onChunk,
          onSources,
          onConversationId,
          (messageId) => {
            onDone(messageId);
            resolve();
          },
          (error) => {
            onError(error);
            resolve();
          }
        );
      });

      expect(onConversationId).toHaveBeenCalledWith('conv-1');
      expect(onSources).toHaveBeenCalledWith([]);
      expect(onChunk).toHaveBeenCalledWith('Hello');
      expect(onChunk).toHaveBeenCalledWith(' world');
      expect(onDone).toHaveBeenCalledWith('msg-1');
      expect(onError).not.toHaveBeenCalled();
    });

    it('should handle streaming error', async () => {
      const onChunk = vi.fn();
      const onSources = vi.fn();
      const onConversationId = vi.fn();
      const onDone = vi.fn();
      const onError = vi.fn();

      const mockStreamData = 'data: {"type":"error","error":"Something went wrong"}\n';

      const mockReader = {
        read: vi
          .fn()
          .mockResolvedValueOnce({
            done: false,
            value: new TextEncoder().encode(mockStreamData),
          })
          .mockResolvedValueOnce({ done: true, value: undefined }),
        releaseLock: vi.fn(),
      };

      mockFetch.mockResolvedValue({
        ok: true,
        body: {
          getReader: () => mockReader,
        },
      });

      const request: ChatRequest = {
        query: 'Test',
      };

      // Wrap callbacks in Promise
      await new Promise<void>((resolve) => {
        chatService.sendMessageStream(
          request,
          onChunk,
          onSources,
          onConversationId,
          (messageId) => {
            onDone(messageId);
            resolve();
          },
          (error) => {
            onError(error);
            resolve();
          }
        );
      });

      expect(onError).toHaveBeenCalledWith('Something went wrong');
      expect(onDone).not.toHaveBeenCalled();
    });

    it('should handle HTTP error', async () => {
      const onChunk = vi.fn();
      const onSources = vi.fn();
      const onConversationId = vi.fn();
      const onDone = vi.fn();
      const onError = vi.fn();

      mockFetch.mockResolvedValue({
        ok: false,
        status: 500,
      });

      const request: ChatRequest = {
        query: 'Test',
      };

      // Wrap callbacks in Promise - HTTP errors call onError
      await new Promise<void>((resolve) => {
        chatService.sendMessageStream(
          request,
          onChunk,
          onSources,
          onConversationId,
          (messageId) => {
            onDone(messageId);
            resolve();
          },
          (error) => {
            onError(error);
            resolve();
          }
        );
      });

      expect(onError).toHaveBeenCalledWith('HTTP error! status: 500');
      expect(onDone).not.toHaveBeenCalled();
    });

    it('should handle null response body', async () => {
      const onChunk = vi.fn();
      const onSources = vi.fn();
      const onConversationId = vi.fn();
      const onDone = vi.fn();
      const onError = vi.fn();

      mockFetch.mockResolvedValue({
        ok: true,
        body: null,
      });

      const request: ChatRequest = {
        query: 'Test',
      };

      // Wrap callbacks in Promise - null body errors call onError
      await new Promise<void>((resolve) => {
        chatService.sendMessageStream(
          request,
          onChunk,
          onSources,
          onConversationId,
          (messageId) => {
            onDone(messageId);
            resolve();
          },
          (error) => {
            onError(error);
            resolve();
          }
        );
      });

      expect(onError).toHaveBeenCalledWith('Response body is null');
      expect(onDone).not.toHaveBeenCalled();
    });

    it('should handle agent event', async () => {
      const onChunk = vi.fn();
      const onSources = vi.fn();
      const onConversationId = vi.fn();
      const onDone = vi.fn();
      const onError = vi.fn();
      const onAgent = vi.fn();

      const mockStreamData =
        'data: {"type":"agent","agent":{"name":"researcher","display_name":"Research Assistant","description":"Research specialist"}}\n' +
        'data: {"type":"done","message_id":"msg-1"}\n';

      const mockReader = {
        read: vi
          .fn()
          .mockResolvedValueOnce({
            done: false,
            value: new TextEncoder().encode(mockStreamData),
          })
          .mockResolvedValueOnce({ done: true, value: undefined }),
        releaseLock: vi.fn(),
      };

      mockFetch.mockResolvedValue({
        ok: true,
        body: {
          getReader: () => mockReader,
        },
      });

      const request: ChatRequest = {
        query: 'Test',
      };

      // Wrap callbacks in Promise
      await new Promise<void>((resolve) => {
        chatService.sendMessageStream(
          request,
          onChunk,
          onSources,
          onConversationId,
          (messageId) => {
            onDone(messageId);
            resolve();
          },
          (error) => {
            onError(error);
            resolve();
          },
          undefined,
          onAgent
        );
      });

      expect(onAgent).toHaveBeenCalledWith({
        name: 'researcher',
        display_name: 'Research Assistant',
        description: 'Research specialist',
      });
    });

    it('should handle suggested questions event', async () => {
      const onChunk = vi.fn();
      const onSources = vi.fn();
      const onConversationId = vi.fn();
      const onDone = vi.fn();
      const onError = vi.fn();
      const onSuggestedQuestions = vi.fn();

      const mockStreamData =
        'data: {"type":"suggested_questions","questions":["Question 1","Question 2"]}\n' +
        'data: {"type":"done","message_id":"msg-1"}\n';

      const mockReader = {
        read: vi
          .fn()
          .mockResolvedValueOnce({
            done: false,
            value: new TextEncoder().encode(mockStreamData),
          })
          .mockResolvedValueOnce({ done: true, value: undefined }),
        releaseLock: vi.fn(),
      };

      mockFetch.mockResolvedValue({
        ok: true,
        body: {
          getReader: () => mockReader,
        },
      });

      const request: ChatRequest = {
        query: 'Test',
      };

      // Wrap callbacks in Promise
      await new Promise<void>((resolve) => {
        chatService.sendMessageStream(
          request,
          onChunk,
          onSources,
          onConversationId,
          (messageId) => {
            onDone(messageId);
            resolve();
          },
          (error) => {
            onError(error);
            resolve();
          },
          onSuggestedQuestions
        );
      });

      expect(onSuggestedQuestions).toHaveBeenCalledWith(['Question 1', 'Question 2']);
    });
  });
});
