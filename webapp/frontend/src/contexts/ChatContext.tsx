/**
 * Chat Context - Real-time Chat State Management
 * Manages conversations, messages, and WebSocket connections
 */

import React, { createContext, useContext, useReducer, useEffect, ReactNode } from 'react';
import io from 'socket.io-client';
import apiService, { ChatMessage, Conversation } from '../services/api';
import config from '../config/config';

interface ChatState {
  conversations: Conversation[];
  currentConversation: Conversation | null;
  messages: ChatMessage[];
  isLoading: boolean;
  isConnected: boolean;
  isTyping: boolean;
  error: string | null;
  availableModels: string[];
  selectedModel: string;
}

interface ChatContextType extends ChatState {
  // Conversation management
  createConversation: (title?: string) => Promise<boolean>;
  selectConversation: (conversationId: string) => Promise<boolean>;
  deleteConversation: (conversationId: string) => Promise<boolean>;

  // Message management
  sendMessage: (content: string, options?: SendMessageOptions) => Promise<boolean>;
  regenerateMessage: (messageId: string) => Promise<boolean>;
  rateMessage: (messageId: string, rating: number, feedback?: string) => Promise<boolean>;

  // Model management
  setSelectedModel: (model: string) => void;
  refreshModels: () => Promise<void>;

  // Utility
  clearError: () => void;
  clearMessages: () => void;
}

interface SendMessageOptions {
  model?: string;
  temperature?: number;
  maxTokens?: number;
  useRAG?: boolean;
  topK?: number;
  documentIds?: string[];
}

type ChatAction =
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'SET_CONNECTED'; payload: boolean }
  | { type: 'SET_TYPING'; payload: boolean }
  | { type: 'SET_CONVERSATIONS'; payload: Conversation[] }
  | { type: 'ADD_CONVERSATION'; payload: Conversation }
  | { type: 'REMOVE_CONVERSATION'; payload: string }
  | { type: 'SET_CURRENT_CONVERSATION'; payload: Conversation | null }
  | { type: 'SET_MESSAGES'; payload: ChatMessage[] }
  | { type: 'ADD_MESSAGE'; payload: ChatMessage }
  | { type: 'UPDATE_MESSAGE'; payload: { messageId: string; updates: Partial<ChatMessage> } }
  | { type: 'SET_MODELS'; payload: string[] }
  | { type: 'SET_SELECTED_MODEL'; payload: string }
  | { type: 'CLEAR_MESSAGES' };

const initialState: ChatState = {
  conversations: [],
  currentConversation: null,
  messages: [],
  isLoading: false,
  isConnected: false,
  isTyping: false,
  error: null,
  availableModels: config.models.availableModels,
  selectedModel: config.models.defaultModel,
};

const chatReducer = (state: ChatState, action: ChatAction): ChatState => {
  switch (action.type) {
    case 'SET_LOADING':
      return { ...state, isLoading: action.payload };

    case 'SET_ERROR':
      return { ...state, error: action.payload };

    case 'SET_CONNECTED':
      return { ...state, isConnected: action.payload };

    case 'SET_TYPING':
      return { ...state, isTyping: action.payload };

    case 'SET_CONVERSATIONS':
      return { ...state, conversations: action.payload };

    case 'ADD_CONVERSATION':
      return {
        ...state,
        conversations: [action.payload, ...state.conversations],
      };

    case 'REMOVE_CONVERSATION':
      return {
        ...state,
        conversations: state.conversations.filter(conv => conv.id !== action.payload),
        currentConversation: state.currentConversation?.id === action.payload ? null : state.currentConversation,
        messages: state.currentConversation?.id === action.payload ? [] : state.messages,
      };

    case 'SET_CURRENT_CONVERSATION':
      return { ...state, currentConversation: action.payload };

    case 'SET_MESSAGES':
      return { ...state, messages: action.payload };

    case 'ADD_MESSAGE':
      return {
        ...state,
        messages: [...state.messages, action.payload],
      };

    case 'UPDATE_MESSAGE':
      return {
        ...state,
        messages: state.messages.map(msg =>
          msg.id === action.payload.messageId
            ? { ...msg, ...action.payload.updates }
            : msg
        ),
      };

    case 'SET_MODELS':
      return { ...state, availableModels: action.payload };

    case 'SET_SELECTED_MODEL':
      return { ...state, selectedModel: action.payload };

    case 'CLEAR_MESSAGES':
      return { ...state, messages: [] };

    default:
      return state;
  }
};

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export const useChat = (): ChatContextType => {
  const context = useContext(ChatContext);
  if (context === undefined) {
    throw new Error('useChat must be used within a ChatProvider');
  }
  return context;
};

interface ChatProviderProps {
  children: ReactNode;
}

