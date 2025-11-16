/**
 * Chat Interface - Real-time Messaging with RAG Integration
 * Secure chat interface with model selection and document context
 * Performance optimized with React.memo and useCallback
 */

import React, { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  IconButton,
  CircularProgress,
  Chip,
  Card,
  CardContent,
  Avatar,
  Fade,
  Tooltip,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Switch,
  FormControlLabel,
  Alert,
  Snackbar,
  Collapse,
  List,
  ListItem,
  ListItemText,
  Divider,
} from '@mui/material';
import {
  Send as SendIcon,
  Stop as StopIcon,
  Refresh as RefreshIcon,
  ContentCopy as CopyIcon,
  SmartToy,
  Person,
  Settings as SettingsIcon,
  ExpandMore as ExpandMoreIcon,
  Description as DocumentIcon,
  Psychology as ThinkingIcon,
} from '@mui/icons-material';
import { useChat } from '../../contexts/ChatContext';
import { ChatMessage, DocumentSource } from '../../services/api';
import config from '../../config/config';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import remarkGfm from 'remark-gfm';

// ============================================================================
// STATIC STYLES - Defined outside component for performance
// ============================================================================

const textFieldSx = {
  '& .MuiOutlinedInput-root': {
    borderRadius: 2,
  },
};

const messagesContainerSx = {
  flexGrow: 1,
  overflow: 'auto',
  p: 2,
  backgroundColor: 'grey.50',
  minHeight: '300px',
  position: 'relative',
};

const messageContentSx = {
  '& p': { mb: 1 },
  '& ul, & ol': { pl: 2, mb: 1 },
  '& li': { mb: 0.5 },
  '& h1, & h2, & h3, & h4, & h5, & h6': {
    fontWeight: 'bold',
    mt: 2,
    mb: 1,
    '&:first-of-type': { mt: 0 }
  },
  '& table': {
    borderCollapse: 'collapse',
    width: '100%',
    mb: 2,
    border: '1px solid',
    borderColor: 'divider'
  },
  '& th, & td': {
    border: '1px solid',
    borderColor: 'divider',
    p: 1,
    textAlign: 'left'
  },
  '& th': {
    backgroundColor: 'grey.100',
    fontWeight: 'bold'
  },
  '& code': {
    px: 0.5,
    py: 0.25,
    borderRadius: 0.5,
    fontSize: '0.9em',
    fontFamily: 'monospace'
  }
};

const sendButtonBaseSx = {
  p: 1.5,
  color: 'white',
};

const sendButtonDisabledSx = {
  ...sendButtonBaseSx,
  backgroundColor: 'grey.300',
};

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

const formatTimestamp = (timestamp: string) => {
  return new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
};

const getCardSx = (isUser: boolean) => ({
  maxWidth: '70%',
  backgroundColor: isUser ? 'primary.main' : 'background.paper',
  color: isUser ? 'primary.contrastText' : 'text.primary',
  boxShadow: 1,
});

const getSourceBoxSx = (isUser: boolean) => ({
  mt: 1,
  p: 1,
  backgroundColor: isUser ? 'rgba(255,255,255,0.1)' : 'grey.50',
  borderRadius: 1,
});

// ============================================================================
// MEMOIZED MESSAGE COMPONENT
// ============================================================================

interface MessageCardProps {
  message: ChatMessage;
  selectedModel: string;
  expandedSources: Set<string>;
  isRegenerating: boolean;
  onCopy: (content: string) => void;
  onRegenerate: (id: string) => void;
  onToggleSources: (id: string) => void;
}

