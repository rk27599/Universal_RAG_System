/**
 * Error Display Components
 * Consistent error message display
 */

import React from 'react';
import {
  Alert,
  AlertTitle,
  Box,
  Button,
  Typography,
  Paper,
} from '@mui/material';
import {
  Error as ErrorIcon,
  Refresh as RefreshIcon,
  Warning as WarningIcon,
} from '@mui/icons-material';

export interface ErrorDisplayProps {
  error: string | Error;
  title?: string;
  severity?: 'error' | 'warning' | 'info';
  onRetry?: () => void;
  onDismiss?: () => void;
  variant?: 'standard' | 'filled' | 'outlined';
}

export const ErrorDisplay: React.FC<ErrorDisplayProps> = ({
  error,
  title,
  severity = 'error',
  onRetry,
  onDismiss,
  variant = 'standard',
}) => {
  const errorMessage = typeof error === 'string' ? error : error.message;

  return (
    <Alert
      severity={severity}
      variant={variant}
      onClose={onDismiss}
      action={
        onRetry ? (
          <Button color="inherit" size="small" onClick={onRetry} startIcon={<RefreshIcon />}>
            Retry
          </Button>
        ) : undefined
      }
      sx={{
        '& .MuiAlert-message': {
          whiteSpace: 'pre-line', // Preserve line breaks
        },
      }}
    >
      {title && <AlertTitle>{title}</AlertTitle>}
      {errorMessage}
    </Alert>
  );
};

export interface ErrorBoundaryFallbackProps {
  error: Error;
  resetError: () => void;
}

export const ErrorBoundaryFallback: React.FC<ErrorBoundaryFallbackProps> = ({
  error,
  resetError,
}) => (
  <Box
    sx={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '100vh',
      p: 3,
    }}
  >
    <Paper
      sx={{
        p: 4,
        maxWidth: 600,
        textAlign: 'center',
      }}
    >
      <ErrorIcon sx={{ fontSize: 64, color: 'error.main', mb: 2 }} />
      <Typography variant="h5" gutterBottom>
        Something went wrong
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        {error.message || 'An unexpected error occurred'}
      </Typography>
      {process.env.NODE_ENV === 'development' && (
        <Paper
          variant="outlined"
          sx={{
            p: 2,
            mb: 3,
            textAlign: 'left',
            backgroundColor: 'grey.50',
            fontFamily: 'monospace',
            fontSize: '0.875rem',
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-word',
            maxHeight: 200,
            overflow: 'auto',
          }}
        >
          {error.stack}
        </Paper>
      )}
      <Button variant="contained" onClick={resetError} startIcon={<RefreshIcon />}>
        Try Again
      </Button>
    </Paper>
  </Box>
);

export interface NetworkErrorProps {
  onRetry?: () => void;
}

export const NetworkError: React.FC<NetworkErrorProps> = ({ onRetry }) => (
  <ErrorDisplay
    error="Unable to connect to the server. Please check your internet connection."
    title="Network Error"
    severity="error"
    onRetry={onRetry}
  />
);

export interface ValidationErrorProps {
  message: string;
  onDismiss?: () => void;
}

export const ValidationError: React.FC<ValidationErrorProps> = ({ message, onDismiss }) => (
  <ErrorDisplay
    error={message}
    title="Validation Error"
    severity="warning"
    onDismiss={onDismiss}
  />
);

export default {
  ErrorDisplay,
  ErrorBoundaryFallback,
  NetworkError,
  ValidationError,
};
