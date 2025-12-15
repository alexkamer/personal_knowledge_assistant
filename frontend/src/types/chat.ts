/**
 * Chat and conversation type definitions.
 */

export interface Message {
  id: string;
  conversation_id: string;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
  model_used?: string;
  sources?: SourceCitation[];
}

export interface SourceCitation {
  index: number;
  source_type: 'note' | 'document';
  source_id: string;
  source_title: string;
  chunk_index: number;
  distance: number;
}

export interface Conversation {
  id: string;
  title: string;
  summary?: string;
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
}

export interface ChatResponse {
  conversation_id: string;
  message_id: string;
  response: string;
  sources: SourceCitation[];
  model_used: string;
}

export interface ConversationListResponse {
  conversations: Conversation[];
  total: number;
}
