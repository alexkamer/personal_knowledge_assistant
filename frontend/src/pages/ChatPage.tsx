/**
 * Chat page for AI-powered Q&A using RAG.
 */
import React, { useState } from 'react';
import { MessageSquare, Plus, Trash2 } from 'lucide-react';
import { MessageList } from '@/components/chat/MessageList';
import { ChatInput } from '@/components/chat/ChatInput';
import {
  useConversations,
  useConversation,
  useSendMessage,
  useDeleteConversation,
} from '@/hooks/useChat';
import type { Message } from '@/types/chat';

export function ChatPage() {
  const [selectedConversationId, setSelectedConversationId] = useState<string | null>(null);

  const { data: conversationsData } = useConversations();
  const { data: conversationData, isLoading: isLoadingConversation } = useConversation(
    selectedConversationId
  );
  const sendMessage = useSendMessage();
  const deleteConversation = useDeleteConversation();

  const messages: Message[] = conversationData?.messages || [];

  const handleSendMessage = async (message: string) => {
    try {
      const response = await sendMessage.mutateAsync({
        message,
        conversation_id: selectedConversationId || undefined,
        conversation_title: selectedConversationId ? undefined : `Chat: ${message.slice(0, 50)}`,
      });

      // If this was a new conversation, select it
      if (!selectedConversationId) {
        setSelectedConversationId(response.conversation_id);
      }
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  };

  const handleNewChat = () => {
    setSelectedConversationId(null);
  };

  const handleSelectConversation = (id: string) => {
    setSelectedConversationId(id);
  };

  const handleDeleteConversation = async (id: string) => {
    if (window.confirm('Are you sure you want to delete this conversation?')) {
      try {
        await deleteConversation.mutateAsync(id);
        if (selectedConversationId === id) {
          setSelectedConversationId(null);
        }
      } catch (error) {
        console.error('Failed to delete conversation:', error);
      }
    }
  };

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <MessageSquare className="text-blue-600" size={28} />
            <div>
              <h1 className="text-2xl font-bold text-gray-900">AI Chat</h1>
              <p className="text-sm text-gray-600">Ask questions about your knowledge base</p>
            </div>
          </div>
          <button
            onClick={handleNewChat}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Plus size={18} />
            New Chat
          </button>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar - Conversation List */}
        <aside className="w-80 bg-white border-r border-gray-200 flex flex-col">
          <div className="px-4 py-3 border-b border-gray-200">
            <h2 className="font-semibold text-gray-900">Conversations</h2>
          </div>

          <div className="flex-1 overflow-y-auto">
            {conversationsData && conversationsData.conversations.length > 0 ? (
              <div className="divide-y divide-gray-200">
                {conversationsData.conversations.map((conv) => (
                  <div
                    key={conv.id}
                    onClick={() => handleSelectConversation(conv.id)}
                    className={`
                      p-4 cursor-pointer hover:bg-gray-50 transition-colors
                      ${selectedConversationId === conv.id ? 'bg-blue-50 border-l-4 border-blue-600' : ''}
                    `}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <h3 className="text-sm font-medium text-gray-900 truncate">
                          {conv.title}
                        </h3>
                        <p className="text-xs text-gray-500 mt-1">
                          {new Date(conv.updated_at).toLocaleDateString('en-US', {
                            month: 'short',
                            day: 'numeric',
                            year: 'numeric',
                          })}
                        </p>
                      </div>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeleteConversation(conv.id);
                        }}
                        className="ml-2 p-1 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
                        aria-label="Delete conversation"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-8 text-center text-gray-500">
                <p className="text-sm">No conversations yet</p>
                <p className="text-xs mt-2">Start a new chat to begin</p>
              </div>
            )}
          </div>
        </aside>

        {/* Chat Area */}
        <main className="flex-1 flex flex-col bg-gray-50">
          <MessageList
            messages={messages}
            isLoading={sendMessage.isPending || isLoadingConversation}
          />
          <ChatInput
            onSend={handleSendMessage}
            disabled={sendMessage.isPending}
          />
        </main>
      </div>
    </div>
  );
}
