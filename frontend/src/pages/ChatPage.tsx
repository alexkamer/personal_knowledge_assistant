/**
 * Chat page for AI-powered Q&A using RAG.
 */
import { useState, useRef, useEffect, useCallback, useMemo, useReducer } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useLocation, useSearchParams } from 'react-router-dom';
import { Plus, MoreVertical, AlertCircle, Search, X, ChevronLeft, ChevronRight, Download, Pin, PinOff } from 'lucide-react';
import { MessageList } from '@/components/chat/MessageList';
import { ChatInput } from '@/components/chat/ChatInput';
import { Pagination } from '@/components/ui/Pagination';
import { TokenUsage } from '@/components/chat/TokenUsage';
import { LearningToolsFAB } from '@/components/chat/LearningToolsFAB';
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
import { usePaginationState } from '@/hooks/usePaginationState';
import { useDebouncedValue } from '@/hooks/useDebouncedValue';
import { chatService } from '@/services/chatService';
import { learningGapsService, type LearningGap, type LearningPathResponse } from '@/services/learningGapsService';
import { metabolizationService, type MetabolizationQuestion, type AnswerEvaluationResponse } from '@/services/metabolizationService';
import { useCreateSnapshot } from '@/hooks/useKnowledgeEvolution';
import { downloadConversationAsMarkdown } from '@/utils/exportMarkdown';
import { useKeyboardShortcuts, type KeyboardShortcut } from '@/hooks/useKeyboardShortcuts';
import type { Message, ToolCall, ToolResult } from '@/types/chat';

// Streaming state types
interface StreamingState {
  isStreaming: boolean;
  userMessage: string;
  message: string;
  sources: any[];
  suggestedQuestions: string[];
  status: string;
  toolCalls: ToolCall[];
  toolResults: ToolResult[];
  activeAgent: { name: string; display_name: string; description: string } | null;
}

// Streaming state actions
type StreamingAction =
  | { type: 'START_STREAMING'; payload: string }
  | { type: 'UPDATE_CHUNK'; payload: string }
  | { type: 'UPDATE_SOURCES'; payload: any[] }
  | { type: 'UPDATE_SUGGESTED_QUESTIONS'; payload: string[] }
  | { type: 'UPDATE_STATUS'; payload: string }
  | { type: 'ADD_TOOL_CALL'; payload: ToolCall }
  | { type: 'ADD_TOOL_RESULT'; payload: ToolResult }
  | { type: 'UPDATE_AGENT'; payload: { name: string; display_name: string; description: string } | null }
  | { type: 'RESET' };

// Initial streaming state
const initialStreamingState: StreamingState = {
  isStreaming: false,
  userMessage: '',
  message: '',
  sources: [],
  suggestedQuestions: [],
  status: '',
  toolCalls: [],
  toolResults: [],
  activeAgent: null,
};

// Streaming state reducer
function streamingReducer(state: StreamingState, action: StreamingAction): StreamingState {
  switch (action.type) {
    case 'START_STREAMING':
      return {
        ...initialStreamingState,
        isStreaming: true,
        userMessage: action.payload,
      };
    case 'UPDATE_CHUNK':
      return {
        ...state,
        message: state.message + action.payload,
      };
    case 'UPDATE_SOURCES':
      return {
        ...state,
        sources: action.payload,
      };
    case 'UPDATE_SUGGESTED_QUESTIONS':
      return {
        ...state,
        suggestedQuestions: action.payload,
      };
    case 'UPDATE_STATUS':
      return {
        ...state,
        status: action.payload,
      };
    case 'ADD_TOOL_CALL':
      return {
        ...state,
        toolCalls: [...state.toolCalls, action.payload],
      };
    case 'ADD_TOOL_RESULT':
      return {
        ...state,
        toolResults: [...state.toolResults, action.payload],
      };
    case 'UPDATE_AGENT':
      return {
        ...state,
        activeAgent: action.payload,
      };
    case 'RESET':
      return initialStreamingState;
    default:
      return state;
  }
}

