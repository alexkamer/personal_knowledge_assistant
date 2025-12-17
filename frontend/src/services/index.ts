/**
 * Service exports for easy imports.
 */
export { apiClient } from './api';
export { chatService } from './chatService';

// Re-export commonly used functions
import { chatService as chat } from './chatService';
export const {
  getAgents,
  sendMessage,
  sendMessageStream,
  getConversations,
  getConversation,
  updateConversation,
  deleteConversation,
  getTokenUsage,
  getChunkDetail,
} = chat;
