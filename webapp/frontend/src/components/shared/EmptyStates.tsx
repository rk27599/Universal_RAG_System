/**
 * Empty State Components
 * Consistent empty state designs across the app
 */

import React from 'react';
import { Box, Typography, Button, SvgIconProps } from '@mui/material';
import {
  SmartToy,
  FolderOpen,
  SearchOff,
  ChatBubbleOutline,
} from '@mui/icons-material';
import { EmptyStateContainer, EmptyStateContent } from '../../theme/components';

export interface EmptyStateProps {
  icon?: React.ComponentType<SvgIconProps>;
  title: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon: Icon,
  title,
  description,
  actionLabel,
  onAction,
}) => (
  <EmptyStateContainer>
    <EmptyStateContent>
      {Icon && <Icon />}
      <Typography variant="h6" color="text.secondary" gutterBottom>
        {title}
      </Typography>
      {description && (
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {description}
        </Typography>
      )}
      {actionLabel && onAction && (
        <Button variant="contained" onClick={onAction}>
          {actionLabel}
        </Button>
      )}
    </EmptyStateContent>
  </EmptyStateContainer>
);

// Predefined empty states for common scenarios

export const EmptyChatState: React.FC<{ onStart?: () => void }> = ({ onStart }) => (
  <EmptyState
    icon={SmartToy}
    title="Start a conversation"
    description="Ask me anything! I can help with questions using your uploaded documents."
    actionLabel={onStart ? "Start Chat" : undefined}
    onAction={onStart}
  />
);

export const EmptyDocumentsState: React.FC<{ onUpload?: () => void }> = ({ onUpload }) => (
  <EmptyState
    icon={FolderOpen}
    title="No documents yet"
    description="Upload documents to get started with RAG-powered conversations."
    actionLabel={onUpload ? "Upload Document" : undefined}
    onAction={onUpload}
  />
);

export const NoResultsState: React.FC = () => (
  <EmptyState
    icon={SearchOff}
    title="No results found"
    description="Try adjusting your search or filters."
  />
);

export const NoMessagesState: React.FC = () => (
  <EmptyState
    icon={ChatBubbleOutline}
    title="No messages"
    description="Start a new conversation to see messages here."
  />
);

export default {
  EmptyState,
  EmptyChatState,
  EmptyDocumentsState,
  NoResultsState,
  NoMessagesState,
};
