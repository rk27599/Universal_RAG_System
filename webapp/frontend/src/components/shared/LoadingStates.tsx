/**
 * Loading States Components
 * Unified loading indicators for consistent UX
 */

import React from 'react';
import {
  Box,
  CircularProgress,
  Typography,
  Skeleton,
  Card,
  CardContent,
} from '@mui/material';

export interface LoadingSpinnerProps {
  size?: number;
  message?: string;
  fullScreen?: boolean;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 40,
  message,
  fullScreen = false,
}) => {
  const content = (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 2,
      }}
    >
      <CircularProgress size={size} />
      {message && (
        <Typography variant="body2" color="text.secondary">
          {message}
        </Typography>
      )}
    </Box>
  );

  if (fullScreen) {
    return (
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '100vh',
        }}
      >
        {content}
      </Box>
    );
  }

  return content;
};

export interface InlineLoaderProps {
  message?: string;
}

export const InlineLoader: React.FC<InlineLoaderProps> = ({ message = 'Loading...' }) => (
  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, py: 2 }}>
    <CircularProgress size={20} />
    <Typography variant="body2" color="text.secondary">
      {message}
    </Typography>
  </Box>
);

export interface MessageSkeletonProps {
  count?: number;
}

export const MessageSkeleton: React.FC<MessageSkeletonProps> = ({ count = 3 }) => (
  <Box sx={{ p: 2 }}>
    {Array.from({ length: count }).map((_, index) => (
      <Card key={index} sx={{ mb: 2, maxWidth: '70%' }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
            <Skeleton variant="circular" width={24} height={24} />
            <Skeleton variant="text" width={100} />
          </Box>
          <Skeleton variant="rectangular" height={60} />
          <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
            <Skeleton variant="rounded" width={60} height={20} />
            <Skeleton variant="rounded" width={80} height={20} />
          </Box>
        </CardContent>
      </Card>
    ))}
  </Box>
);

export interface LoadingOverlayProps {
  message?: string;
}

export const LoadingOverlay: React.FC<LoadingOverlayProps> = ({ message }) => (
  <Box
    sx={{
      position: 'absolute',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      backgroundColor: 'rgba(0, 0, 0, 0.5)',
      zIndex: 1000,
    }}
  >
    <Card>
      <CardContent>
        <LoadingSpinner message={message} />
      </CardContent>
    </Card>
  </Box>
);

export default {
  LoadingSpinner,
  InlineLoader,
  MessageSkeleton,
  LoadingOverlay,
};
