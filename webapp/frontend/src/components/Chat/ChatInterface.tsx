/**
 * Chat Interface - Refactored & Modular
 * Real-time messaging with RAG integration
 * Now using component composition for better maintainability
 */

import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Box, Snackbar, Alert } from '@mui/material';
import { useChat } from '../../contexts/ChatContext';
import config from '../../config/config';
import { ChatHeader } from './ChatInterface/ChatHeader';
import { MessageList } from './ChatInterface/MessageList';
import { MessageInput } from './ChatInterface/MessageInput';
import { useMessageActions } from '../../hooks/useMessageActions';

// ============================================================================
// MAIN COMPONENT
// ============================================================================

interface ChatInterfaceProps {
  conversationId?: string;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ conversationId }) => {
  const {
    messages,
    isLoading,
    isTyping,
    isConnected,
    error,
    selectedModel,
    availableModels,
    hasMoreMessages,
    totalMessages,
    sendMessage,
    regenerateMessage,
    loadMoreMessages,
    stopGeneration,
    setSelectedModel,
    clearError,
  } = useChat();

  // Local state
  const [messageInput, setMessageInput] = useState('');
  const [useRAG, setUseRAG] = useState(true);
  const [showSettings, setShowSettings] = useState(true);
  const [temperature, setTemperature] = useState(0.0);
  const [topK, setTopK] = useState(25);
  const [isLoadingMore, setIsLoadingMore] = useState(false);

  // Message actions hook
  const {
    handleCopy,
    handleRegenerate,
    handleToggleSources,
    expandedSources,
    regeneratingMessageId,
    snackbarMessage,
    clearSnackbar,
  } = useMessageActions({
    regenerateMessageFn: regenerateMessage,
    onRegenerateSuccess: () => {
      // Optionally scroll to bottom or perform other actions
    },
  });

  // Use ref to store config values to reduce useCallback dependencies
  const configRef = useRef({
    selectedModel,
    temperature,
    useRAG,
    topK,
    maxTokens: config.models.maxTokens,
  });

  // Update config ref when values change
  useEffect(() => {
    configRef.current = {
      selectedModel,
      temperature,
      useRAG,
      topK,
      maxTokens: config.models.maxTokens,
    };
  }, [selectedModel, temperature, useRAG, topK]);

  // ============================================================================
  // EVENT HANDLERS
  // ============================================================================

  const handleSendMessage = useCallback(async () => {
    if (!messageInput.trim() || isLoading) return;

    const message = messageInput.trim();
    setMessageInput('');

    // Get expert prompt settings from localStorage
    const useExpertPrompt = localStorage.getItem('useExpertPrompt');
    const customSystemPrompt = localStorage.getItem('customSystemPrompt');

    // Get enhanced RAG settings from localStorage
    const useReranker = localStorage.getItem('useReranker');
    const useQueryExpansion = localStorage.getItem('useQueryExpansion');
    const useHybridSearch = localStorage.getItem('useHybridSearch');
    const promptTemplate = localStorage.getItem('promptTemplate');

    // Parse settings
    const enhancedRAGOptions = {
      useReranker: useReranker !== null ? JSON.parse(useReranker) : true,
      useQueryExpansion: useQueryExpansion !== null ? JSON.parse(useQueryExpansion) : false,
      useHybridSearch: useHybridSearch !== null ? JSON.parse(useHybridSearch) : false,
      promptTemplate: promptTemplate || null,
    };

    // Debug logging
    console.log('🔍 Enhanced RAG Settings:', enhancedRAGOptions);

    const success = await sendMessage(message, {
      ...configRef.current,
      useExpertPrompt: useExpertPrompt !== null ? JSON.parse(useExpertPrompt) : true,
      customSystemPrompt: customSystemPrompt || undefined,
      // Enhanced RAG options
      ...enhancedRAGOptions,
    });

    if (!success) {
      // Error already handled by context
    }
  }, [messageInput, isLoading, sendMessage]);

  const handleLoadMore = useCallback(async (): Promise<boolean> => {
    if (isLoadingMore || !hasMoreMessages) return false;

    setIsLoadingMore(true);
    const success = await loadMoreMessages();
    setIsLoadingMore(false);

    return success;
  }, [isLoadingMore, hasMoreMessages, loadMoreMessages]);

  const handleCloseSnackbar = useCallback(() => {
    clearSnackbar();
  }, [clearSnackbar]);

  // ============================================================================
  // RENDER
  // ============================================================================

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Chat Header */}
      <ChatHeader
        isConnected={isConnected}
        selectedModel={selectedModel}
        availableModels={availableModels}
        showSettings={showSettings}
        useRAG={useRAG}
        temperature={temperature}
        topK={topK}
        onModelChange={setSelectedModel}
        onSettingsToggle={() => setShowSettings(!showSettings)}
        onUseRAGChange={setUseRAG}
        onTemperatureChange={setTemperature}
        onTopKChange={setTopK}
      />

      {/* Messages Area */}
      <MessageList
        messages={messages}
        selectedModel={selectedModel}
        isTyping={isTyping}
        isLoadingMore={isLoadingMore}
        hasMoreMessages={hasMoreMessages}
        totalMessages={totalMessages}
        expandedSources={expandedSources}
        regeneratingMessageId={regeneratingMessageId}
        onCopy={handleCopy}
        onRegenerate={handleRegenerate}
        onToggleSources={handleToggleSources}
        onLoadMore={handleLoadMore}
      />

      {/* Input Area */}
      <MessageInput
        value={messageInput}
        isLoading={isLoading}
        isTyping={isTyping}
        onChange={setMessageInput}
        onSend={handleSendMessage}
        onStop={stopGeneration}
      />

      {/* Error Snackbar - Persistent (user must close manually) */}
      <Snackbar
        open={!!error}
        autoHideDuration={null}
        onClose={(event, reason) => {
          // Only allow manual close (clicking X), not clickaway or timeout
          if (reason === 'clickaway') {
            return;
          }
          clearError();
        }}
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
      >
        <Alert
          onClose={clearError}
          severity="error"
          sx={{
            width: '100%',
            maxWidth: '600px',
            '& .MuiAlert-message': {
              whiteSpace: 'pre-line', // Preserve line breaks in error messages
            },
          }}
        >
          {error}
        </Alert>
      </Snackbar>

      {/* Success Snackbar */}
      <Snackbar
        open={!!snackbarMessage}
        autoHideDuration={3000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={handleCloseSnackbar} severity="success" sx={{ width: '100%' }}>
          {snackbarMessage}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default ChatInterface;
