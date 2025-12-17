/**
 * Chat page for AI-powered Q&A using RAG.
 */
import { useState, useRef, useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useLocation } from 'react-router-dom';
import { MessageSquare, Plus, MoreVertical, AlertCircle, RotateCcw, Search, X, Globe, ChevronLeft, ChevronRight, Moon, Sun, Download, Pin, PinOff, GraduationCap, Lightbulb, Brain, Clock, BookOpen } from 'lucide-react';
import { MessageList } from '@/components/chat/MessageList';
import { ChatInput } from '@/components/chat/ChatInput';
import { TokenUsage } from '@/components/chat/TokenUsage';
import { KeyboardShortcutsModal } from '@/components/KeyboardShortcutsModal';
import ActivityTimeline from '@/components/chat/ActivityTimeline';
import { LearningGapsPanel } from '@/components/learning/LearningGapsPanel';
import { MetabolizationQuiz } from '@/components/learning/MetabolizationQuiz';
import { KnowledgeEvolutionTimeline } from '@/components/learning/KnowledgeEvolutionTimeline';
import {
  useConversations,
  useConversation,
  useDeleteConversation,
  useUpdateConversation,
} from '@/hooks/useChat';
import { chatService } from '@/services/chatService';
import { learningGapsService, type LearningGap, type LearningPathResponse } from '@/services/learningGapsService';
import { metabolizationService, type MetabolizationQuestion, type AnswerEvaluationResponse } from '@/services/metabolizationService';
import { useCreateSnapshot } from '@/hooks/useKnowledgeEvolution';
import { useTheme } from '@/contexts/ThemeContext';
import { downloadConversationAsMarkdown } from '@/utils/exportMarkdown';
import { useKeyboardShortcuts, type KeyboardShortcut } from '@/hooks/useKeyboardShortcuts';
import type { Message, ToolCall, ToolResult } from '@/types/chat';

