/**
 * Chat Interface - Real-time Messaging with RAG Integration
 * Secure chat interface with model selection and document context
 */

import React, { useState, useRef, useEffect } from 'react';
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
  ThumbUp,
  ThumbDown,
  ContentCopy as CopyIcon,
  SmartToy,
  Person,
  Settings as SettingsIcon,
  ExpandMore as ExpandMoreIcon,
  Description as DocumentIcon,
} from '@mui/icons-material';
import { useChat } from '../../contexts/ChatContext';
import { ChatMessage, DocumentSource } from '../../services/api';
import config from '../../config/config';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import remarkGfm from 'remark-gfm'; 

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
    rateMessage,
    loadMoreMessages,
    stopGeneration,
    setSelectedModel,
    clearError,
  } = useChat();

  const [messageInput, setMessageInput] = useState('');
  const [useRAG, setUseRAG] = useState(true);
  const [showSettings, setShowSettings] = useState(true);
  const [temperature, setTemperature] = useState(0.7);
  const [topK, setTopK] = useState(15);
  const [snackbarMessage, setSnackbarMessage] = useState('');

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const [isLoadingMore, setIsLoadingMore] = useState(false);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
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

  const handleSendMessage = async () => {
    if (!messageInput.trim() || isLoading) return;

    const message = messageInput.trim();
    setMessageInput('');

    const success = await sendMessage(message, {
      model: selectedModel,
      temperature,
      useRAG,
      topK,
      maxTokens: config.models.maxTokens,
    });

    if (!success) {
      setSnackbarMessage('Failed to send message');
    }
  };

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSendMessage();
    }
  };

  const handleCopyMessage = (content: string) => {
    navigator.clipboard.writeText(content);
    setSnackbarMessage('Message copied to clipboard');
  };

  const handleRateMessage = async (messageId: string, rating: number) => {
    const success = await rateMessage(messageId, rating);
    if (success) {
      setSnackbarMessage('Thank you for your feedback!');
    }
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const [expandedSources, setExpandedSources] = useState<Set<string>>(new Set());

  const toggleSources = (messageId: string) => {
    setExpandedSources(prev => {
      const newSet = new Set(prev);
      if (newSet.has(messageId)) {
        newSet.delete(messageId);
      } else {
        newSet.add(messageId);
      }
      return newSet;
    });
  };

  const renderMessage = (message: ChatMessage, index: number) => {
    const isUser = message.role === 'user';
    const isSystem = message.role === 'system';
    const hasSources = message.metadata?.sources && message.metadata.sources.length > 0;

    if (isSystem) {
      return (
        <Box key={message.id} sx={{ mb: 2, textAlign: 'center' }}>
          <Chip label={message.content} size="small" variant="outlined" />
        </Box>
      );
    }

    return (
      <Fade key={message.id} in timeout={200}>
        <Box
          sx={{
            display: 'flex',
            justifyContent: isUser ? 'flex-end' : 'flex-start',
            mb: 2,
          }}
        >
          <Card
            sx={{
              maxWidth: '70%',
              backgroundColor: isUser ? 'primary.main' : 'background.paper',
              color: isUser ? 'primary.contrastText' : 'text.primary',
              boxShadow: 1,
            }}
          >
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
              {/* Message Content */}
              <Box
                sx={{
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
                    backgroundColor: isUser ? 'rgba(255,255,255,0.1)' : 'grey.100',
                    px: 0.5,
                    py: 0.25,
                    borderRadius: 0.5,
                    fontSize: '0.9em',
                    fontFamily: 'monospace'
                  }
                }}
              >
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}  // This enables table support!
                  components={{
                    code: ({ node, className, children, ...props }: any) => {
                      const match = /language-(\w+)/.exec(className || '');
                      const isInline = !className;
                      
                      return !isInline && match ? (
                        <SyntaxHighlighter
                          style={oneDark}
                          language={match[1]}
                          PreTag="div"
                          customStyle={{
                            margin: '1em 0',
                            borderRadius: '4px'
                          }}
                        >
                          {String(children).replace(/\n$/, '')}
                        </SyntaxHighlighter>
                      ) : (
                        <code className={className} style={{ 
                          backgroundColor: isUser ? 'rgba(255,255,255,0.1)' : '#f5f5f5',
                          padding: '2px 4px',
                          borderRadius: '3px',
                          fontSize: '0.9em',
                          fontFamily: 'monospace'
                        }}>
                          {children}
                        </code>
                      );
                    }
                  }}
                >
                  {message.content}
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
                    onClick={() => toggleSources(message.id)}
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
                    <Box
                      sx={{
                        mt: 1,
                        p: 1,
                        backgroundColor: isUser ? 'rgba(255,255,255,0.1)' : 'grey.50',
                        borderRadius: 1,
                      }}
                    >
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
                    onClick={() => handleCopyMessage(message.content)}
                    sx={{ color: isUser ? 'primary.contrastText' : 'text.secondary' }}
                  >
                    <CopyIcon fontSize="small" />
                  </IconButton>
                </Tooltip>

                {!isUser && (
                  <>
                    <Tooltip title="Regenerate response">
                      <IconButton
                        size="small"
                        onClick={() => regenerateMessage(message.id)}
                        sx={{ color: 'text.secondary' }}
                      >
                        <RefreshIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>

                    <Tooltip title="Good response">
                      <IconButton
                        size="small"
                        onClick={() => handleRateMessage(message.id, 5)}
                        sx={{ color: 'success.main' }}
                      >
                        <ThumbUp fontSize="small" />
                      </IconButton>
                    </Tooltip>

                    <Tooltip title="Poor response">
                      <IconButton
                        size="small"
                        onClick={() => handleRateMessage(message.id, 1)}
                        sx={{ color: 'error.main' }}
                      >
                        <ThumbDown fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </>
                )}
              </Box>
            </CardContent>
          </Card>
        </Box>
      </Fade>
    );
  };

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
      <Box
        ref={messagesContainerRef}
        sx={{
          flexGrow: 1,
          overflow: 'auto',
          p: 2,
          backgroundColor: 'grey.50',
          minHeight: '300px',
          position: 'relative',
        }}
      >
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
            sx={{
              '& .MuiOutlinedInput-root': {
                borderRadius: 2,
              },
            }}
          />

          <IconButton
            color={isTyping ? 'error' : 'primary'}
            onClick={isTyping ? stopGeneration : handleSendMessage}
            disabled={!isTyping && (!messageInput.trim() || isLoading)}
            sx={{
              p: 1.5,
              backgroundColor: isTyping ? 'error.main' : 'primary.main',
              color: 'white',
              '&:hover': {
                backgroundColor: isTyping ? 'error.dark' : 'primary.dark',
              },
              '&:disabled': {
                backgroundColor: 'grey.300',
              },
            }}
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

      {/* Error Snackbar */}
      <Snackbar
        open={!!error}
        autoHideDuration={6000}
        onClose={clearError}
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
      >
        <Alert onClose={clearError} severity="error" sx={{ width: '100%' }}>
          {error}
        </Alert>
      </Snackbar>

      {/* Success Snackbar */}
      <Snackbar
        open={!!snackbarMessage}
        autoHideDuration={3000}
        onClose={() => setSnackbarMessage('')}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={() => setSnackbarMessage('')} severity="success" sx={{ width: '100%' }}>
          {snackbarMessage}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default ChatInterface;