/**
 * Testing utilities and helpers
 */
import { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';

// Create a custom render function that includes providers
const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false, // Don't retry failed queries in tests
        gcTime: 0, // Disable caching in tests
      },
      mutations: {
        retry: false,
      },
    },
  });

interface AllProvidersProps {
  children: React.ReactNode;
}

function AllProviders({ children }: AllProvidersProps) {
  const testQueryClient = createTestQueryClient();

  return (
    <QueryClientProvider client={testQueryClient}>
      <BrowserRouter>{children}</BrowserRouter>
    </QueryClientProvider>
  );
}

function customRender(ui: ReactElement, options?: Omit<RenderOptions, 'wrapper'>) {
  return render(ui, { wrapper: AllProviders, ...options });
}

// Re-export everything from testing library
export * from '@testing-library/react';
export { customRender as render };

// Mock API responses
export const mockNote = {
  id: '123e4567-e89b-12d3-a456-426614174000',
  title: 'Test Note',
  content: 'This is a test note content',
  created_at: '2025-01-01T00:00:00Z',
  updated_at: '2025-01-01T00:00:00Z',
  tags: [],
};

export const mockDocument = {
  id: '123e4567-e89b-12d3-a456-426614174001',
  filename: 'test.pdf',
  file_type: 'pdf',
  file_path: '/uploads/test.pdf',
  file_size: 1024,
  created_at: '2025-01-01T00:00:00Z',
  updated_at: '2025-01-01T00:00:00Z',
  metadata_: null,
};

export const mockConversation = {
  id: '123e4567-e89b-12d3-a456-426614174002',
  title: 'Test Conversation',
  created_at: '2025-01-01T00:00:00Z',
  updated_at: '2025-01-01T00:00:00Z',
  summary: null,
  is_pinned: false,
  message_count: 2,
};

export const mockMessage = {
  id: '123e4567-e89b-12d3-a456-426614174003',
  conversation_id: '123e4567-e89b-12d3-a456-426614174002',
  role: 'user',
  content: 'Test message',
  created_at: '2025-01-01T00:00:00Z',
  model_used: null,
  sources: null,
};

export const mockChatResponse = {
  conversation_id: '123e4567-e89b-12d3-a456-426614174002',
  message_id: '123e4567-e89b-12d3-a456-426614174004',
  response: 'This is a test response from the AI',
  sources: [],
  model_used: 'qwen2.5:14b',
  suggested_questions: ['Follow-up question 1?', 'Follow-up question 2?'],
};
