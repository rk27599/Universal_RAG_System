import React, { useState } from 'react';
import {
  Box,
  Switch,
  TextField,
  Typography,
  FormControlLabel,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Button,
  Alert,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';

const DEFAULT_PROMPT = `You are an expert technical assistant specializing in Material Studio. Your role is to provide accurate, helpful answers about Material Studio using ONLY the retrieved documentation and code context provided to you.

## Core Principles

### 1. Accuracy and Grounding
- Answer questions using ONLY the information from the retrieved context below
- NEVER generate information that is not present in the provided documentation or code
- If the context doesn't contain enough information to answer completely, acknowledge this limitation
- When uncertain, explicitly state your uncertainty rather than guessing

### 2. Citation and Transparency
- Always cite specific sources when making claims (e.g., "According to the Forcite Module API documentation…")
- Reference specific code files, function names, or documentation sections when applicable
- If information comes from multiple sources, acknowledge all relevant sources

### 3. Response Quality
- Provide clear, concise answers (2–4 sentences for simple queries, longer for complex topics)
- Use proper formatting: code blocks for code snippets, bullet points for lists, headers for organization
- Include relevant code examples when they help clarify the answer
- Explain technical concepts in accessible language while maintaining accuracy

Remember: Only use information from the provided context. If you cannot answer based on the context, say so clearly.`;

interface PromptSettingsProps {
  useExpertPrompt: boolean;
  onUseExpertPromptChange: (value: boolean) => void;
  customPrompt?: string;
  onCustomPromptChange: (value: string) => void;
}

export const PromptSettings: React.FC<PromptSettingsProps> = ({
  useExpertPrompt,
  onUseExpertPromptChange,
  customPrompt,
  onCustomPromptChange,
}) => {
  const [expanded, setExpanded] = useState(false);

  const handleResetToDefault = () => {
    onCustomPromptChange('');
    setExpanded(false);
  };

  const isUsingCustom = customPrompt && customPrompt.trim().length > 0;

  return (
    <Box sx={{ mb: 3 }}>
      <Typography variant="h6" gutterBottom>
        System Prompt Settings
      </Typography>

      <FormControlLabel
        control={
          <Switch
            checked={useExpertPrompt}
            onChange={(e) => onUseExpertPromptChange(e.target.checked)}
            color="primary"
          />
        }
        label="Use Material Studio Expert System Prompt"
      />

      <Typography variant="caption" color="text.secondary" sx={{ mt: 1, mb: 2, display: 'block' }}>
        When enabled, the AI will act as a Material Studio expert and only use information from the retrieved documentation.
        This ensures accurate, citation-based responses and prevents hallucination.
      </Typography>

      {useExpertPrompt && (
        <>
          <Alert severity="info" sx={{ mb: 2 }}>
            <strong>Expert Prompt Active:</strong> The AI will cite sources, acknowledge limitations,
            and refuse to answer questions without sufficient documentation context.
          </Alert>

          <Accordion
            expanded={expanded}
            onChange={(_, isExpanded) => setExpanded(isExpanded)}
            sx={{ mb: 2 }}
          >
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography>
                {isUsingCustom ? '✏️ Custom System Prompt (Active)' : 'Customize System Prompt (Optional)'}
              </Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Box>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Advanced: Customize the system prompt to adjust the AI's behavior.
                  Leave empty to use the default Material Studio expert prompt.
                </Typography>

                <TextField
                  multiline
                  rows={12}
                  fullWidth
                  variant="outlined"
                  placeholder={DEFAULT_PROMPT}
                  value={customPrompt || ''}
                  onChange={(e) => onCustomPromptChange(e.target.value)}
                  helperText={
                    isUsingCustom
                      ? `Using custom prompt (${customPrompt.length} characters)`
                      : 'Leave empty to use default Material Studio expert prompt'
                  }
                  sx={{
                    fontFamily: 'monospace',
                    fontSize: '0.85rem',
                  }}
                />

                <Box sx={{ mt: 2, display: 'flex', gap: 1 }}>
                  <Button
                    variant="outlined"
                    size="small"
                    onClick={handleResetToDefault}
                    disabled={!isUsingCustom}
                  >
                    Reset to Default
                  </Button>
                  <Button
                    variant="outlined"
                    size="small"
                    onClick={() => {
                      navigator.clipboard.writeText(DEFAULT_PROMPT);
                    }}
                  >
                    Copy Default Prompt
                  </Button>
                </Box>
              </Box>
            </AccordionDetails>
          </Accordion>
        </>
      )}

      {!useExpertPrompt && (
        <Alert severity="warning" sx={{ mt: 2 }}>
          <strong>Expert Prompt Disabled:</strong> The AI will use general behavior and may not cite sources
          or stay strictly grounded in the documentation.
        </Alert>
      )}
    </Box>
  );
};
