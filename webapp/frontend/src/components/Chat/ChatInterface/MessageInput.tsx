/**
 * Message Input Component
 * Text input field with send/stop button
 */

import React, { useRef, useEffect, useMemo } from 'react';
import { Box, CircularProgress } from '@mui/material';
import { Send as SendIcon, Stop as StopIcon } from '@mui/icons-material';
import { InputPaper, StyledTextField, RoundedIconButton } from '../../../theme/components';

export interface MessageInputProps {
  value: string;
  isLoading: boolean;
  isTyping: boolean;
  disabled?: boolean;
  placeholder?: string;
  onChange: (value: string) => void;
  onSend: () => void;
  onStop: () => void;
  onKeyPress?: (event: React.KeyboardEvent) => void;
  autoFocus?: boolean;
}

export const MessageInput: React.FC<MessageInputProps> = ({
  value,
  isLoading,
  isTyping,
  disabled = false,
  placeholder = 'Type your message...',
  onChange,
  onSend,
  onStop,
  onKeyPress,
  autoFocus = true,
}) => {
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-focus on mount
  useEffect(() => {
    if (autoFocus) {
      inputRef.current?.focus();
    }
  }, [autoFocus]);

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      if (isTyping) {
        onStop();
      } else {
        onSend();
      }
    }
    onKeyPress?.(event);
  };

  const handleButtonClick = () => {
    if (isTyping) {
      onStop();
    } else {
      onSend();
    }
  };

  const isDisabled = !isTyping && (!value.trim() || isLoading || disabled);

  const sendButtonSx = useMemo(
    () => ({
      p: 1.5,
      color: 'white',
      backgroundColor: isTyping ? 'error.main' : 'primary.main',
      '&:hover': {
        backgroundColor: isTyping ? 'error.dark' : 'primary.dark',
      },
      '&:disabled': {
        backgroundColor: 'grey.300',
      },
    }),
    [isTyping]
  );

  return (
    <InputPaper>
      <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-end' }}>
        <StyledTextField
          ref={inputRef}
          multiline
          maxRows={4}
          fullWidth
          variant="outlined"
          placeholder={placeholder}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyPress={handleKeyPress}
          disabled={isLoading || disabled}
        />

        <RoundedIconButton
          color={isTyping ? 'error' : 'primary'}
          onClick={handleButtonClick}
          disabled={isDisabled}
          sx={sendButtonSx}
        >
          {isLoading ? (
            <CircularProgress size={20} color="inherit" />
          ) : isTyping ? (
            <StopIcon />
          ) : (
            <SendIcon />
          )}
        </RoundedIconButton>
      </Box>
    </InputPaper>
  );
};

export default MessageInput;
