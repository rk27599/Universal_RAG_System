/**
 * Message Item Component
 * Individual chat message display with actions
 */

import React, { useMemo } from 'react';
import {
  Box,
  CardContent,
  Avatar,
  Typography,
  Chip,
  IconButton,
  Tooltip,
  CircularProgress,
  Fade,
} from '@mui/material';
import {
  ContentCopy as CopyIcon,
  Refresh as RefreshIcon,
  SmartToy,
  Person,
} from '@mui/icons-material';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import remarkGfm from 'remark-gfm';
import { ChatMessage } from '../../../services/api';
import { MessageCard, MessageContentBox } from '../../../theme/components';
import { ThinkingProcess } from './ThinkingProcess';
import { SourceCitations } from './SourceCitations';

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

const formatTimestamp = (timestamp: string) => {
  return new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
};

const parseThinkingContent = (content: string): { thinking: string | null; answer: string } => {
  // Pattern 1: Check for <think> or </think> tags (Qwen3 format)
  const thinkTagMatch = content.match(/([\s\S]*?)<\/think>\s*/);
  if (thinkTagMatch) {
    const thinking = thinkTagMatch[1].trim();
    const answer = content.replace(/[\s\S]*?<\/think>\s*/, '').trim();

    if (thinking.length > 0 && answer.length > 0) {
      return { thinking, answer };
    }
  }

  // Pattern 2: Check for thinking process in plain text format
  const paragraphs = content.split('\n\n');

  const thinkingIndicators = [
    /^(Okay[,.]|Hmm[,.]|Let me think|First thought|I should|The user is asking|This seems|Looking at|Let me analyze)/i,
    /\b(seems like|looks like|probably|maybe|I think|wondering|trying to|I'll craft|I should)\b/i,
  ];

  if (paragraphs.length >= 2) {
    const firstPara = paragraphs[0];
    const hasThinkingIndicators = thinkingIndicators.some((pattern) => pattern.test(firstPara));

    if (hasThinkingIndicators && firstPara.length > 30) {
      const remainingContent = paragraphs.slice(1).join('\n\n').trim();

      if (remainingContent.length > 20) {
        return {
          thinking: firstPara.trim(),
          answer: remainingContent,
        };
      }
    }
  }

  // No thinking detected
  return { thinking: null, answer: content };
};

// ============================================================================
// MESSAGE ITEM COMPONENT
// ============================================================================

export interface MessageItemProps {
  message: ChatMessage;
  selectedModel: string;
  isExpanded: boolean;
  isRegenerating: boolean;
  onCopy: (content: string) => void;
  onRegenerate: (id: string) => void;
  onToggleSources: (id: string) => void;
}

export const MessageItem = React.memo<MessageItemProps>(
  ({ message, selectedModel, isExpanded, isRegenerating, onCopy, onRegenerate, onToggleSources }) => {
    const isUser = message.role === 'user';
    const isSystem = message.role === 'system';
    const hasSources = message.metadata?.sources && message.metadata.sources.length > 0;

    const { thinking, answer } = !isUser && !isSystem
      ? parseThinkingContent(message.content)
      : { thinking: null, answer: message.content };

    // Memoize markdown components
    const markdownComponents = useMemo(
      () => ({
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
                  borderRadius: '4px',
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
                fontFamily: 'monospace',
              }}
            >
              {children}
            </code>
          );
        },
      }),
      [isUser]
    );

    // System messages
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
          <MessageCard isUser={isUser}>
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

              {/* Thinking Section */}
              {thinking && <ThinkingProcess thinking={thinking} isUser={isUser} markdownComponents={markdownComponents} />}

              {/* Message Content */}
              <MessageContentBox isUser={isUser}>
                <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
                  {answer}
                </ReactMarkdown>
              </MessageContentBox>

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
                      label={`${message.metadata.sources!.length} source${
                        message.metadata.sources!.length > 1 ? 's' : ''
                      }`}
                      variant="outlined"
                      color="success"
                      sx={{ fontSize: '0.7rem', height: 20 }}
                    />
                  )}
                </Box>
              )}

              {/* Document Sources */}
              {hasSources && (
                <SourceCitations
                  sources={message.metadata!.sources!}
                  messageId={message.id}
                  isExpanded={isExpanded}
                  isUser={isUser}
                  onToggle={onToggleSources}
                />
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
                  <Tooltip title={isRegenerating ? 'Regenerating...' : 'Regenerate response'}>
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
          </MessageCard>
        </Box>
      </Fade>
    );
  }
);

MessageItem.displayName = 'MessageItem';

export default MessageItem;
