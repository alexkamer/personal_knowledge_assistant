/**
 * Chat page for AI-powered Q&A using RAG.
 */
import { useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { MessageSquare, Plus, Trash2, AlertCircle, RotateCcw, Search, X, Globe, ChevronLeft, ChevronRight, Moon, Sun } from 'lucide-react';
import { MessageList } from '@/components/chat/MessageList';
import { ChatInput } from '@/components/chat/ChatInput';
import {
  useConversations,
  useConversation,
  useSendMessage,
  useDeleteConversation,
} from '@/hooks/useChat';
import { chatService } from '@/services/chatService';
import { useTheme } from '@/contexts/ThemeContext';
import type { Message } from '@/types/chat';

export function ChatPage() {
  const [selectedConversationId, setSelectedConversationId] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [webSearchEnabled, setWebSearchEnabled] = useState<boolean>(true); // Changed default to true
  const [streamingMessage, setStreamingMessage] = useState<string>('');
  const [isStreaming, setIsStreaming] = useState<boolean>(false);
  const [streamingSources, setStreamingSources] = useState<any[]>([]);
  const [streamingSuggestedQuestions, setStreamingSuggestedQuestions] = useState<string[]>([]);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);

  const queryClient = useQueryClient();
  const { theme, toggleTheme } = useTheme();
  const { data: conversationsData } = useConversations();
  const { data: conversationData, isLoading: isLoadingConversation } = useConversation(
    selectedConversationId
  );
  const sendMessage = useSendMessage();
  const deleteConversation = useDeleteConversation();

  const messages: Message[] = conversationData?.messages || [];

  // Add streaming message to the messages if currently streaming
  const displayMessages: Message[] = isStreaming
    ? [
        ...messages,
        {
          id: 'streaming',
          conversation_id: selectedConversationId || '',
          role: 'assistant' as const,
          content: streamingMessage,
          sources: streamingSources.length > 0 ? streamingSources : undefined,
          suggested_questions: streamingSuggestedQuestions.length > 0 ? streamingSuggestedQuestions : undefined,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
      ]
    : messages;

  // Filter conversations based on search query
  const filteredConversations = conversationsData?.conversations.filter((conv) =>
    conv.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    conv.summary?.toLowerCase().includes(searchQuery.toLowerCase())
  ) || [];

  const handleSendMessage = async (message: string) => {
    try {
      setErrorMessage(null);
      setIsStreaming(true);
      setStreamingMessage('');
      setStreamingSources([]);
      setStreamingSuggestedQuestions([]);

      // Get preferred model from localStorage
      const preferredModel = localStorage.getItem('preferred_model') || undefined;

      let newConversationId = selectedConversationId;

      await chatService.sendMessageStream(
        {
          message,
          conversation_id: selectedConversationId || undefined,
          conversation_title: selectedConversationId ? undefined : `Chat: ${message.slice(0, 50)}`,
          model: preferredModel,
          include_web_search: webSearchEnabled,
        },
        // onChunk
        (chunk) => {
          setStreamingMessage((prev) => prev + chunk);
        },
        // onSources
        (sources) => {
          setStreamingSources(sources);
        },
        // onConversationId
        (conversationId) => {
          if (!newConversationId) {
            newConversationId = conversationId;
            setSelectedConversationId(conversationId);
          }
        },
        // onDone
        (messageId) => {
          setIsStreaming(false);
          setStreamingMessage('');
          setStreamingSources([]);
          setStreamingSuggestedQuestions([]);
          // Invalidate queries to refresh the conversation
          queryClient.invalidateQueries({ queryKey: ['conversations'] });
          queryClient.invalidateQueries({ queryKey: ['conversations', newConversationId] });
        },
        // onError
        (error) => {
          setIsStreaming(false);
          setStreamingMessage('');
          setStreamingSources([]);
          setStreamingSuggestedQuestions([]);
          setErrorMessage(error);
        },
        // onSuggestedQuestions
        (questions) => {
          setStreamingSuggestedQuestions(questions);
        }
      );
    } catch (error: any) {
      console.error('Failed to send message:', error);
      const errorDetail = error?.message || 'Failed to send message';
      setErrorMessage(errorDetail);
      setIsStreaming(false);
      setStreamingMessage('');
      setStreamingSources([]);
      setStreamingSuggestedQuestions([]);
    }
  };

  const handleNewChat = () => {
    setSelectedConversationId(null);
    setErrorMessage(null);
  };

  const handleClearChat = () => {
    if (messages.length > 0 && window.confirm('Clear this conversation? This will start fresh but keep the conversation in history.')) {
      setSelectedConversationId(null);
      setErrorMessage(null);
    }
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

  const handleRegenerateMessage = async (messageId: string) => {
    // Find the message to regenerate
    const messageIndex = messages.findIndex((m) => m.id === messageId);
    if (messageIndex === -1) return;

    // Find the previous user message
    const userMessage = messages
      .slice(0, messageIndex)
      .reverse()
      .find((m) => m.role === 'user');

    if (!userMessage) return;

    // Resend the user message
    await handleSendMessage(userMessage.content);
  };

  return (
    <div className="h-screen flex flex-col bg-gray-50 dark:bg-gray-950">
      {/* Header */}
      <header className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <MessageSquare className="text-blue-600 dark:text-blue-400" size={28} />
            <div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">AI Chat</h1>
              <p className="text-sm text-gray-600 dark:text-gray-400">Ask questions about your knowledge base</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={toggleTheme}
              className="p-2 text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
              title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
            >
              {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
            </button>
            <button
              onClick={handleNewChat}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Plus size={18} />
              New Chat
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden relative">
        {/* Sidebar - Conversation List */}
        <aside className={`bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800 flex flex-col transition-all duration-300 ease-in-out relative ${
          isSidebarCollapsed ? 'w-0' : 'w-80'
        }`}>
          <div className={`${isSidebarCollapsed ? 'opacity-0' : 'opacity-100'} transition-opacity duration-300 flex flex-col h-full`}>
            <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-800 flex-shrink-0 flex items-center justify-between">
              <h2 className="font-semibold text-gray-900 dark:text-white">Conversations</h2>
              <button
                onClick={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
                className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded transition-colors"
                title="Hide sidebar"
              >
                <ChevronLeft size={20} />
              </button>
            </div>

            {/* Search Input */}
            <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-800 flex-shrink-0">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 dark:text-gray-500" size={18} />
                <input
                  type="text"
                  placeholder="Search conversations..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-10 py-2 border border-gray-300 dark:border-gray-700 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                {searchQuery && (
                  <button
                    onClick={() => setSearchQuery('')}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                  >
                    <X size={18} />
                  </button>
                )}
              </div>
            </div>

            <div className="flex-1 overflow-y-auto min-h-0">
            {conversationsData && conversationsData.conversations.length > 0 ? (
              filteredConversations.length > 0 ? (
                <div className="divide-y divide-gray-200 dark:divide-gray-800">
                  {filteredConversations.map((conv) => (
                  <div
                    key={conv.id}
                    onClick={() => handleSelectConversation(conv.id)}
                    className={`
                      p-4 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors
                      ${selectedConversationId === conv.id ? 'bg-blue-50 dark:bg-blue-900/20 border-l-4 border-blue-600' : ''}
                    `}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <h3 className="text-sm font-medium text-gray-900 dark:text-white truncate">
                          {conv.title}
                        </h3>
                        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
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
                        className="ml-2 p-1 text-gray-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded transition-colors"
                        aria-label="Delete conversation"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
              ) : (
                <div className="p-8 text-center text-gray-500 dark:text-gray-400">
                  <Search className="mx-auto mb-3 text-gray-400 dark:text-gray-500" size={32} />
                  <p className="text-sm font-medium">No conversations found</p>
                  <p className="text-xs mt-2">Try a different search term</p>
                  <button
                    onClick={() => setSearchQuery('')}
                    className="mt-4 text-xs text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300"
                  >
                    Clear search
                  </button>
                </div>
              )
            ) : (
              <div className="p-8 text-center text-gray-500 dark:text-gray-400">
                <p className="text-sm">No conversations yet</p>
                <p className="text-xs mt-2">Start a new chat to begin</p>
              </div>
            )}
            </div>
          </div>

          {/* Show Sidebar Button - Only visible when collapsed */}
          {isSidebarCollapsed && (
            <button
              onClick={() => setIsSidebarCollapsed(false)}
              className="absolute top-3 left-2 p-1 text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-800 rounded transition-colors z-10"
              title="Show sidebar"
            >
              <ChevronRight size={20} />
            </button>
          )}
        </aside>

        {/* Chat Area */}
        <main className="flex-1 flex flex-col bg-gray-50 dark:bg-gray-950">
          {/* Error Banner */}
          {errorMessage && (
            <div className="mx-6 mt-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg flex items-start gap-3">
              <AlertCircle className="text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" size={20} />
              <div className="flex-1">
                <h3 className="text-sm font-semibold text-red-900 dark:text-red-200">Error</h3>
                <p className="text-sm text-red-700 dark:text-red-300 mt-1">{errorMessage}</p>
              </div>
              <button
                onClick={() => setErrorMessage(null)}
                className="text-red-400 hover:text-red-600 dark:hover:text-red-300 transition-colors"
              >
                ×
              </button>
            </div>
          )}

          <MessageList
            messages={displayMessages}
            isLoading={isLoadingConversation}
            onRegenerateMessage={handleRegenerateMessage}
            onFeedbackSubmitted={() => {
              // Refresh conversation to get updated feedback
              queryClient.invalidateQueries({ queryKey: ['conversations', selectedConversationId] });
            }}
            onQuestionClick={handleSendMessage}
          />

          {/* Clear Chat Button - shows when there are messages */}
          {displayMessages.length > 0 && (
            <div className="px-6 pb-2 flex justify-center">
              <button
                onClick={handleClearChat}
                className="flex items-center gap-2 px-3 py-1.5 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-800 rounded-md transition-colors"
              >
                <RotateCcw size={14} />
                Clear Chat
              </button>
            </div>
          )}

          {/* Web Search Toggle */}
          <div className="px-6 pb-2">
            <button
              onClick={() => setWebSearchEnabled(!webSearchEnabled)}
              className={`flex items-center gap-2 px-3 py-2 rounded-md text-sm transition-colors ${
                webSearchEnabled
                  ? 'bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400 border border-green-300 dark:border-green-700'
                  : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 border border-gray-300 dark:border-gray-700 hover:bg-gray-200 dark:hover:bg-gray-700'
              }`}
            >
              <Globe size={16} />
              <span>{webSearchEnabled ? '✓ Using web + documents' : 'Documents only (no web search)'}</span>
            </button>
          </div>

          <ChatInput
            onSend={handleSendMessage}
            disabled={isStreaming}
          />
        </main>
      </div>
    </div>
  );
}
