/**
 * Chat and conversation type definitions.
 */

export interface MessageFeedback {
  id: string;
  message_id: string;
  is_positive: boolean;
  comment?: string;
  created_at: string;
}

export interface Message {
  id: string;
  conversation_id: string;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
  model_used?: string;
  sources?: SourceCitation[];
  feedback?: MessageFeedback;
  suggested_questions?: string[];
}

export interface SourceCitation {
  index: number;
  source_type: 'note' | 'document' | 'web';
  source_id: string;
  chunk_id?: string;
  source_title: string;
  chunk_index: number;
  distance: number;
  // Metadata fields from semantic chunking
  content_type?: string;
  section_title?: string;
  has_code?: boolean;
  semantic_density?: number;
}

export interface ChunkDetail {
  id: string;
  content: string;
  chunk_index: number;
  token_count: number;
  source_title: string;
  source_type: string;
  metadata: Record<string, any>;
}

export interface Conversation {
  id: string;
  title: string;
  summary?: string;
  is_pinned: boolean;
  created_at: string;
  updated_at: string;
  message_count?: number;
}

export interface ConversationWithMessages extends Conversation {
  messages: Message[];
}

export interface ChatRequest {
  message: string;
  conversation_id?: string;
  conversation_title?: string;
  model?: string;
  top_k?: number;
  include_web_search?: boolean;
  include_notes?: boolean;
  socratic_mode?: boolean;
}

export interface ChatResponse {
  conversation_id: string;
  message_id: string;
  response: string;
  sources: SourceCitation[];
  model_used: string;
  suggested_questions?: string[];
}

export interface ConversationListResponse {
  conversations: Conversation[];
  total: number;
}

// Tool-related types for agent reasoning
export interface ToolCall {
  tool: string;
  parameters: Record<string, any>;
  thought?: string;
}

export interface ToolResult {
  tool: string;
  success: boolean;
  result: any;
  error?: string;
  metadata?: Record<string, any>;
}
