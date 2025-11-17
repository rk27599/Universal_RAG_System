/**
 * Source Citations Component
 * Displays document sources used in RAG responses
 */

import React from 'react';
import {
  Box,
  Typography,
  Collapse,
  List,
  ListItem,
  ListItemText,
  Divider,
  Chip,
} from '@mui/material';
import {
  Description as DocumentIcon,
  ExpandMore as ExpandMoreIcon,
} from '@mui/icons-material';
import { DocumentSource } from '../../../services/api';
import { SourceBox } from '../../../theme/components';

export interface SourceCitationsProps {
  sources: DocumentSource[];
  messageId: string;
  isExpanded: boolean;
  isUser?: boolean;
  onToggle: (messageId: string) => void;
}

export const SourceCitations: React.FC<SourceCitationsProps> = ({
  sources,
  messageId,
  isExpanded,
  isUser = false,
  onToggle,
}) => {
  if (!sources || sources.length === 0) {
    return null;
  }

  return (
    <Box sx={{ mt: 1 }}>
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          gap: 0.5,
          cursor: 'pointer',
          '&:hover': { opacity: 0.7 },
        }}
        onClick={() => onToggle(messageId)}
      >
        <DocumentIcon sx={{ fontSize: '0.9rem', color: 'text.secondary' }} />
        <Typography variant="caption" sx={{ color: 'text.secondary' }}>
          {sources.length} source{sources.length > 1 ? 's' : ''}
        </Typography>
        <ExpandMoreIcon
          sx={{
            fontSize: '1rem',
            color: 'text.secondary',
            transform: isExpanded ? 'rotate(180deg)' : 'rotate(0deg)',
            transition: 'transform 0.2s',
          }}
        />
      </Box>

      <Collapse in={isExpanded}>
        <SourceBox isUser={isUser}>
          <List dense disablePadding>
            {sources.map((source, idx) => (
              <React.Fragment key={source.chunkId}>
                {idx > 0 && <Divider sx={{ my: 0.5 }} />}
                <ListItem disablePadding sx={{ py: 0.5 }}>
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography variant="caption" sx={{ fontWeight: 'bold' }}>
                          {source.documentTitle}
                        </Typography>
                        <Chip
                          size="small"
                          label={`${(source.similarity * 100).toFixed(0)}%`}
                          color="success"
                          sx={{ height: 16, fontSize: '0.65rem' }}
                        />
                      </Box>
                    }
                    secondary={
                      <Typography variant="caption" sx={{ fontSize: '0.7rem' }}>
                        {source.section}
                      </Typography>
                    }
                  />
                </ListItem>
              </React.Fragment>
            ))}
          </List>
        </SourceBox>
      </Collapse>
    </Box>
  );
};

export default SourceCitations;
