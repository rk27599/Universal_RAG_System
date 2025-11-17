/**
 * Advanced Settings Component
 * RAG settings, temperature, and source count controls
 */

import React from 'react';
import { Box, FormControlLabel, Switch, TextField, Typography, Collapse } from '@mui/material';

export interface AdvancedSettingsProps {
  show: boolean;
  useRAG: boolean;
  temperature: number;
  topK: number;
  onUseRAGChange: (value: boolean) => void;
  onTemperatureChange: (value: number) => void;
  onTopKChange: (value: number) => void;
}

export const AdvancedSettings: React.FC<AdvancedSettingsProps> = ({
  show,
  useRAG,
  temperature,
  topK,
  onUseRAGChange,
  onTemperatureChange,
  onTopKChange,
}) => {
  return (
    <Collapse in={show}>
      <Box sx={{ mt: 2, display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
        <FormControlLabel
          control={<Switch checked={useRAG} onChange={(e) => onUseRAGChange(e.target.checked)} />}
          label="Use RAG"
        />

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Typography variant="caption">Temperature:</Typography>
          <TextField
            type="number"
            size="small"
            value={temperature}
            onChange={(e) => onTemperatureChange(Number(e.target.value))}
            inputProps={{ min: 0, max: 2, step: 0.1 }}
            sx={{ width: 80 }}
          />
        </Box>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Typography variant="caption">Sources:</Typography>
          <TextField
            type="number"
            size="small"
            value={topK}
            onChange={(e) => onTopKChange(Number(e.target.value))}
            inputProps={{ min: 1, step: 1 }}
            sx={{ width: 80 }}
          />
        </Box>
      </Box>
    </Collapse>
  );
};

export default AdvancedSettings;
