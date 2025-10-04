/**
 * Error Boundary - Global Error Handling Component
 * Catches and handles React errors gracefully
 */

import React, { Component, ReactNode } from 'react';
import {
  Box,
  Typography,
  Button,
  Alert,
  AlertTitle,
  Card,
  CardContent,
  Stack,
  Divider,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Error as ErrorIcon,
  Home as HomeIcon,
} from '@mui/icons-material';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: string | null;
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error,
      errorInfo: error.stack || 'No stack trace available',
    };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);

    // Log error to monitoring service (if available)
    this.logErrorToService(error, errorInfo);
  }

  logErrorToService = (error: Error, errorInfo: React.ErrorInfo) => {
    // In a production environment, send to monitoring service
    const errorData = {
      message: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href,
    };

    // Store in localStorage for debugging
    const errorLog = JSON.parse(localStorage.getItem('errorLog') || '[]');
    errorLog.push(errorData);

    // Keep only last 10 errors
    if (errorLog.length > 10) {
      errorLog.shift();
    }

    localStorage.setItem('errorLog', JSON.stringify(errorLog));
  };

  handleRetry = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  handleReload = () => {
    window.location.reload();
  };

  handleGoHome = () => {
    window.location.href = '/';
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <Box
          sx={{
            minHeight: '100vh',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            bgcolor: 'grey.50',
            p: 3,
          }}
        >
          <Card sx={{ maxWidth: 600, width: '100%' }}>
            <CardContent sx={{ p: 4 }}>
              <Stack spacing={3} alignItems="center">
                <ErrorIcon sx={{ fontSize: 64, color: 'error.main' }} />

                <Typography variant="h4" textAlign="center" color="error">
                  Something went wrong
                </Typography>

                <Alert severity="error" sx={{ width: '100%' }}>
                  <AlertTitle>Application Error</AlertTitle>
                  The application has encountered an unexpected error.
                  Please try refreshing the page or returning to the home screen.
                </Alert>

                {/* Error Details (Development) */}
                {process.env.NODE_ENV === 'development' && this.state.error && (
                  <Card sx={{ width: '100%', bgcolor: 'grey.100' }}>
                    <CardContent>
                      <Typography variant="subtitle2" gutterBottom color="error">
                        Error Details:
                      </Typography>
                      <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>
                        {this.state.error.message}
                      </Typography>

                      {this.state.errorInfo && (
                        <>
                          <Divider sx={{ my: 1 }} />
                          <Typography variant="subtitle2" gutterBottom color="error">
                            Stack Trace:
                          </Typography>
                          <Typography
                            variant="body2"
                            sx={{
                              fontFamily: 'monospace',
                              fontSize: '0.7rem',
                              whiteSpace: 'pre-wrap',
                              maxHeight: 200,
                              overflow: 'auto',
                            }}
                          >
                            {this.state.errorInfo}
                          </Typography>
                        </>
                      )}
                    </CardContent>
                  </Card>
                )}

                <Stack direction="row" spacing={2}>
                  <Button
                    variant="contained"
                    color="primary"
                    startIcon={<RefreshIcon />}
                    onClick={this.handleRetry}
                  >
                    Try Again
                  </Button>

                  <Button
                    variant="outlined"
                    color="primary"
                    startIcon={<RefreshIcon />}
                    onClick={this.handleReload}
                  >
                    Reload Page
                  </Button>

                  <Button
                    variant="outlined"
                    color="secondary"
                    startIcon={<HomeIcon />}
                    onClick={this.handleGoHome}
                  >
                    Go Home
                  </Button>
                </Stack>

                <Typography variant="caption" color="text.secondary" textAlign="center">
                  If this problem persists, please check the application logs or contact support.
                  Error ID: {Date.now().toString(36)}
                </Typography>
              </Stack>
            </CardContent>
          </Card>
        </Box>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;