export const ChatProvider: React.FC<ChatProviderProps> = ({ children }) => {
  const [state, dispatch] = useReducer(chatReducer, initialState);
  const socketRef = React.useRef<any>(null);

  // Initialize WebSocket connection
  useEffect(() => {
    const token = localStorage.getItem('authToken');
    if (!token) {
      console.log('🔌 No auth token - skipping WebSocket connection');
      return;
    }

    console.log('🔌 Connecting to WebSocket with token...');
    socketRef.current = io(config.websocket.url, {
      auth: { token },
      transports: ['polling', 'websocket'],
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
    });

    const socket = socketRef.current;

    socket.on('connect', () => {
      dispatch({ type: 'SET_CONNECTED', payload: true });
      console.log('🔌 WebSocket connected');
    });

    socket.on('disconnect', () => {
      dispatch({ type: 'SET_CONNECTED', payload: false });
      console.log('🔌 WebSocket disconnected');
    });

    // Handle streaming message chunks (real-time updates)
    let streamingMessageId: string | null = null;
    let streamingContent = '';

    socket.on('message_chunk', (data: { content: string }) => {
      streamingContent += data.content;

      // Update or create streaming message
      if (!streamingMessageId) {
        streamingMessageId = `streaming-${Date.now()}`;
        const streamingMessage: ChatMessage = {
          id: streamingMessageId,
          role: 'assistant',
          content: streamingContent,
          timestamp: new Date().toISOString(),
        };
        dispatch({ type: 'ADD_MESSAGE', payload: streamingMessage });
      } else {
        dispatch({
          type: 'UPDATE_MESSAGE',
          payload: {
            messageId: streamingMessageId,
            updates: { content: streamingContent }
          }
        });
      }
    });

    // Handle complete message - replace streaming message with final version
    socket.on('message', (message: ChatMessage) => {
      console.log('📨 Received message with metadata:', message.metadata);
      if (streamingMessageId) {
        // Update the streaming message with the real ID and metadata
        dispatch({
          type: 'UPDATE_MESSAGE',
          payload: {
            messageId: streamingMessageId,
            updates: {
              id: message.id,
              content: message.content,
              metadata: message.metadata
            }
          }
        });
        streamingMessageId = null;
        streamingContent = '';
      } else {
        // No streaming message, just add the complete message
        dispatch({ type: 'ADD_MESSAGE', payload: message });
      }
      dispatch({ type: 'SET_TYPING', payload: false });
    });

    socket.on('typing', () => {
      dispatch({ type: 'SET_TYPING', payload: true });
      // Reset streaming state
      streamingMessageId = null;
      streamingContent = '';
    });

    socket.on('typing_stop', () => {
      dispatch({ type: 'SET_TYPING', payload: false });
    });

    socket.on('error', (error: any) => {
      dispatch({ type: 'SET_ERROR', payload: error.message || 'Connection error' });
      console.error('WebSocket error:', error);
    });

    return () => {
      socket.disconnect();
    };
  }, []);

  // Load initial data only when user has a valid token
  useEffect(() => {
    const token = localStorage.getItem('authToken');
    if (!token) {
      return; // Don't load data if not authenticated
    }

    const loadInitialData = async () => {
      try {
        dispatch({ type: 'SET_LOADING', payload: true });

        // Load conversations
        const conversationsResponse = await apiService.getConversations();
        if (conversationsResponse.success) {
          dispatch({ type: 'SET_CONVERSATIONS', payload: conversationsResponse.data });

          // Auto-select first conversation if available
          if (conversationsResponse.data && conversationsResponse.data.length > 0) {
            const firstConversation = conversationsResponse.data[0];
            dispatch({ type: 'SET_CURRENT_CONVERSATION', payload: firstConversation });
            console.log('🔄 Auto-selected first conversation:', firstConversation.id);
          }
        }

        // Load available models
        const modelsResponse = await apiService.getAvailableModels();
        if (modelsResponse.success) {
          dispatch({ type: 'SET_MODELS', payload: modelsResponse.data });
        }
      } catch (error: any) {
        console.error('Failed to load initial data:', error);
        dispatch({ type: 'SET_ERROR', payload: 'Failed to load initial data' });
      } finally {
        dispatch({ type: 'SET_LOADING', payload: false });
      }
    };

    loadInitialData();
  }, []);

  const createConversation = async (title?: string): Promise<boolean> => {
    try {
      const response = await apiService.createConversation(title);
      if (response.success) {
        dispatch({ type: 'ADD_CONVERSATION', payload: response.data });
        return true;
      }
      return false;
    } catch (error: any) {
      dispatch({ type: 'SET_ERROR', payload: 'Failed to create conversation' });
      return false;
    }
  };

  const selectConversation = async (conversationId: string): Promise<boolean> => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });

      const response = await apiService.getConversation(conversationId);
      if (response.success) {
        dispatch({ type: 'SET_CURRENT_CONVERSATION', payload: response.data.conversation });
        dispatch({ type: 'SET_MESSAGES', payload: response.data.messages });

        // Join conversation room for real-time updates
        if (socketRef.current) {
          socketRef.current.emit('join_conversation', conversationId);
        }

        return true;
      }
      return false;
    } catch (error: any) {
      dispatch({ type: 'SET_ERROR', payload: 'Failed to load conversation' });
      return false;
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  };

  const deleteConversation = async (conversationId: string): Promise<boolean> => {
    try {
      const response = await apiService.deleteConversation(conversationId);
      if (response.success) {
        dispatch({ type: 'REMOVE_CONVERSATION', payload: conversationId });
        return true;
      }
      return false;
    } catch (error: any) {
      dispatch({ type: 'SET_ERROR', payload: 'Failed to delete conversation' });
      return false;
    }
  };

  const sendMessage = async (content: string, options?: SendMessageOptions): Promise<boolean> => {
    if (!state.currentConversation) {
      dispatch({ type: 'SET_ERROR', payload: 'No conversation selected' });
      return false;
    }

    try {
      // Add user message immediately
      const userMessage: ChatMessage = {
        id: `temp-${Date.now()}`,
        role: 'user',
        content,
        timestamp: new Date().toISOString(),
      };
      dispatch({ type: 'ADD_MESSAGE', payload: userMessage });

      // Send via WebSocket for real-time response
      if (socketRef.current && state.isConnected) {
        socketRef.current.emit('send_message', {
          conversationId: state.currentConversation.id,
          content,
          model: options?.model || state.selectedModel,
          ...options,
        });
        return true;
      } else {
        // Fallback to HTTP API
        const response = await apiService.sendMessage(
          state.currentConversation.id,
          content,
          {
            model: state.selectedModel,
            ...options,
          }
        );

        if (response.success) {
          dispatch({ type: 'ADD_MESSAGE', payload: response.data });
          return true;
        }
        return false;
      }
    } catch (error: any) {
      dispatch({ type: 'SET_ERROR', payload: 'Failed to send message' });
      return false;
    }
  };

  const regenerateMessage = async (messageId: string): Promise<boolean> => {
    if (!state.currentConversation) return false;

    try {
      const response = await apiService.regenerateMessage(state.currentConversation.id, messageId);
      if (response.success) {
        dispatch({ type: 'UPDATE_MESSAGE', payload: { messageId, updates: response.data } });
        return true;
      }
      return false;
    } catch (error: any) {
      dispatch({ type: 'SET_ERROR', payload: 'Failed to regenerate message' });
      return false;
    }
  };

  const rateMessage = async (messageId: string, rating: number, feedback?: string): Promise<boolean> => {
    try {
      const response = await apiService.rateMessage(messageId, rating, feedback);
      if (response.success) {
        const currentMessage = state.messages.find(m => m.id === messageId);
        dispatch({
          type: 'UPDATE_MESSAGE',
          payload: {
            messageId,
            updates: {
              metadata: {
                ...currentMessage?.metadata,
                rating,
                model: currentMessage?.metadata?.model,
                responseTime: currentMessage?.metadata?.responseTime,
                tokenCount: currentMessage?.metadata?.tokenCount,
                similarity: currentMessage?.metadata?.similarity
              }
            },
          },
        });
        return true;
      }
      return false;
    } catch (error: any) {
      dispatch({ type: 'SET_ERROR', payload: 'Failed to rate message' });
      return false;
    }
  };

  const setSelectedModel = (model: string): void => {
    dispatch({ type: 'SET_SELECTED_MODEL', payload: model });
  };

  const refreshModels = async (): Promise<void> => {
    try {
      const response = await apiService.getAvailableModels();
      if (response.success) {
        dispatch({ type: 'SET_MODELS', payload: response.data });
      }
    } catch (error: any) {
      dispatch({ type: 'SET_ERROR', payload: 'Failed to refresh models' });
    }
  };

  const clearError = (): void => {
    dispatch({ type: 'SET_ERROR', payload: null });
  };

  const clearMessages = (): void => {
    dispatch({ type: 'CLEAR_MESSAGES' });
  };

  const contextValue: ChatContextType = {
    ...state,
    createConversation,
    selectConversation,
    deleteConversation,
    sendMessage,
    regenerateMessage,
    rateMessage,
    setSelectedModel,
    refreshModels,
    clearError,
    clearMessages,
  };

  return (
    <ChatContext.Provider value={contextValue}>
      {children}
    </ChatContext.Provider>
  );
};

export default ChatContext;
