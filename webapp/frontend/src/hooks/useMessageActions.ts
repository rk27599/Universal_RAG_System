/**
 * useMessageActions Hook
 * Centralized message action handlers (copy, regenerate, etc.)
 */

import { useCallback, useState } from 'react';

export interface MessageActionsResult {
  // Handlers
  handleCopy: (content: string) => void;
  handleRegenerate: (messageId: string) => Promise<void>;
  handleToggleSources: (messageId: string) => void;

  // State
  expandedSources: Set<string>;
  regeneratingMessageId: string | null;
  snackbarMessage: string;

  // Setters
  clearSnackbar: () => void;
}

interface UseMessageActionsOptions {
  regenerateMessageFn?: (messageId: string) => Promise<boolean>;
  onRegenerateSuccess?: () => void;
  onRegenerateError?: (error: any) => void;
}

/**
 * Custom hook for message actions (copy, regenerate, toggle sources)
 */
export function useMessageActions(options: UseMessageActionsOptions = {}): MessageActionsResult {
  const {
    regenerateMessageFn,
    onRegenerateSuccess,
    onRegenerateError,
  } = options;

  const [expandedSources, setExpandedSources] = useState<Set<string>>(new Set());
  const [regeneratingMessageId, setRegeneratingMessageId] = useState<string | null>(null);
  const [snackbarMessage, setSnackbarMessage] = useState('');

  // Copy message to clipboard
  const handleCopy = useCallback((content: string) => {
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

  // Toggle source citations visibility
  const handleToggleSources = useCallback((messageId: string) => {
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

  // Regenerate message
  const handleRegenerate = useCallback(async (messageId: string) => {
    if (!regenerateMessageFn) {
      console.warn('No regenerate function provided');
      return;
    }

    try {
      setRegeneratingMessageId(messageId);
      const success = await regenerateMessageFn(messageId);
      setRegeneratingMessageId(null);

      if (success) {
        setSnackbarMessage('Message regenerated successfully');
        onRegenerateSuccess?.();
      } else {
        setSnackbarMessage('Failed to regenerate message - no response from server');
      }
    } catch (error: any) {
      setRegeneratingMessageId(null);
      console.error('Regenerate error:', error);
      setSnackbarMessage(`Failed to regenerate: ${error.message || 'Unknown error'}`);
      onRegenerateError?.(error);
    }
  }, [regenerateMessageFn, onRegenerateSuccess, onRegenerateError]);

  const clearSnackbar = useCallback(() => {
    setSnackbarMessage('');
  }, []);

  return {
    handleCopy,
    handleRegenerate,
    handleToggleSources,
    expandedSources,
    regeneratingMessageId,
    snackbarMessage,
    clearSnackbar,
  };
}

export default useMessageActions;
