/**
 * Message List Component
 * Scrollable container for chat messages with infinite scroll
 */

import React, { useRef, useEffect, useCallback } from 'react';
import { Box, Typography, Card, CardContent, Avatar, CircularProgress } from '@mui/material';
import { SmartToy } from '@mui/icons-material';
import { ChatMessage } from '../../../services/api';
import { MessagesContainer } from '../../../theme/components';
import { EmptyChatState } from '../../shared/EmptyStates';
import { MessageItem } from './MessageItem';

export interface MessageListProps {
  messages: ChatMessage[];
  selectedModel: string;
  isTyping: boolean;
  isLoadingMore: boolean;
  hasMoreMessages: boolean;
  totalMessages: number;
  expandedSources: Set<string>;
  regeneratingMessageId: string | null;
  onCopy: (content: string) => void;
  onRegenerate: (id: string) => void;
  onToggleSources: (id: string) => void;
  onLoadMore: () => Promise<boolean>;
}

export const MessageList: React.FC<MessageListProps> = ({
  messages,
  selectedModel,
  isTyping,
  isLoadingMore,
  hasMoreMessages,
  totalMessages,
  expandedSources,
  regeneratingMessageId,
  onCopy,
  onRegenerate,
  onToggleSources,
  onLoadMore,
}) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const userScrolledUp = useRef(false);

  // Auto-scroll to bottom only if user hasn't scrolled up
  useEffect(() => {
    if (!userScrolledUp.current) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isTyping]);

  // Infinite scroll - load more messages when scrolling to top
  useEffect(() => {
    const container = messagesContainerRef.current;
    if (!container) return;

    const handleScroll = async () => {
      // Detect if user has scrolled up (not at bottom)
      const isAtBottom = container.scrollHeight - container.scrollTop <= container.clientHeight + 50;
      userScrolledUp.current = !isAtBottom;

      // Check if scrolled to top (with 100px threshold)
      if (container.scrollTop < 100 && hasMoreMessages && !isLoadingMore) {
        // Store scroll position relative to bottom
        const scrollHeightBefore = container.scrollHeight;
        const scrollTopBefore = container.scrollTop;

        const success = await onLoadMore();

        if (success) {
          // Use requestAnimationFrame for smooth scroll position update
          requestAnimationFrame(() => {
            const scrollHeightAfter = container.scrollHeight;
            const heightDifference = scrollHeightAfter - scrollHeightBefore;
            // Maintain scroll position by adding the height of new content
            container.scrollTop = scrollTopBefore + heightDifference;
          });
        }
      }
    };

    container.addEventListener('scroll', handleScroll);
    return () => container.removeEventListener('scroll', handleScroll);
  }, [hasMoreMessages, isLoadingMore, onLoadMore]);

  // Expose scroll to bottom method via ref callback
  const scrollToBottom = useCallback(() => {
    userScrolledUp.current = false;
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  return (
    <MessagesContainer ref={messagesContainerRef}>
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

      {/* Empty State */}
      {messages.length === 0 ? (
        <EmptyChatState />
      ) : (
        <>
          {/* Messages */}
          {messages.map((message) => (
            <MessageItem
              key={message.id}
              message={message}
              selectedModel={selectedModel}
              isExpanded={expandedSources.has(message.id)}
              isRegenerating={regeneratingMessageId === message.id}
              onCopy={onCopy}
              onRegenerate={onRegenerate}
              onToggleSources={onToggleSources}
            />
          ))}

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
    </MessagesContainer>
  );
};

export default MessageList;
