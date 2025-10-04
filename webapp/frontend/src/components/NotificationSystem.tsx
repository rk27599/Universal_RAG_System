/**
 * Notification System - Global Toast Notifications
 * Provides consistent user feedback across the application
 */

import React, { createContext, useContext, useReducer, ReactNode } from 'react';
import {
  Snackbar,
  Alert,
  AlertTitle,
  Slide,
  SlideProps,
  Box,
  IconButton,
  LinearProgress,
} from '@mui/material';
import {
  Close as CloseIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
} from '@mui/icons-material';

// Notification types
type NotificationType = 'success' | 'error' | 'warning' | 'info';

interface Notification {
  id: string;
  type: NotificationType;
  title?: string;
  message: string;
  duration?: number;
  persistent?: boolean;
  actions?: Array<{
    label: string;
    action: () => void;
    color?: 'primary' | 'secondary';
  }>;
  progress?: {
    value: number;
    total: number;
  };
}

interface NotificationState {
  notifications: Notification[];
}

type NotificationAction =
  | { type: 'ADD_NOTIFICATION'; payload: Notification }
  | { type: 'REMOVE_NOTIFICATION'; payload: string }
  | { type: 'UPDATE_NOTIFICATION'; payload: { id: string; updates: Partial<Notification> } }
  | { type: 'CLEAR_ALL' };

interface NotificationContextType {
  showNotification: (notification: Omit<Notification, 'id'>) => string;
  updateNotification: (id: string, updates: Partial<Notification>) => void;
  removeNotification: (id: string) => void;
  clearAllNotifications: () => void;

  // Convenience methods
  showSuccess: (message: string, title?: string, options?: Partial<Notification>) => string;
  showError: (message: string, title?: string, options?: Partial<Notification>) => string;
  showWarning: (message: string, title?: string, options?: Partial<Notification>) => string;
  showInfo: (message: string, title?: string, options?: Partial<Notification>) => string;

  // Progress notifications
  showProgress: (message: string, progress: { value: number; total: number }) => string;
  updateProgress: (id: string, progress: { value: number; total: number }) => void;
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

const initialState: NotificationState = {
  notifications: [],
};

function notificationReducer(state: NotificationState, action: NotificationAction): NotificationState {
  switch (action.type) {
    case 'ADD_NOTIFICATION':
      return {
        ...state,
        notifications: [...state.notifications, action.payload],
      };

    case 'REMOVE_NOTIFICATION':
      return {
        ...state,
        notifications: state.notifications.filter(n => n.id !== action.payload),
      };

    case 'UPDATE_NOTIFICATION':
      return {
        ...state,
        notifications: state.notifications.map(n =>
          n.id === action.payload.id ? { ...n, ...action.payload.updates } : n
        ),
      };

    case 'CLEAR_ALL':
      return {
        ...state,
        notifications: [],
      };

    default:
      return state;
  }
}

function SlideTransition(props: SlideProps) {
  return <Slide {...props} direction="up" />;
}

interface NotificationProviderProps {
  children: ReactNode;
}

export const NotificationProvider: React.FC<NotificationProviderProps> = ({ children }) => {
  const [state, dispatch] = useReducer(notificationReducer, initialState);

  const generateId = () => `notification_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

  const showNotification = (notification: Omit<Notification, 'id'>): string => {
    const id = generateId();
    const newNotification: Notification = {
      id,
      duration: 6000,
      persistent: false,
      ...notification,
    };

    dispatch({ type: 'ADD_NOTIFICATION', payload: newNotification });

    // Auto-remove after duration (if not persistent)
    if (!newNotification.persistent && newNotification.duration) {
      setTimeout(() => {
        dispatch({ type: 'REMOVE_NOTIFICATION', payload: id });
      }, newNotification.duration);
    }

    return id;
  };

  const updateNotification = (id: string, updates: Partial<Notification>) => {
    dispatch({ type: 'UPDATE_NOTIFICATION', payload: { id, updates } });
  };

  const removeNotification = (id: string) => {
    dispatch({ type: 'REMOVE_NOTIFICATION', payload: id });
  };

  const clearAllNotifications = () => {
    dispatch({ type: 'CLEAR_ALL' });
  };

  // Convenience methods
  const showSuccess = (message: string, title?: string, options?: Partial<Notification>): string =>
    showNotification({ type: 'success', message, title, ...options });

  const showError = (message: string, title?: string, options?: Partial<Notification>): string =>
    showNotification({ type: 'error', message, title, persistent: true, ...options });

  const showWarning = (message: string, title?: string, options?: Partial<Notification>): string =>
    showNotification({ type: 'warning', message, title, ...options });

  const showInfo = (message: string, title?: string, options?: Partial<Notification>): string =>
    showNotification({ type: 'info', message, title, ...options });

  const showProgress = (message: string, progress: { value: number; total: number }): string =>
    showNotification({
      type: 'info',
      message,
      progress,
      persistent: true,
    });

  const updateProgress = (id: string, progress: { value: number; total: number }) => {
    updateNotification(id, { progress });

    // Auto-remove when complete
    if (progress.value >= progress.total) {
      setTimeout(() => removeNotification(id), 2000);
    }
  };

  const contextValue: NotificationContextType = {
    showNotification,
    updateNotification,
    removeNotification,
    clearAllNotifications,
    showSuccess,
    showError,
    showWarning,
    showInfo,
    showProgress,
    updateProgress,
  };

  const renderNotification = (notification: Notification) => {
    const { id, type, title, message, persistent, actions, progress } = notification;

    const iconMap = {
      success: <SuccessIcon />,
      error: <ErrorIcon />,
      warning: <WarningIcon />,
      info: <InfoIcon />,
    };

    return (
      <Snackbar
        key={id}
        open={true}
        anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
        TransitionComponent={SlideTransition}
        sx={{
          position: 'relative',
          top: `${state.notifications.findIndex(n => n.id === id) * 80}px`,
        }}
      >
        <Alert
          severity={type}
          icon={iconMap[type]}
          action={
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              {actions?.map((action, index) => (
                <IconButton
                  key={index}
                  size="small"
                  onClick={action.action}
                  color={action.color || 'inherit'}
                >
                  {action.label}
                </IconButton>
              ))}
              <IconButton
                size="small"
                onClick={() => removeNotification(id)}
                color="inherit"
              >
                <CloseIcon fontSize="small" />
              </IconButton>
            </Box>
          }
          sx={{
            width: '100%',
            minWidth: 300,
            maxWidth: 500,
          }}
        >
          {title && <AlertTitle>{title}</AlertTitle>}
          {message}

          {progress && (
            <Box sx={{ mt: 1 }}>
              <LinearProgress
                variant="determinate"
                value={(progress.value / progress.total) * 100}
                sx={{ mb: 1 }}
              />
              <Box sx={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem' }}>
                <span>{progress.value} of {progress.total}</span>
                <span>{Math.round((progress.value / progress.total) * 100)}%</span>
              </Box>
            </Box>
          )}
        </Alert>
      </Snackbar>
    );
  };

  return (
    <NotificationContext.Provider value={contextValue}>
      {children}

      {/* Render all notifications */}
      <Box sx={{ position: 'fixed', top: 24, right: 24, zIndex: 9999 }}>
        {state.notifications.map(renderNotification)}
      </Box>
    </NotificationContext.Provider>
  );
};

export const useNotification = (): NotificationContextType => {
  const context = useContext(NotificationContext);
  if (context === undefined) {
    throw new Error('useNotification must be used within a NotificationProvider');
  }
  return context;
};

export default NotificationContext;