const MessageCard = React.memo<MessageCardProps>(({
  message,
  selectedModel,
  expandedSources,
  isRegenerating,
  onCopy,
  onRegenerate,
  onToggleSources,
}) => {
  const isUser = message.role === 'user';
  const isSystem = message.role === 'system';
  const hasSources = message.metadata?.sources && message.metadata.sources.length > 0;
  const [showThinking, setShowThinking] = React.useState(false);

  // Parse thinking from content (for Qwen3-4B-Thinking and similar models)
  const parseThinkingContent = (content: string): { thinking: string | null; answer: string } => {
    // Pattern 1: Check for <think> or </think> tags (Qwen3 format)
    // Note: Model outputs </think> (closing tag) at the end of thinking
    const thinkTagMatch = content.match(/([\s\S]*?)<\/think>\s*/);
    if (thinkTagMatch) {
      const thinking = thinkTagMatch[1].trim();
      const answer = content.replace(/[\s\S]*?<\/think>\s*/, '').trim();

      if (thinking.length > 0 && answer.length > 0) {
        return { thinking, answer };
      }
    }

    // Pattern 2: Check for thinking process in plain text format
    // Thinking typically appears as internal monologue before the actual answer
    // Examples: "Okay,", "Hmm,", "Let me think", "First thought:", etc.
    const paragraphs = content.split('\n\n');

    // Check if first paragraph looks like thinking (contains thinking indicators)
    const thinkingIndicators = [
      /^(Okay[,.]|Hmm[,.]|Let me think|First thought|I should|The user is asking|This seems|Looking at|Let me analyze)/i,
      /\b(seems like|looks like|probably|maybe|I think|wondering|trying to|I'll craft|I should)\b/i,
    ];

    if (paragraphs.length >= 2) {
      const firstPara = paragraphs[0];
      const hasThinkingIndicators = thinkingIndicators.some(pattern => pattern.test(firstPara));

      // If first paragraph has thinking indicators and is substantial (>30 chars)
      if (hasThinkingIndicators && firstPara.length > 30) {
        // Check if there's clear answer content after
        const remainingContent = paragraphs.slice(1).join('\n\n').trim();

        if (remainingContent.length > 20) {
          return {
            thinking: firstPara.trim(),
            answer: remainingContent
          };
        }
      }
    }

    // No thinking detected
    return { thinking: null, answer: content };
  };

  const { thinking, answer } = !isUser && !isSystem
    ? parseThinkingContent(message.content)
    : { thinking: null, answer: message.content };

  // Memoize markdown components
  const markdownComponents = useMemo(() => ({
    code: ({ node, className, children, ...props }: any) => {
      const match = /language-(\w+)/.exec(className || '');
      const isInline = !className;
      const content = String(children).replace(/\n$/, '');

      if (!isInline && match) {
        return (
          <SyntaxHighlighter
            style={oneDark}
            language={match[1]}
            PreTag="div"
            customStyle={{
              margin: '1em 0',
              borderRadius: '4px'
            }}
          >
            {content}
          </SyntaxHighlighter>
        );
      }

      return (
        <code
          className={className}
          style={{
            backgroundColor: isUser ? 'rgba(255,255,255,0.1)' : '#f5f5f5',
            padding: '2px 4px',
            borderRadius: '3px',
            fontSize: '0.9em',
            fontFamily: 'monospace'
          }}
        >
          {children}
        </code>
      );
    }
  }), [isUser]);

  // Memoize message content box styles
  const contentBoxSx = useMemo(() => ({
    ...messageContentSx,
    '& code': {
      ...messageContentSx['& code'],
      backgroundColor: isUser ? 'rgba(255,255,255,0.1)' : 'grey.100',
    }
  }), [isUser]);

  if (isSystem) {
    return (
      <Box sx={{ mb: 2, textAlign: 'center' }}>
        <Chip label={message.content} size="small" variant="outlined" />
      </Box>
    );
  }

  return (
    <Fade in timeout={200}>
      <Box
        sx={{
          display: 'flex',
          justifyContent: isUser ? 'flex-end' : 'flex-start',
          mb: 2,
        }}
      >
        <Card sx={getCardSx(isUser)}>
          <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
            {/* Message Header */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
              <Avatar sx={{ width: 24, height: 24 }}>
                {isUser ? <Person fontSize="small" /> : <SmartToy fontSize="small" />}
              </Avatar>
              <Typography variant="caption" sx={{ opacity: 0.8 }}>
                {isUser ? 'You' : selectedModel}
              </Typography>
              <Typography variant="caption" sx={{ opacity: 0.6, ml: 'auto' }}>
                {formatTimestamp(message.timestamp)}
              </Typography>
            </Box>

            {/* Thinking Section (Qwen3-4B-Thinking model) */}
            {thinking && (
              <Box sx={{ mb: 1 }}>
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 0.5,
                    cursor: 'pointer',
                    '&:hover': { opacity: 0.7 },
                  }}
                  onClick={() => setShowThinking(!showThinking)}
                >
                  <ThinkingIcon sx={{ fontSize: '0.9rem', color: 'text.secondary' }} />
                  <Typography variant="caption" sx={{ color: 'text.secondary', fontStyle: 'italic' }}>
                    Show thinking process
                  </Typography>
                  <ExpandMoreIcon
                    sx={{
                      fontSize: '1rem',
                      color: 'text.secondary',
                      transform: showThinking ? 'rotate(180deg)' : 'rotate(0deg)',
                      transition: 'transform 0.2s',
                    }}
                  />
                </Box>

                <Collapse in={showThinking}>
                  <Box
                    sx={{
                      mt: 1,
                      p: 1.5,
                      backgroundColor: isUser ? 'rgba(255,255,255,0.05)' : 'grey.50',
                      borderRadius: 1,
                      borderLeft: '3px solid',
                      borderColor: 'primary.light',
                      opacity: 0.7,
                    }}
                  >
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      components={markdownComponents}
                    >
                      {thinking}
                    </ReactMarkdown>
                  </Box>
                </Collapse>
              </Box>
            )}

            {/* Message Content */}
            <Box sx={contentBoxSx}>
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={markdownComponents}
              >
                {answer}
              </ReactMarkdown>
            </Box>

            {/* Message Metadata */}
            {message.metadata && (
              <Box sx={{ mt: 1, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                {message.metadata.responseTime && (
                  <Chip
                    size="small"
                    label={`${message.metadata.responseTime.toFixed(2)}s`}
                    variant="outlined"
                    sx={{ fontSize: '0.7rem', height: 20 }}
                  />
                )}
                {message.metadata.tokenCount && (
                  <Chip
                    size="small"
                    label={`${message.metadata.tokenCount} tokens`}
                    variant="outlined"
                    sx={{ fontSize: '0.7rem', height: 20 }}
                  />
                )}
                {message.metadata.similarity && (
                  <Chip
                    size="small"
                    label={`${(message.metadata.similarity * 100).toFixed(1)}% match`}
                    variant="outlined"
                    color="info"
                    sx={{ fontSize: '0.7rem', height: 20 }}
                  />
                )}
                {hasSources && (
                  <Chip
                    size="small"
                    label={`${message.metadata!.sources!.length} source${message.metadata!.sources!.length > 1 ? 's' : ''}`}
                    variant="outlined"
                    color="success"
                    sx={{ fontSize: '0.7rem', height: 20 }}
                  />
                )}
              </Box>
            )}

            {/* Document Sources */}
            {hasSources && (
              <Box sx={{ mt: 1 }}>
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 0.5,
                    cursor: 'pointer',
                    '&:hover': { opacity: 0.7 },
                  }}
                  onClick={() => onToggleSources(message.id)}
                >
                  <DocumentIcon sx={{ fontSize: '0.9rem', color: 'text.secondary' }} />
                  <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                    {message.metadata!.sources!.length} source{message.metadata!.sources!.length > 1 ? 's' : ''}
                  </Typography>
                  <ExpandMoreIcon
                    sx={{
                      fontSize: '1rem',
                      color: 'text.secondary',
                      transform: expandedSources.has(message.id) ? 'rotate(180deg)' : 'rotate(0deg)',
                      transition: 'transform 0.2s',
                    }}
                  />
                </Box>

                <Collapse in={expandedSources.has(message.id)}>
                  <Box sx={getSourceBoxSx(isUser)}>
                    <List dense disablePadding>
                      {message.metadata!.sources!.map((source, idx) => (
                        <React.Fragment key={source.chunkId}>
                          {idx > 0 && <Divider sx={{ my: 0.5 }} />}
                          <ListItem disablePadding sx={{ py: 0.5 }}>
                            <ListItemText
                              primary={
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                  <Typography variant="caption" sx={{ fontWeight: 'bold' }}>
                                    {source.documentTitle}
                                  </Typography>
                                  <Chip
                                    size="small"
                                    label={`${(source.similarity * 100).toFixed(0)}%`}
                                    color="success"
                                    sx={{ height: 16, fontSize: '0.65rem' }}
                                  />
                                </Box>
                              }
                              secondary={
                                <Typography variant="caption" sx={{ fontSize: '0.7rem' }}>
                                  {source.section}
                                </Typography>
                              }
                            />
                          </ListItem>
                        </React.Fragment>
                      ))}
                    </List>
                  </Box>
                </Collapse>
              </Box>
            )}

            {/* Message Actions */}
            <Box sx={{ mt: 1, display: 'flex', gap: 0.5, justifyContent: 'flex-end' }}>
              <Tooltip title="Copy message">
                <IconButton
                  size="small"
                  onClick={() => onCopy(answer)}
                  sx={{ color: isUser ? 'primary.contrastText' : 'text.secondary' }}
                >
                  <CopyIcon fontSize="small" />
                </IconButton>
              </Tooltip>

              {!isUser && (
                <Tooltip title={isRegenerating ? "Regenerating..." : "Regenerate response"}>
                  <IconButton
                    size="small"
                    onClick={() => onRegenerate(message.id)}
                    disabled={isRegenerating}
                    sx={{ color: 'text.secondary' }}
                  >
                    {isRegenerating ? (
                      <CircularProgress size={16} color="inherit" />
                    ) : (
                      <RefreshIcon fontSize="small" />
                    )}
                  </IconButton>
                </Tooltip>
              )}
            </Box>
          </CardContent>
        </Card>
      </Box>
    </Fade>
  );
});

