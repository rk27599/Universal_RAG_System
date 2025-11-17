/**
 * Styled Component Patterns
 * Reusable styled components to reduce sx prop verbosity
 */

import { styled } from '@mui/material/styles';
import { Box, Card, Paper, IconButton, TextField } from '@mui/material';
import { spacing, borderRadius, shadows } from './tokens';

// ============================================================================
// MESSAGE COMPONENTS
// ============================================================================

export const MessageCard = styled(Card, {
  shouldForwardProp: (prop) => prop !== 'isUser',
})<{ isUser?: boolean }>(({ theme, isUser }) => ({
  maxWidth: '70%',
  backgroundColor: isUser ? theme.palette.primary.main : theme.palette.background.paper,
  color: isUser ? theme.palette.primary.contrastText : theme.palette.text.primary,
  boxShadow: shadows.card,
  borderRadius: borderRadius.lg,
  transition: theme.transitions.create(['box-shadow', 'transform'], {
    duration: theme.transitions.duration.short,
  }),
  '&:hover': {
    boxShadow: shadows.elevated,
  },
}));

export const MessagesContainer = styled(Box)(({ theme }) => ({
  flexGrow: 1,
  overflow: 'auto',
  padding: theme.spacing(2),
  backgroundColor: theme.palette.mode === 'dark' ? theme.palette.grey[900] : theme.palette.grey[50],
  minHeight: '300px',
  position: 'relative',
}));

export const MessageContentBox = styled(Box, {
  shouldForwardProp: (prop) => prop !== 'isUser',
})<{ isUser?: boolean }>(({ theme, isUser }) => ({
  '& p': { marginBottom: theme.spacing(1) },
  '& ul, & ol': { paddingLeft: theme.spacing(2), marginBottom: theme.spacing(1) },
  '& li': { marginBottom: theme.spacing(0.5) },
  '& h1, & h2, & h3, & h4, & h5, & h6': {
    fontWeight: 'bold',
    marginTop: theme.spacing(2),
    marginBottom: theme.spacing(1),
    '&:first-of-type': { marginTop: 0 },
  },
  '& table': {
    borderCollapse: 'collapse',
    width: '100%',
    marginBottom: theme.spacing(2),
    border: '1px solid',
    borderColor: theme.palette.divider,
  },
  '& th, & td': {
    border: '1px solid',
    borderColor: theme.palette.divider,
    padding: theme.spacing(1),
    textAlign: 'left',
  },
  '& th': {
    backgroundColor: theme.palette.mode === 'dark' ? theme.palette.grey[800] : theme.palette.grey[100],
    fontWeight: 'bold',
  },
  '& code': {
    paddingLeft: theme.spacing(0.5),
    paddingRight: theme.spacing(0.5),
    paddingTop: theme.spacing(0.25),
    paddingBottom: theme.spacing(0.25),
    borderRadius: borderRadius.sm,
    fontSize: '0.9em',
    fontFamily: 'monospace',
    backgroundColor: isUser ? 'rgba(255,255,255,0.1)' : theme.palette.grey[100],
  },
}));

// ============================================================================
// INPUT COMPONENTS
// ============================================================================

export const StyledTextField = styled(TextField)(({ theme }) => ({
  '& .MuiOutlinedInput-root': {
    borderRadius: borderRadius.md,
    transition: theme.transitions.create(['border-color', 'box-shadow'], {
      duration: theme.transitions.duration.short,
    }),
    '&:hover': {
      '& .MuiOutlinedInput-notchedOutline': {
        borderColor: theme.palette.primary.light,
      },
    },
    '&.Mui-focused': {
      '& .MuiOutlinedInput-notchedOutline': {
        borderWidth: 2,
      },
    },
  },
}));

export const RoundedIconButton = styled(IconButton)(({ theme }) => ({
  borderRadius: borderRadius.lg,
  padding: theme.spacing(1.5),
  transition: theme.transitions.create(['background-color', 'transform'], {
    duration: theme.transitions.duration.short,
  }),
  '&:hover': {
    transform: 'scale(1.05)',
  },
  '&:active': {
    transform: 'scale(0.95)',
  },
}));

// ============================================================================
// LAYOUT COMPONENTS
// ============================================================================

export const HeaderPaper = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(2),
  borderRadius: 0,
  borderBottom: `1px solid ${theme.palette.divider}`,
  backgroundColor: theme.palette.background.paper,
}));

export const InputPaper = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(2),
  borderRadius: 0,
  borderTop: `1px solid ${theme.palette.divider}`,
  backgroundColor: theme.palette.background.paper,
}));

export const CenteredBox = styled(Box)({
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  textAlign: 'center',
  height: '100%',
});

export const FlexRow = styled(Box)({
  display: 'flex',
  alignItems: 'center',
  gap: spacing.md,
});

export const FlexColumn = styled(Box)({
  display: 'flex',
  flexDirection: 'column',
  gap: spacing.md,
});

// ============================================================================
// SOURCE & THINKING COMPONENTS
// ============================================================================

export const SourceBox = styled(Box, {
  shouldForwardProp: (prop) => prop !== 'isUser',
})<{ isUser?: boolean }>(({ theme, isUser }) => ({
  marginTop: theme.spacing(1),
  padding: theme.spacing(1),
  backgroundColor: isUser ? 'rgba(255,255,255,0.1)' : theme.palette.mode === 'dark' ? theme.palette.grey[800] : theme.palette.grey[50],
  borderRadius: borderRadius.md,
}));

export const ThinkingBox = styled(Box, {
  shouldForwardProp: (prop) => prop !== 'isUser',
})<{ isUser?: boolean }>(({ theme, isUser }) => ({
  marginTop: theme.spacing(1),
  padding: theme.spacing(1.5),
  backgroundColor: isUser ? 'rgba(255,255,255,0.05)' : theme.palette.mode === 'dark' ? theme.palette.grey[800] : theme.palette.grey[50],
  borderRadius: borderRadius.md,
  borderLeft: `3px solid ${theme.palette.primary.light}`,
  opacity: 0.7,
}));

// ============================================================================
// CARD COMPONENTS
// ============================================================================

export const ElevatedCard = styled(Card)(({ theme }) => ({
  borderRadius: borderRadius.lg,
  boxShadow: shadows.card,
  transition: theme.transitions.create(['box-shadow', 'transform'], {
    duration: theme.transitions.duration.short,
  }),
  '&:hover': {
    boxShadow: shadows.elevated,
    transform: 'translateY(-2px)',
  },
}));

// ============================================================================
// EMPTY STATE COMPONENTS
// ============================================================================

export const EmptyStateContainer = styled(Box)(({ theme }) => ({
  height: '100%',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  textAlign: 'center',
  padding: theme.spacing(4),
}));

export const EmptyStateContent = styled(Box)(({ theme }) => ({
  maxWidth: 400,
  '& .MuiSvgIcon-root': {
    fontSize: 64,
    color: theme.palette.text.secondary,
    marginBottom: theme.spacing(2),
  },
}));