export function ChatPage() {
  const [selectedConversationId, setSelectedConversationId] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [webSearchEnabled, setWebSearchEnabled] = useState<boolean>(true); // Changed default to true
  const [includeNotes, setIncludeNotes] = useState<boolean>(false); // Default to false - only use reputable sources
  const [socraticMode, setSocraticMode] = useState<boolean>(false); // Default to false - direct answers
  const [streamingMessage, setStreamingMessage] = useState<string>('');
  const [isStreaming, setIsStreaming] = useState<boolean>(false);
  const [streamingSources, setStreamingSources] = useState<any[]>([]);
  const [streamingSuggestedQuestions, setStreamingSuggestedQuestions] = useState<string[]>([]);
  const [streamingStatus, setStreamingStatus] = useState<string>('');
  const [streamingToolCalls, setStreamingToolCalls] = useState<ToolCall[]>([]);
  const [streamingToolResults, setStreamingToolResults] = useState<ToolResult[]>([]);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [activeAgent, setActiveAgent] = useState<{name: string; display_name: string; description: string} | null>(null);
  const [openMenuId, setOpenMenuId] = useState<string | null>(null);
  const [editingConversationId, setEditingConversationId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState('');
  const [showShortcutsModal, setShowShortcutsModal] = useState(false);
  const [prefillQuestion, setPrefillQuestion] = useState<string>('');

  // Learning Gaps state
  const [showLearningGaps, setShowLearningGaps] = useState(false);
  const [learningGaps, setLearningGaps] = useState<LearningGap[]>([]);
  const [learningPath, setLearningPath] = useState<LearningPathResponse | undefined>(undefined);
  const [isLoadingGaps, setIsLoadingGaps] = useState(false);
  const [gapsQuestion, setGapsQuestion] = useState('');
  const [gapsError, setGapsError] = useState<string | null>(null);

  // Metabolization Quiz state
  const [showMetabolizationQuiz, setShowMetabolizationQuiz] = useState(false);
  const [quizQuestions, setQuizQuestions] = useState<MetabolizationQuestion[]>([]);
  const [isLoadingQuiz, setIsLoadingQuiz] = useState(false);
  const [quizContentTitle, setQuizContentTitle] = useState('');

  // Knowledge Evolution Timeline state
  const [showEvolutionTimeline, setShowEvolutionTimeline] = useState(false);

  const createSnapshot = useCreateSnapshot();

  const menuRef = useRef<HTMLDivElement>(null);
  const editInputRef = useRef<HTMLInputElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);

  const queryClient = useQueryClient();
  const location = useLocation();
  const { theme, toggleTheme } = useTheme();
  const { data: conversationsData } = useConversations();
  const { data: conversationData, isLoading: isLoadingConversation } = useConversation(
    selectedConversationId
  );
  const deleteConversation = useDeleteConversation();
  const updateConversation = useUpdateConversation();

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
        },
      ]
    : messages;

  // Filter conversations based on search query
  const filteredConversations = conversationsData?.conversations.filter((conv) =>
    conv.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    conv.summary?.toLowerCase().includes(searchQuery.toLowerCase())
  ) || [];

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setOpenMenuId(null);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Focus input when editing starts
  useEffect(() => {
    if (editingConversationId && editInputRef.current) {
      editInputRef.current.focus();
      editInputRef.current.select();
    }
  }, [editingConversationId]);

  // Handle prefilled question from navigation state (from Context Panel)
  useEffect(() => {
    const prefill = location.state?.prefillQuestion;
    if (prefill && typeof prefill === 'string') {
      setPrefillQuestion(prefill);
      // Clear navigation state to prevent re-use on re-renders
      window.history.replaceState({}, document.title);
    }
  }, [location]);

  const handleSendMessage = async (message: string) => {
    try {
      setErrorMessage(null);
      setIsStreaming(true);
      setStreamingMessage('');
      setStreamingSources([]);
      setStreamingSuggestedQuestions([]);
      setStreamingStatus('');
      setStreamingToolCalls([]);
      setStreamingToolResults([]);
      setActiveAgent(null);
      setPrefillQuestion(''); // Clear prefill after sending

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
          include_notes: includeNotes,
          socratic_mode: socraticMode,
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
        (_messageId) => {
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
        },
        // onAgent
        (agent) => {
          setActiveAgent(agent);
        },
        // onStatus
        (status) => {
          setStreamingStatus(status);
        },
        // onToolCall
        (toolCall) => {
          setStreamingToolCalls((prev) => [...prev, toolCall]);
        },
        // onToolResult
        (toolResult) => {
          setStreamingToolResults((prev) => [...prev, toolResult]);
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

  const handleMenuToggle = (e: React.MouseEvent, conversationId: string) => {
    e.stopPropagation();
    setOpenMenuId(openMenuId === conversationId ? null : conversationId);
  };

  const handleEditConversation = (e: React.MouseEvent, conversation: { id: string; title: string }) => {
    e.stopPropagation();
    setEditingConversationId(conversation.id);
    setEditTitle(conversation.title);
    setOpenMenuId(null);
  };

  const handleSaveEdit = async (e: React.FormEvent, originalTitle: string, conversationId: string) => {
    e.preventDefault();
    e.stopPropagation();

    if (!editTitle.trim()) {
      setEditTitle(originalTitle); // Reset to original
      setEditingConversationId(null);
      return;
    }

    try {
      await updateConversation.mutateAsync({
        id: conversationId,
        data: {
          title: editTitle.trim(),
        },
      });
      setEditingConversationId(null);
    } catch (error) {
      console.error('Failed to update conversation title:', error);
      setEditTitle(originalTitle); // Reset to original
      setEditingConversationId(null);
    }
  };

  const handleCancelEdit = (e: React.MouseEvent, originalTitle: string) => {
    e.stopPropagation();
    setEditTitle(originalTitle);
    setEditingConversationId(null);
  };

  const handleTogglePin = async (e: React.MouseEvent, conversationId: string, isPinned: boolean) => {
    e.stopPropagation();
    setOpenMenuId(null);

    try {
      await updateConversation.mutateAsync({
        id: conversationId,
        data: {
          is_pinned: !isPinned,
        },
      });
    } catch (error) {
      console.error('Failed to toggle pin:', error);
      setErrorMessage('Failed to pin/unpin conversation');
    }
  };

  const handleExportConversation = async (e: React.MouseEvent, conversationId: string) => {
    e.stopPropagation();
    setOpenMenuId(null);

    try {
      // Fetch the full conversation with messages
      const conversation = await chatService.getConversation(conversationId);
      downloadConversationAsMarkdown(conversation);
    } catch (error) {
      console.error('Failed to export conversation:', error);
      setErrorMessage('Failed to export conversation');
    }
  };

  const handleDeleteConversation = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    setOpenMenuId(null);
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

  const handleDetectLearningGaps = async (question: string) => {
    try {
      setIsLoadingGaps(true);
      setGapsQuestion(question);
      setShowLearningGaps(true);
      setLearningPath(undefined);
      setGapsError(null);

      // Get conversation history for context
      const history = messages.map(m => ({
        role: m.role,
        content: m.content
      }));

      const result = await learningGapsService.detectGaps(
        question,
        history
      );

      setLearningGaps(result.gaps);
      setGapsError(null);
    } catch (error: any) {
      console.error('Failed to detect learning gaps:', error);
      setLearningGaps([]);

      // Set user-friendly error message
      if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
        setGapsError('The analysis is taking longer than expected. This is a complex question that requires significant processing time. Please try again or simplify your question.');
      } else {
        setGapsError('Failed to analyze learning gaps. Please try again later.');
      }
    } finally {
      setIsLoadingGaps(false);
    }
  };

  const handleGenerateLearningPath = async () => {
    if (learningGaps.length === 0) return;

    try {
      setIsLoadingGaps(true);
      const result = await learningGapsService.generateLearningPath(
        gapsQuestion,
        learningGaps
      );
      setLearningPath(result);
    } catch (error) {
      console.error('Failed to generate learning path:', error);
    } finally {
      setIsLoadingGaps(false);
    }
  };

  const handleGenerateQuiz = async () => {
    if (messages.length === 0) return;

    try {
      setIsLoadingQuiz(true);

      // Get the last few messages to generate quiz from
      const recentMessages = messages.slice(-6); // Last 3 exchanges
      const content = recentMessages.map(m => `${m.role}: ${m.content}`).join('\n\n');

      // Use conversation title or first user message as title
      const title = conversationData?.title || messages.find(m => m.role === 'user')?.content.slice(0, 50) || 'Conversation';

      setQuizContentTitle(title);

      const result = await metabolizationService.generateQuiz({
        content,
        content_type: 'note',
        content_title: title,
        num_questions: 3,
      });

      setQuizQuestions(result.questions);
      setShowMetabolizationQuiz(true);
    } catch (error) {
      console.error('Failed to generate quiz:', error);
    } finally {
      setIsLoadingQuiz(false);
    }
  };

  const handleSubmitQuizAnswer = async (
    question: MetabolizationQuestion,
    answer: string
  ): Promise<AnswerEvaluationResponse> => {
    // Get conversation content for context
    const recentMessages = messages.slice(-6);
    const contentContext = recentMessages.map(m => `${m.role}: ${m.content}`).join('\n\n');

    return await metabolizationService.evaluateAnswer({
      question,
      user_answer: answer,
      content_context: contentContext,
    });
  };

  const handleQuizComplete = (score: number) => {
    console.log('Quiz completed with score:', score);
    // Could store score in database here
  };

  const handleCaptureSnapshot = async () => {
    if (!selectedConversationId || messages.length === 0) return;

    try {
      // Extract a topic from the conversation
      const userMessages = messages.filter(m => m.role === 'user');
      const lastUserMessage = userMessages[userMessages.length - 1];
      const topic = lastUserMessage?.content.slice(0, 100) || 'Conversation Topic';

      // Create snapshot
      await createSnapshot.mutateAsync({
        topic,
        conversation_messages: messages.map(m => ({
          role: m.role,
          content: m.content
        })),
        conversation_id: selectedConversationId,
      });

      // Show success message (could add a toast notification here)
      console.log('Snapshot captured successfully');
    } catch (error) {
      console.error('Failed to capture snapshot:', error);
    }
  };

  // Define keyboard shortcuts
  const shortcuts: KeyboardShortcut[] = [
    {
      key: 'k',
      ctrl: true,
      handler: () => {
        searchInputRef.current?.focus();
        searchInputRef.current?.select();
      },
      description: 'Focus search',
      category: 'Navigation',
    },
    {
      key: 'n',
      ctrl: true,
      handler: () => {
        handleNewChat();
      },
      description: 'New chat',
      category: 'Actions',
    },
    {
      key: 'b',
      ctrl: true,
      handler: () => {
        setIsSidebarCollapsed(!isSidebarCollapsed);
      },
      description: 'Toggle sidebar',
      category: 'Navigation',
    },
    {
      key: 'Escape',
      handler: () => {
        setOpenMenuId(null);
        setShowShortcutsModal(false);
      },
      description: 'Close menus/modals',
      category: 'General',
    },
    {
      key: '?',
      shift: true,
      handler: () => {
        setShowShortcutsModal(true);
      },
      description: 'Show keyboard shortcuts',
      category: 'Help',
    },
  ];

  // Register keyboard shortcuts
  useKeyboardShortcuts(shortcuts);

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
                  ref={searchInputRef}
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
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1 min-w-0">
                        {editingConversationId === conv.id ? (
                          <form onSubmit={(e) => handleSaveEdit(e, conv.title, conv.id)} className="mb-1">
                            <input
                              ref={editInputRef}
                              type="text"
                              value={editTitle}
                              onChange={(e) => setEditTitle(e.target.value)}
                              onBlur={(e) => {
                                // Convert blur to form submission
                                const form = e.currentTarget.form;
                                if (form) {
                                  form.requestSubmit();
                                }
                              }}
                              onKeyDown={(e) => {
                                if (e.key === 'Escape') {
                                  handleCancelEdit(e as any, conv.title);
                                }
                              }}
                              className="w-full px-2 py-1 text-sm font-medium border-2 border-blue-500 dark:border-blue-400 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                              onClick={(e) => e.stopPropagation()}
                            />
                          </form>
                        ) : (
                          <h3 className="text-sm font-medium text-gray-900 dark:text-white truncate flex items-center gap-1.5">
                            {conv.is_pinned && <Pin size={12} className="text-blue-600 dark:text-blue-400 flex-shrink-0" />}
                            <span className="truncate">{conv.title}</span>
                          </h3>
                        )}
                        <div className="flex items-center gap-2 mt-1">
                          <p className="text-xs text-gray-500 dark:text-gray-400">
                            {new Date(conv.updated_at).toLocaleDateString('en-US', {
                              month: 'short',
                              day: 'numeric',
                              year: 'numeric',
                            })}
                          </p>
                          {conv.message_count !== undefined && (
                            <span className="text-xs text-gray-400 dark:text-gray-500">
                              • {conv.message_count} {conv.message_count === 1 ? 'message' : 'messages'}
                            </span>
                          )}
                        </div>
                      </div>

                      {/* Three-dot menu */}
                      <div className="relative flex-shrink-0" ref={openMenuId === conv.id ? menuRef : null}>
                        <button
                          onClick={(e) => handleMenuToggle(e, conv.id)}
                          className="p-1.5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-colors"
                          title="More options"
                        >
                          <MoreVertical size={16} />
                        </button>

                        {openMenuId === conv.id && (
                          <div className="absolute right-0 top-full mt-1 w-40 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg z-10">
                            <button
                              onClick={(e) => handleTogglePin(e, conv.id, conv.is_pinned)}
                              className="w-full px-4 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-t-lg transition-colors flex items-center gap-2"
                            >
                              {conv.is_pinned ? <PinOff size={14} /> : <Pin size={14} />}
                              {conv.is_pinned ? 'Unpin' : 'Pin'}
                            </button>
                            <button
                              onClick={(e) => handleEditConversation(e, conv)}
                              className="w-full px-4 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                            >
                              Edit
                            </button>
                            <button
                              onClick={(e) => handleExportConversation(e, conv.id)}
                              className="w-full px-4 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors flex items-center gap-2"
                            >
                              <Download size={14} />
                              Export as MD
                            </button>
                            <button
                              onClick={(e) => handleDeleteConversation(e, conv.id)}
                              className="w-full px-4 py-2 text-left text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-b-lg transition-colors"
                              disabled={deleteConversation.isPending}
                            >
                              Delete
                            </button>
                          </div>
                        )}
                      </div>
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

          {/* Loading Status - shows during streaming */}
          {isStreaming && streamingStatus && !streamingMessage && (
            <div className="px-6 py-4">
              <div className="flex items-center gap-3 text-gray-600 dark:text-gray-400">
                <div className="flex gap-1">
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                </div>
                <span className="text-sm">{streamingStatus}</span>
              </div>
            </div>
          )}

          {/* Tool Activity Timeline - Show when tool calls are active */}
          {(streamingToolCalls.length > 0 || streamingToolResults.length > 0) && isStreaming && (
            <div className="px-6 py-4">
              <ActivityTimeline
                toolCalls={streamingToolCalls}
                toolResults={streamingToolResults}
              />
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

          {/* Settings and Learning Tools - Organized Layout */}
          <div className="px-6 pb-3 space-y-2.5">
            {/* Clear Chat Button - shows when there are messages */}
            {displayMessages.length > 0 && (
              <div className="flex justify-center pb-0.5">
                <button
                  onClick={handleClearChat}
                  className="flex items-center gap-1.5 px-2.5 py-1 text-xs text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-800 rounded-md transition-colors"
                >
                  <RotateCcw size={12} />
                  Clear Chat
                </button>
              </div>
            )}

            {/* Search & Filter Settings - Horizontal */}
            <div className="flex flex-wrap gap-1.5">
              {/* Web Search Toggle */}
              <button
                onClick={() => setWebSearchEnabled(!webSearchEnabled)}
                className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-xs transition-colors ${
                  webSearchEnabled
                    ? 'bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400 border border-green-300 dark:border-green-700'
                    : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 border border-gray-300 dark:border-gray-700 hover:bg-gray-200 dark:hover:bg-gray-700'
                }`}
              >
                <Globe size={13} />
                <span className="whitespace-nowrap">{webSearchEnabled ? '✓ Web' : 'Docs only'}</span>
              </button>

              {/* Include Notes Toggle */}
              <button
                onClick={() => setIncludeNotes(!includeNotes)}
                className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-xs transition-colors ${
                  includeNotes
                    ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-400 border border-blue-300 dark:border-blue-700'
                    : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 border border-gray-300 dark:border-gray-700 hover:bg-gray-200 dark:hover:bg-gray-700'
                }`}
              >
                <MessageSquare size={13} />
                <span className="whitespace-nowrap">{includeNotes ? '✓ Notes' : 'Verified only'}</span>
              </button>

              {/* Socratic Learning Mode Toggle */}
              <button
                onClick={() => setSocraticMode(!socraticMode)}
                className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-xs transition-colors ${
                  socraticMode
                    ? 'bg-purple-50 dark:bg-purple-900/20 text-purple-700 dark:text-purple-400 border border-purple-300 dark:border-purple-700'
                    : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 border border-gray-300 dark:border-gray-700 hover:bg-gray-200 dark:hover:bg-gray-700'
                }`}
                title="Enable Socratic Learning Mode: AI teaches through guided questions instead of direct answers"
              >
                <GraduationCap size={13} />
                <span className="whitespace-nowrap">{socraticMode ? '✓ Socratic' : 'Direct'}</span>
              </button>
            </div>

            {/* Learning Tools - Only show when conversation has messages */}
            {messages.length > 0 && (
              <div className="pt-1">
                <div className="text-[10px] uppercase tracking-wider text-gray-500 dark:text-gray-400 font-semibold mb-1.5 px-1">
                  Learning Tools
                </div>
                <div className="grid grid-cols-2 gap-1.5">
                  {/* Learning Gaps Detector */}
                  <button
                    onClick={() => {
                      const lastUserMessage = messages.filter(m => m.role === 'user').pop();
                      if (lastUserMessage) {
                        handleDetectLearningGaps(lastUserMessage.content);
                      }
                    }}
                    className="flex items-center gap-1.5 px-2 py-1.5 rounded-md text-xs transition-colors bg-gradient-to-r from-orange-50 to-yellow-50 dark:from-orange-900/20 dark:to-yellow-900/20 text-orange-700 dark:text-orange-400 border border-orange-300 dark:border-orange-700 hover:from-orange-100 hover:to-yellow-100 dark:hover:from-orange-900/30 dark:hover:to-yellow-900/30"
                    title="Detect foundational knowledge gaps"
                  >
                    <Lightbulb size={13} />
                    <span className="whitespace-nowrap">Gaps</span>
                  </button>

                  {/* Metabolization Quiz */}
                  <button
                    onClick={handleGenerateQuiz}
                    disabled={isLoadingQuiz}
                    className="flex items-center gap-1.5 px-2 py-1.5 rounded-md text-xs transition-colors bg-gradient-to-r from-purple-50 to-blue-50 dark:from-purple-900/20 dark:to-blue-900/20 text-purple-700 dark:text-purple-400 border border-purple-300 dark:border-purple-700 hover:from-purple-100 hover:to-blue-100 dark:hover:from-purple-900/30 dark:hover:to-blue-900/30 disabled:opacity-50 disabled:cursor-not-allowed"
                    title="Test your understanding with questions"
                  >
                    <Brain size={13} />
                    <span className="whitespace-nowrap">{isLoadingQuiz ? 'Loading...' : 'Quiz Me'}</span>
                  </button>

                  {/* Knowledge Evolution Snapshot */}
                  <button
                    onClick={handleCaptureSnapshot}
                    disabled={createSnapshot.isPending}
                    className="flex items-center gap-1.5 px-2 py-1.5 rounded-md text-xs transition-colors bg-gradient-to-r from-green-50 to-teal-50 dark:from-green-900/20 dark:to-teal-900/20 text-green-700 dark:text-green-400 border border-green-300 dark:border-green-700 hover:from-green-100 hover:to-teal-100 dark:hover:from-green-900/30 dark:hover:to-teal-900/30 disabled:opacity-50 disabled:cursor-not-allowed"
                    title="Capture your current understanding"
                  >
                    <BookOpen size={13} />
                    <span className="whitespace-nowrap">{createSnapshot.isPending ? 'Saving...' : 'Snapshot'}</span>
                  </button>

                  {/* View Evolution Timeline */}
                  <button
                    onClick={() => setShowEvolutionTimeline(true)}
                    className="flex items-center gap-1.5 px-2 py-1.5 rounded-md text-xs transition-colors bg-gradient-to-r from-indigo-50 to-purple-50 dark:from-indigo-900/20 dark:to-purple-900/20 text-indigo-700 dark:text-indigo-400 border border-indigo-300 dark:border-indigo-700 hover:from-indigo-100 hover:to-purple-100 dark:hover:from-indigo-900/30 dark:hover:to-purple-900/30"
                    title="View knowledge evolution timeline"
                  >
                    <Clock size={13} />
                    <span className="whitespace-nowrap">Timeline</span>
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Active Agent Indicator */}
          {activeAgent && (
            <div className="px-6 pb-2">
              <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 rounded-md text-sm border border-blue-200 dark:border-blue-800">
                <span className="font-medium">{activeAgent.display_name}</span>
                <span className="text-blue-500 dark:text-blue-400">•</span>
                <span className="text-xs text-blue-600 dark:text-blue-400">{activeAgent.description}</span>
              </div>
            </div>
          )}

          {/* Token Usage Indicator */}
          {selectedConversationId && (
            <div className="px-6 pb-3">
              <TokenUsage conversationId={selectedConversationId} />
            </div>
          )}

          <ChatInput
            onSend={handleSendMessage}
            disabled={isStreaming}
            initialValue={prefillQuestion}
          />
        </main>
      </div>

      {/* Learning Gaps Panel */}
      <LearningGapsPanel
        isOpen={showLearningGaps}
        onClose={() => setShowLearningGaps(false)}
        userQuestion={gapsQuestion}
        gaps={learningGaps}
        learningPath={learningPath}
        isLoading={isLoadingGaps}
        error={gapsError}
        onGeneratePath={handleGenerateLearningPath}
      />

      {/* Metabolization Quiz */}
      <MetabolizationQuiz
        isOpen={showMetabolizationQuiz}
        onClose={() => setShowMetabolizationQuiz(false)}
        contentTitle={quizContentTitle}
        contentType="note"
        questions={quizQuestions}
        isLoading={isLoadingQuiz}
        onSubmitAnswer={handleSubmitQuizAnswer}
        onComplete={handleQuizComplete}
      />

      {/* Knowledge Evolution Timeline */}
      <KnowledgeEvolutionTimeline
        isOpen={showEvolutionTimeline}
        onClose={() => setShowEvolutionTimeline(false)}
      />

      {/* Keyboard Shortcuts Modal */}
      <KeyboardShortcutsModal
        isOpen={showShortcutsModal}
        onClose={() => setShowShortcutsModal(false)}
        shortcuts={shortcuts}
      />
    </div>
  );
}