MessageCard.displayName = 'MessageCard';

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

  const [messageInput, setMessageInput] = useState('');
  const [useRAG, setUseRAG] = useState(true);
  const [showSettings, setShowSettings] = useState(true);
  const [temperature, setTemperature] = useState(0.0);
  const [topK, setTopK] = useState(25);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [expandedSources, setExpandedSources] = useState<Set<string>>(new Set());
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [regeneratingMessageId, setRegeneratingMessageId] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const userScrolledUp = useRef(false);

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

  // Auto-scroll to bottom only if user hasn't scrolled up
  useEffect(() => {
    if (!userScrolledUp.current) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isTyping]);

  // Focus input on load
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  // Infinite scroll - load more messages when scrolling to top
  useEffect(() => {
    const container = messagesContainerRef.current;
    if (!container) return;

    const handleScroll = async () => {
      // Detect if user has scrolled up (not at bottom)
      const isAtBottom = container.scrollHeight - container.scrollTop <= container.clientHeight + 50;
      userScrolledUp.current = !isAtBottom;

      // Check if scrolled to top (with 100px threshold)
      if (container.scrollTop < 100 && hasMoreMessages && !isLoadingMore && !isLoading) {
        setIsLoadingMore(true);

        // Store scroll position relative to bottom
        const scrollHeightBefore = container.scrollHeight;
        const scrollTopBefore = container.scrollTop;

        const success = await loadMoreMessages();

        if (success) {
          // Use requestAnimationFrame for smooth scroll position update
          requestAnimationFrame(() => {
            const scrollHeightAfter = container.scrollHeight;
            const heightDifference = scrollHeightAfter - scrollHeightBefore;
            // Maintain scroll position by adding the height of new content
            container.scrollTop = scrollTopBefore + heightDifference;
          });
        }

        setIsLoadingMore(false);
      }
    };

    container.addEventListener('scroll', handleScroll);
    return () => container.removeEventListener('scroll', handleScroll);
  }, [hasMoreMessages, isLoadingMore, isLoading, loadMoreMessages]);

  // ============================================================================
  // MEMOIZED EVENT HANDLERS
  // ============================================================================

  const handleSendMessage = useCallback(async () => {
    if (!messageInput.trim() || isLoading) return;

    const message = messageInput.trim();
    setMessageInput('');

    // Reset scroll lock when user sends a message
    userScrolledUp.current = false;

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
    console.log('   localStorage values:', { useReranker, useQueryExpansion, useHybridSearch, promptTemplate });

    const success = await sendMessage(message, {
      ...configRef.current,
      useExpertPrompt: useExpertPrompt !== null ? JSON.parse(useExpertPrompt) : true,
      customSystemPrompt: customSystemPrompt || undefined,
      // Enhanced RAG options
      ...enhancedRAGOptions,
    });

    if (!success) {
      setSnackbarMessage('Failed to send message');
    }
  }, [messageInput, isLoading, sendMessage]);

  const handleKeyPress = useCallback((event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSendMessage();
    }
  }, [handleSendMessage]);

  const handleCopyMessage = useCallback((content: string) => {
    // Check if Clipboard API is available (HTTPS or localhost)
    if (navigator.clipboard && navigator.clipboard.writeText) {
      // Modern Clipboard API (preferred)
      navigator.clipboard.writeText(content)
        .then(() => {
          setSnackbarMessage('Message copied to clipboard');
        })
        .catch((err) => {
          console.error('Failed to copy using Clipboard API:', err);
          setSnackbarMessage('Failed to copy message');
        });
    } else {
      // Fallback for HTTP contexts (legacy method)
      try {
        const textArea = document.createElement('textarea');
        textArea.value = content;
        textArea.style.position = 'fixed';
        textArea.style.left = '-9999px';
        textArea.style.top = '-9999px';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();

        const successful = document.execCommand('copy');
        document.body.removeChild(textArea);

        if (successful) {
          setSnackbarMessage('Message copied to clipboard');
        } else {
          setSnackbarMessage('Failed to copy message');
        }
      } catch (err) {
        console.error('Failed to copy using fallback method:', err);
        setSnackbarMessage('Copy not supported in this context');
      }
    }
  }, []);

  const toggleSources = useCallback((messageId: string) => {
    setExpandedSources(prev => {
      const newSet = new Set(prev);
      if (newSet.has(messageId)) {
        newSet.delete(messageId);
      } else {
        newSet.add(messageId);
      }
      return newSet;
    });
  }, []);

  const handleRegenerateMessage = useCallback(async (messageId: string) => {
    try {
      setRegeneratingMessageId(messageId);
      const success = await regenerateMessage(messageId);
      setRegeneratingMessageId(null);

      if (success) {
        setSnackbarMessage('Message regenerated successfully');
        // Force scroll to bottom to show updated message
        setTimeout(() => {
          messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
        }, 100);
      } else {
        setSnackbarMessage('Failed to regenerate message - no response from server');
      }
    } catch (error: any) {
      setRegeneratingMessageId(null);
      console.error('Regenerate error:', error);
      setSnackbarMessage(`Failed to regenerate: ${error.message || 'Unknown error'}`);
    }
  }, [regenerateMessage]);

  const handleCloseSnackbar = useCallback(() => {
    setSnackbarMessage('');
  }, []);

  const handleStopOrSend = useCallback(() => {
    if (isTyping) {
      stopGeneration();
    } else {
      handleSendMessage();
    }
  }, [isTyping, stopGeneration, handleSendMessage]);

  // Memoize send button sx
  const sendButtonSx = useMemo(() => ({
    ...sendButtonBaseSx,
    backgroundColor: isTyping ? 'error.main' : 'primary.main',
    '&:hover': {
      backgroundColor: isTyping ? 'error.dark' : 'primary.dark',
    },
    '&:disabled': {
      backgroundColor: 'grey.300',
    },
  }), [isTyping]);

  // ============================================================================
  // RENDER HELPERS
  // ============================================================================

  const renderMessage = useCallback((message: ChatMessage, index: number) => {
    return (
      <MessageCard
        key={message.id}
        message={message}
        selectedModel={selectedModel}
        expandedSources={expandedSources}
        isRegenerating={regeneratingMessageId === message.id}
        onCopy={handleCopyMessage}
        onRegenerate={handleRegenerateMessage}
        onToggleSources={toggleSources}
      />
    );
  }, [selectedModel, expandedSources, regeneratingMessageId, handleCopyMessage, handleRegenerateMessage, toggleSources]);

  // ============================================================================
  // RENDER
  // ============================================================================

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Chat Header */}
      <Paper sx={{ p: 2, borderRadius: 0, borderBottom: 1, borderColor: 'divider' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Typography variant="h6">Chat</Typography>

            {/* Connection Status */}
            <Chip
              size="small"
              label={isConnected ? 'Connected' : 'Offline'}
              color={isConnected ? 'success' : 'error'}
              variant="outlined"
            />

            {/* Model Selector */}
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel>Model</InputLabel>
              <Select
                value={selectedModel}
                label="Model"
                onChange={(e) => setSelectedModel(e.target.value)}
              >
                {availableModels.map((model) => (
                  <MenuItem key={model} value={model}>
                    {model}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>

          {/* Settings Toggle */}
          <IconButton onClick={() => setShowSettings(!showSettings)}>
            <SettingsIcon />
          </IconButton>
        </Box>

        {/* Advanced Settings */}
        {showSettings && (
          <Box sx={{ mt: 2, display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
            <FormControlLabel
              control={
                <Switch
                  checked={useRAG}
                  onChange={(e) => setUseRAG(e.target.checked)}
                />
              }
              label="Use RAG"
            />

            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Typography variant="caption">Temperature:</Typography>
              <TextField
                type="number"
                size="small"
                value={temperature}
                onChange={(e) => setTemperature(Number(e.target.value))}
                inputProps={{ min: 0, max: 2, step: 0.1 }}
                sx={{ width: 80 }}
              />
            </Box>

            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Typography variant="caption">Sources:</Typography>
              <TextField
                type="number"
                size="small"
                value={topK}
                onChange={(e) => setTopK(Number(e.target.value))}
                inputProps={{ min: 1, step: 1 }}
                sx={{ width: 80 }}
              />
            </Box>
          </Box>
        )}
      </Paper>

      {/* Messages Area */}
      <Box ref={messagesContainerRef} sx={messagesContainerSx}>
        {/* Loading More Indicator */}
        {isLoadingMore && (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 2 }}>
            <CircularProgress size={24} />
            <Typography variant="caption" sx={{ ml: 1, color: 'text.secondary' }}>
              Loading older messages...
            </Typography>
          </Box>
        )}

        {/* Has More Messages Indicator */}
        {hasMoreMessages && !isLoadingMore && messages.length > 0 && totalMessages > messages.length && (
          <Box sx={{ textAlign: 'center', py: 1 }}>
            <Typography variant="caption" sx={{ color: 'text.secondary' }}>
              Scroll up to load more ({messages.length}/{totalMessages} messages)
            </Typography>
          </Box>
        )}

        {messages.length === 0 ? (
          <Box
            sx={{
              height: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              textAlign: 'center',
            }}
          >
            <Box>
              <SmartToy sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" color="text.secondary" gutterBottom>
                Start a conversation
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Ask me anything! I can help with questions using your uploaded documents.
              </Typography>
            </Box>
          </Box>
        ) : (
          <>
            {messages.map((message, index) => renderMessage(message, index))}

            {/* Typing Indicator */}
            {isTyping && (
              <Box sx={{ display: 'flex', justifyContent: 'flex-start', mb: 2 }}>
                <Card sx={{ backgroundColor: 'background.paper' }}>
                  <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 1, p: 2 }}>
                    <Avatar sx={{ width: 24, height: 24 }}>
                      <SmartToy fontSize="small" />
                    </Avatar>
                    <Typography variant="body2" color="text.secondary">
                      {selectedModel} is typing...
                    </Typography>
                    <CircularProgress size={16} />
                  </CardContent>
                </Card>
              </Box>
            )}
          </>
        )}

        <div ref={messagesEndRef} />
      </Box>

      {/* Input Area */}
      <Paper sx={{ p: 2, borderRadius: 0, borderTop: 1, borderColor: 'divider' }}>
        <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-end' }}>
          <TextField
            ref={inputRef}
            multiline
            maxRows={4}
            fullWidth
            variant="outlined"
            placeholder="Type your message..."
            value={messageInput}
            onChange={(e) => setMessageInput(e.target.value)}
            onKeyPress={handleKeyPress}
            disabled={isLoading}
            sx={textFieldSx}
          />

          <IconButton
            color={isTyping ? 'error' : 'primary'}
            onClick={handleStopOrSend}
            disabled={!isTyping && (!messageInput.trim() || isLoading)}
            sx={sendButtonSx}
          >
            {isLoading ? (
              <CircularProgress size={20} color="inherit" />
            ) : isTyping ? (
              <StopIcon />
            ) : (
              <SendIcon />
            )}
          </IconButton>
        </Box>
      </Paper>

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
            }
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