export function ChatPage() {
  const [searchParams, setSearchParams] = useSearchParams();

  // URL state management
  const selectedConversationId = searchParams.get('conv') || null;
  const searchQuery = searchParams.get('search') || '';
  const isSidebarCollapsed = searchParams.get('hideSidebar') === 'true';

  // Local state (not persisted in URL)
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [sourceFilter, setSourceFilter] = useState<'general' | 'docs' | 'web'>('general'); // Default to general (no RAG)
  const [socraticMode, setSocraticMode] = useState<boolean>(false); // Default to false - direct answers
  const [selectedModel, setSelectedModel] = useState<string>(() => {
    // Load from localStorage or default to gemini-2.5-flash
    return localStorage.getItem('preferred_model') || 'gemini-2.5-flash';
  });

  // Streaming state (consolidated with useReducer for performance)
  const [streamingState, dispatchStreaming] = useReducer(streamingReducer, initialStreamingState);

  const [openMenuId, setOpenMenuId] = useState<string | null>(null);
  const [editingConversationId, setEditingConversationId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState('');
  const [showShortcutsModal, setShowShortcutsModal] = useState(false);
  const [prefillQuestion, setPrefillQuestion] = useState<string>('');

  // Pagination state
  const pagination = usePaginationState({
    defaultLimit: 20,
    paramPrefix: 'conv_',
  });

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

  // Drag and drop state
  const [isDraggingFiles, setIsDraggingFiles] = useState(false);
  const dragCounterRef = useRef(0);
  const dragTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Knowledge Evolution Timeline state
  const [showEvolutionTimeline, setShowEvolutionTimeline] = useState(false);

  const createSnapshot = useCreateSnapshot();

  const menuRef = useRef<HTMLDivElement>(null);
  const editInputRef = useRef<HTMLInputElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);

  const queryClient = useQueryClient();
  const location = useLocation();

  // Fetch conversations with pagination
  const { data: conversationsData } = useConversations(
    pagination.offset,
    pagination.limit
  );
  const { data: conversationData, isLoading: isLoadingConversation } = useConversation(
    selectedConversationId
  );
  const deleteConversation = useDeleteConversation();
  const updateConversation = useUpdateConversation();

  // URL param update helpers
  const updateURLParam = useCallback((key: string, value: string | null) => {
    setSearchParams((prev) => {
      const newParams = new URLSearchParams(prev);
      if (value) {
        newParams.set(key, value);
      } else {
        newParams.delete(key);
      }
      return newParams;
    });
  }, [setSearchParams]);

  const handleSelectConversation = useCallback((convId: string) => {
    updateURLParam('conv', convId);
  }, [updateURLParam]);

  const handleSearchChange = useCallback((query: string) => {
    setSearchParams((prev) => {
      const newParams = new URLSearchParams(prev);
      if (query) {
        newParams.set('search', query);
      } else {
        newParams.delete('search');
      }
      // Reset to page 1 when searching
      newParams.delete('conv_page');
      return newParams;
    });
  }, [setSearchParams]);

  const handleToggleSidebar = useCallback(() => {
    updateURLParam('hideSidebar', !isSidebarCollapsed ? 'true' : null);
  }, [updateURLParam, isSidebarCollapsed]);

  const messages: Message[] = conversationData?.messages || [];

  // Add streaming messages to the messages if currently streaming (memoized for performance)
  const displayMessages: Message[] = useMemo(() => {
    if (!streamingState.isStreaming) return messages;

    const streamingMessages: Message[] = [];

    // Add user message immediately
    if (streamingState.userMessage) {
      streamingMessages.push({
        id: 'streaming-user',
        conversation_id: selectedConversationId || '',
        role: 'user' as const,
        content: streamingState.userMessage,
        created_at: new Date().toISOString(),
      });
    }

    // Add assistant message (with status as placeholder if no content yet)
    streamingMessages.push({
      id: 'streaming-assistant',
      conversation_id: selectedConversationId || '',
      role: 'assistant' as const,
      content: streamingState.message,
      sources: streamingState.sources.length > 0 ? streamingState.sources : undefined,
      suggested_questions: streamingState.suggestedQuestions.length > 0 ? streamingState.suggestedQuestions : undefined,
      created_at: new Date().toISOString(),
      // Pass status for rendering as placeholder
      metadata: { status: streamingState.status },
    });

    return [...messages, ...streamingMessages];
  }, [messages, streamingState.isStreaming, streamingState.userMessage, streamingState.message, streamingState.sources, streamingState.suggestedQuestions, streamingState.status, selectedConversationId]);

  // Debounce search query for better performance
  const debouncedSearchQuery = useDebouncedValue(searchQuery, 300);

  // Filter conversations based on debounced search query
  const filteredConversations = useMemo(() => {
    const conversations = conversationsData?.conversations || [];
    if (!debouncedSearchQuery) return conversations;

    return conversations.filter((conv) =>
      conv.title.toLowerCase().includes(debouncedSearchQuery.toLowerCase()) ||
      conv.summary?.toLowerCase().includes(debouncedSearchQuery.toLowerCase())
    );
  }, [conversationsData?.conversations, debouncedSearchQuery]);

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

  // Save selected model to localStorage when it changes
  useEffect(() => {
    localStorage.setItem('preferred_model', selectedModel);
  }, [selectedModel]);

  const handleSendMessage = useCallback(async (message: string, files?: File[]) => {
    try {
      setErrorMessage(null);
      // Store the user message for immediate display
      dispatchStreaming({ type: 'START_STREAMING', payload: message });
      setPrefillQuestion(''); // Clear prefill after sending

      let newConversationId = selectedConversationId;

      await chatService.sendMessageStream(
        {
          message,
          conversation_id: selectedConversationId || undefined,
          conversation_title: selectedConversationId ? undefined : undefined,  // Let backend generate title
          model: selectedModel,
          include_web_search: sourceFilter === 'web',
          include_notes: sourceFilter === 'docs' ? true : false, // docs mode includes all sources
          socratic_mode: socraticMode,
          skip_rag: sourceFilter === 'general', // Skip RAG for general knowledge mode
          files, // Pass files to service
        },
        // onChunk
        (chunk) => {
          dispatchStreaming({ type: 'UPDATE_CHUNK', payload: chunk });
        },
        // onSources
        (sources) => {
          dispatchStreaming({ type: 'UPDATE_SOURCES', payload: sources });
        },
        // onConversationId
        (conversationId) => {
          if (!newConversationId) {
            newConversationId = conversationId;
            updateURLParam('conv', conversationId);
          }
        },
        // onDone
        (_messageId) => {
          dispatchStreaming({ type: 'RESET' });
          // Only invalidate the specific conversation to avoid expensive full list refetch
          if (newConversationId) {
            queryClient.invalidateQueries({ queryKey: ['conversations', newConversationId] });
            // Invalidate list only to update the sidebar title/message count
            queryClient.invalidateQueries({ queryKey: ['conversations'] });
          }
        },
        // onError
        (error) => {
          dispatchStreaming({ type: 'RESET' });
          setErrorMessage(error);
        },
        // onSuggestedQuestions
        (questions) => {
          dispatchStreaming({ type: 'UPDATE_SUGGESTED_QUESTIONS', payload: questions });
        },
        // onAgent
        (agent) => {
          dispatchStreaming({ type: 'UPDATE_AGENT', payload: agent });
        },
        // onStatus
        (status) => {
          dispatchStreaming({ type: 'UPDATE_STATUS', payload: status });
        },
        // onToolCall
        (toolCall) => {
          dispatchStreaming({ type: 'ADD_TOOL_CALL', payload: toolCall });
        },
        // onToolResult
        (toolResult) => {
          dispatchStreaming({ type: 'ADD_TOOL_RESULT', payload: toolResult });
        }
      );
    } catch (error: any) {
      console.error('Failed to send message:', error);
      const errorDetail = error?.message || 'Failed to send message';
      setErrorMessage(errorDetail);
      dispatchStreaming({ type: 'RESET' });
    }
  }, [selectedConversationId, selectedModel, sourceFilter, socraticMode, updateURLParam, queryClient]);

  const handleNewChat = useCallback(() => {
    updateURLParam('conv', null);
    setErrorMessage(null);
  }, [updateURLParam]);

  // Drag and drop handlers for the main chat area
  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    dragCounterRef.current++;
    // Check if dragging files (dataTransfer.items is more reliable than types)
    if (e.dataTransfer.items && e.dataTransfer.items.length > 0) {
      setIsDraggingFiles(true);
    }
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    dragCounterRef.current--;
    if (dragCounterRef.current === 0) {
      setIsDraggingFiles(false);
    }
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();

    // Clear any existing timeout
    if (dragTimeoutRef.current) {
      clearTimeout(dragTimeoutRef.current);
    }

    // Set a timeout - if no dragover for 100ms, assume drag left the window
    dragTimeoutRef.current = setTimeout(() => {
      setIsDraggingFiles(false);
      dragCounterRef.current = 0;
    }, 100);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (dragTimeoutRef.current) {
      clearTimeout(dragTimeoutRef.current);
    }
    setIsDraggingFiles(false);
    dragCounterRef.current = 0;

    // Extract files and dispatch a drop event to the ChatInput
    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      // Find the ChatInput's drop zone and dispatch drop event to it
      const chatInputContainer = document.querySelector('[data-chat-input-dropzone]');
      if (chatInputContainer) {
        const dropEvent = new DragEvent('drop', {
          bubbles: true,
          cancelable: true,
          dataTransfer: e.dataTransfer,
        });
        chatInputContainer.dispatchEvent(dropEvent);
      }
    }
  }, []);

  // Cleanup drag state when drag leaves the browser window or file is dropped
  useEffect(() => {
    const handleDocumentDragOver = (e: DragEvent) => {
      // Track that we're still dragging inside the window
      e.preventDefault();
    };

    const handleDocumentDragLeave = (e: DragEvent) => {
      // Check if we're leaving the window entirely
      // This fires when relatedTarget is null (leaving document body)
      const rect = document.documentElement.getBoundingClientRect();
      const isOutside = e.clientX <= 0 || e.clientX >= rect.width ||
                       e.clientY <= 0 || e.clientY >= rect.height;

      if (isOutside || !e.relatedTarget) {
        setIsDraggingFiles(false);
        dragCounterRef.current = 0;
      }
    };

    const handleDocumentDrop = () => {
      // Reset state when any drop happens
      setIsDraggingFiles(false);
      dragCounterRef.current = 0;
    };

    const handleDocumentDragEnd = () => {
      // Reset when drag operation ends
      setIsDraggingFiles(false);
      dragCounterRef.current = 0;
    };

    document.addEventListener('dragover', handleDocumentDragOver);
    document.addEventListener('dragleave', handleDocumentDragLeave);
    document.addEventListener('drop', handleDocumentDrop);
    document.addEventListener('dragend', handleDocumentDragEnd);

    return () => {
      document.removeEventListener('dragover', handleDocumentDragOver);
      document.removeEventListener('dragleave', handleDocumentDragLeave);
      document.removeEventListener('drop', handleDocumentDrop);
      document.removeEventListener('dragend', handleDocumentDragEnd);
    };
  }, []);

  // Removed duplicate - now using the URL-based version above

  const handleMenuToggle = useCallback((e: React.MouseEvent, conversationId: string) => {
    e.stopPropagation();
    setOpenMenuId(openMenuId === conversationId ? null : conversationId);
  }, [openMenuId]);

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
          updateURLParam('conv', null);
        }
      } catch (error) {
        console.error('Failed to delete conversation:', error);
      }
    }
  };

  const handleRegenerateMessage = useCallback(async (messageId: string) => {
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
  }, [messages, handleSendMessage]);

  const handleDetectLearningGaps = useCallback(async (question: string) => {
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
  }, [messages]);

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
        handleToggleSidebar();
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
    <div className="h-screen flex bg-gray-950 relative">
      {/* Command Center Layout - No redundant header! */}
      <div className="flex-1 flex overflow-hidden relative z-0">
        {/* Sidebar - Context Panel */}
        <aside className={`bg-gray-900/95 backdrop-blur-md border-r border-cyan-400/30 flex flex-col transition-all duration-300 ease-in-out relative z-10 ${
          isSidebarCollapsed ? 'w-0' : 'w-72'
        }`}>
          <div className={`${isSidebarCollapsed ? 'opacity-0' : 'opacity-100'} transition-opacity duration-300 flex flex-col h-full`}>
            {/* Sidebar Header */}
            <div className="px-4 py-3 border-b border-gray-700 flex-shrink-0">
              <div className="flex items-center justify-between mb-3">
                <h2 className="text-sm font-semibold text-white">History</h2>
                <button
                  onClick={handleToggleSidebar}
                  className="p-1 text-gray-400 hover:text-white hover:bg-gray-800 rounded transition-colors"
                  title="Hide sidebar"
                >
                  <ChevronLeft size={18} />
                </button>
              </div>
              {/* New Chat Button */}
              <button
                onClick={handleNewChat}
                className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-primary-500 hover:bg-primary-600 text-white font-medium text-sm rounded-lg transition-all shadow-md"
              >
                <Plus size={16} />
                New Chat
              </button>
            </div>

            {/* Search Input */}
            <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-800 flex-shrink-0">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 dark:text-gray-400" size={16} />
                <input
                  ref={searchInputRef}
                  type="text"
                  placeholder="Search..."
                  value={searchQuery}
                  onChange={(e) => handleSearchChange(e.target.value)}
                  className="w-full pl-9 pr-9 py-1.5 text-sm border border-gray-300 dark:border-gray-700 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-stone-500 dark:placeholder-stone-400 focus:outline-none focus:ring-1 focus:ring-stone-400 focus:border-transparent transition-colors"
                />
                {searchQuery && (
                  <button
                    onClick={() => handleSearchChange('')}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                  >
                    <X size={18} />
                  </button>
                )}
              </div>
            </div>

            <div className="flex-1 overflow-y-auto min-h-0 flex flex-col">
            {conversationsData && conversationsData.conversations.length > 0 ? (
              filteredConversations.length > 0 ? (
                <>
                <div className="flex-1 overflow-y-auto divide-y divide-stone-200 dark:divide-stone-800">
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
                            <span className="text-xs text-gray-500 dark:text-gray-400">
                              • {conv.message_count} {conv.message_count === 1 ? 'message' : 'messages'}
                            </span>
                          )}
                        </div>
                      </div>

                      {/* Three-dot menu */}
                      <div className="relative flex-shrink-0" ref={openMenuId === conv.id ? menuRef : null}>
                        <button
                          onClick={(e) => handleMenuToggle(e, conv.id)}
                          className="p-1.5 text-gray-400 hover:text-gray-600 dark:text-gray-400 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-600 rounded transition-colors"
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

              {/* Pagination Controls */}
              {conversationsData && conversationsData.total > pagination.limit && (
                <div className="flex-shrink-0 px-4 py-3 border-t border-gray-700">
                  <Pagination
                    currentPage={pagination.page}
                    totalPages={pagination.totalPages(conversationsData.total)}
                    onPageChange={pagination.setPage}
                    hasNext={pagination.hasNextPage(conversationsData.total)}
                    hasPrev={pagination.hasPrevPage()}
                    showPageNumbers={false}
                    showFirstLast={false}
                  />
                </div>
              )}
              </>
              ) : (
                <div className="p-8 text-center text-gray-500 dark:text-gray-300">
                  <Search className="mx-auto mb-3 text-gray-400 dark:text-gray-400" size={32} />
                  <p className="text-sm font-medium">No conversations found</p>
                  <p className="text-xs mt-2">Try a different search term</p>
                  <button
                    onClick={() => handleSearchChange('')}
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
              onClick={handleToggleSidebar}
              className="absolute top-3 left-2 p-1 text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-800 rounded transition-colors z-10"
              title="Show sidebar"
            >
              <ChevronRight size={20} />
            </button>
          )}
        </aside>

        {/* Main Theater */}
        <main
          className="flex-1 flex flex-col bg-gray-950 overflow-hidden relative"
          onDragEnter={handleDragEnter}
          onDragLeave={handleDragLeave}
          onDragOver={handleDragOver}
          onDrop={handleDrop}
        >
          {/* Drag and Drop Overlay */}
          {isDraggingFiles && (
            <div className="absolute inset-0 bg-indigo-950/80 backdrop-blur-sm flex items-center justify-center z-50 pointer-events-none">
              <div className="text-center">
                <div className="w-24 h-24 mx-auto mb-6 rounded-full bg-indigo-500/20 border-4 border-dashed border-indigo-400 flex items-center justify-center">
                  <svg className="w-12 h-12 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                </div>
                <h3 className="text-2xl font-bold text-white mb-2">Drop files to attach</h3>
                <p className="text-indigo-300 text-lg">PDF, DOCX, TXT, MD files (max 25MB each)</p>
              </div>
            </div>
          )}

          {/* Error Banner */}
          {errorMessage && (
            <div className="max-w-3xl mx-auto w-full px-4 sm:px-6 mt-4">
              <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg flex items-start gap-3">
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
            </div>
          )}

          {/* Tool Activity Timeline - Show when tool calls are active */}
          {(streamingState.toolCalls.length > 0 || streamingState.toolResults.length > 0) && streamingState.isStreaming && (
            <div className="max-w-3xl mx-auto w-full px-4 sm:px-6 py-4">
              <ActivityTimeline
                toolCalls={streamingState.toolCalls}
                toolResults={streamingState.toolResults}
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

          {/* Active Agent Indicator */}
          {streamingState.activeAgent && (
            <div className="max-w-3xl mx-auto w-full px-4 sm:px-6 pb-2">
              <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 rounded-md text-sm border border-blue-200 dark:border-blue-800">
                <span className="font-medium">{streamingState.activeAgent.display_name}</span>
                <span className="text-blue-500 dark:text-blue-400">•</span>
                <span className="text-xs text-blue-600 dark:text-blue-400">{streamingState.activeAgent.description}</span>
              </div>
            </div>
          )}

          <ChatInput
            onSend={handleSendMessage}
            disabled={streamingState.isStreaming}
            initialValue={prefillQuestion}
            selectedModel={selectedModel}
            onModelChange={setSelectedModel}
            sourceFilter={sourceFilter}
            onSourceFilterChange={setSourceFilter}
            socraticMode={socraticMode}
            onSocraticModeToggle={() => setSocraticMode(!socraticMode)}
          />

          {/* Learning Tools FAB - Only show when conversation has messages */}
          {messages.length > 0 && (
            <LearningToolsFAB
              onDetectGaps={() => {
                const lastUserMessage = messages.filter(m => m.role === 'user').pop();
                if (lastUserMessage) {
                  handleDetectLearningGaps(lastUserMessage.content);
                }
              }}
              onGenerateQuiz={handleGenerateQuiz}
              onCaptureSnapshot={handleCaptureSnapshot}
              onViewTimeline={() => setShowEvolutionTimeline(true)}
              isLoadingQuiz={isLoadingQuiz}
              isLoadingSnapshot={createSnapshot.isPending}
              disabled={streamingState.isStreaming}
            />
          )}
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
