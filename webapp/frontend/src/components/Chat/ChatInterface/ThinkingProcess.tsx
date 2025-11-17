/**
 * Thinking Process Component
 * Displays LLM thinking process (for models like Qwen3-4B-Thinking)
 */

import React, { useState, useMemo } from 'react';
import { Box, Typography, Collapse } from '@mui/material';
import { Psychology as ThinkingIcon, ExpandMore as ExpandMoreIcon } from '@mui/icons-material';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import remarkGfm from 'remark-gfm';
import { ThinkingBox } from '../../../theme/components';

export interface ThinkingProcessProps {
  thinking: string;
  isUser?: boolean;
  markdownComponents?: any;
}

export const ThinkingProcess: React.FC<ThinkingProcessProps> = ({
  thinking,
  isUser = false,
  markdownComponents,
}) => {
  const [showThinking, setShowThinking] = useState(false);

  // Default markdown components if not provided
  const defaultMarkdownComponents = useMemo(() => ({
    code: ({ node, className, children, ...props }: any) => {
      const match = /language-(\w+)/.exec(className || '');
      const isInline = !className;
      const content = String(children).replace(/\n$/, '');

      if (!isInline && match) {
        return (
          <SyntaxHighlighter
            style={oneDark}
            language={match[1]}
            PreTag="div"
            customStyle={{
              margin: '1em 0',
              borderRadius: '4px',
            }}
          >
            {content}
          </SyntaxHighlighter>
        );
      }

      return (
        <code
          className={className}
          style={{
            backgroundColor: isUser ? 'rgba(255,255,255,0.1)' : '#f5f5f5',
            padding: '2px 4px',
            borderRadius: '3px',
            fontSize: '0.9em',
            fontFamily: 'monospace',
          }}
        >
          {children}
        </code>
      );
    },
  }), [isUser]);

  const components = markdownComponents || defaultMarkdownComponents;

  return (
    <Box sx={{ mb: 1 }}>
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          gap: 0.5,
          cursor: 'pointer',
          '&:hover': { opacity: 0.7 },
        }}
        onClick={() => setShowThinking(!showThinking)}
      >
        <ThinkingIcon sx={{ fontSize: '0.9rem', color: 'text.secondary' }} />
        <Typography variant="caption" sx={{ color: 'text.secondary', fontStyle: 'italic' }}>
          Show thinking process
        </Typography>
        <ExpandMoreIcon
          sx={{
            fontSize: '1rem',
            color: 'text.secondary',
            transform: showThinking ? 'rotate(180deg)' : 'rotate(0deg)',
            transition: 'transform 0.2s',
          }}
        />
      </Box>

      <Collapse in={showThinking}>
        <ThinkingBox isUser={isUser}>
          <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
            {thinking}
          </ReactMarkdown>
        </ThinkingBox>
      </Collapse>
    </Box>
  );
};

export default ThinkingProcess;
