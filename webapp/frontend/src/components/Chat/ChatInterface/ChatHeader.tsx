/**
 * Chat Header Component
 * Contains title, connection status, model selector, and settings toggle
 */

import React from 'react';
import {
  Box,
  Typography,
  IconButton,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
} from '@mui/material';
import { Settings as SettingsIcon } from '@mui/icons-material';
import { HeaderPaper } from '../../../theme/components';
import { ConnectionStatus } from '../../shared/StatusBadge';
import { AdvancedSettings } from './AdvancedSettings';

export interface ChatHeaderProps {
  isConnected: boolean;
  selectedModel: string;
  availableModels: string[];
  showSettings: boolean;
  useRAG: boolean;
  temperature: number;
  topK: number;
  onModelChange: (model: string) => void;
  onSettingsToggle: () => void;
  onUseRAGChange: (value: boolean) => void;
  onTemperatureChange: (value: number) => void;
  onTopKChange: (value: number) => void;
}

export const ChatHeader: React.FC<ChatHeaderProps> = ({
  isConnected,
  selectedModel,
  availableModels,
  showSettings,
  useRAG,
  temperature,
  topK,
  onModelChange,
  onSettingsToggle,
  onUseRAGChange,
  onTemperatureChange,
  onTopKChange,
}) => {
  return (
    <HeaderPaper>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Typography variant="h6">Chat</Typography>

          {/* Connection Status */}
          <ConnectionStatus isConnected={isConnected} />

          {/* Model Selector */}
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Model</InputLabel>
            <Select value={selectedModel} label="Model" onChange={(e) => onModelChange(e.target.value)}>
              {availableModels.map((model) => (
                <MenuItem key={model} value={model}>
                  {model}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Box>

        {/* Settings Toggle */}
        <IconButton onClick={onSettingsToggle}>
          <SettingsIcon />
        </IconButton>
      </Box>

      {/* Advanced Settings */}
      <AdvancedSettings
        show={showSettings}
        useRAG={useRAG}
        temperature={temperature}
        topK={topK}
        onUseRAGChange={onUseRAGChange}
        onTemperatureChange={onTemperatureChange}
        onTopKChange={onTopKChange}
      />
    </HeaderPaper>
  );
};

export default ChatHeader;
