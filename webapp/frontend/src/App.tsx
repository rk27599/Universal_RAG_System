/**
 * Main App Component - Secure RAG System
 * Integrates all components with security-first architecture
 * Enhanced with dark mode support and design system
 */

import React, { useState, useMemo } from 'react';
import { ThemeProvider, createTheme, PaletteMode } from '@mui/material/styles';
import { CssBaseline, Box } from '@mui/material';
import { AuthProvider } from './contexts/AuthContext';
import { ChatProvider } from './contexts/ChatContext';
import AuthWrapper from './components/Auth/AuthWrapper';
import AppLayout from './components/Layout/AppLayout';
import ChatInterface from './components/Chat/ChatInterface';
import ConversationList from './components/Chat/ConversationList';
import DocumentUpload from './components/Documents/DocumentUpload';
import DocumentList from './components/Documents/DocumentList';
import ModelSettings from './components/Settings/ModelSettings';
import config from './config/config';
import { usePersistedState } from './hooks/usePersistedState';
import { typography, borderRadius } from './theme/tokens';

// Enhanced theme creation function
const createAppTheme = (mode: PaletteMode) => createTheme({
  palette: {
    mode,
    primary: {
      main: config.ui.primaryColor,
      light: mode === 'dark' ? '#42a5f5' : '#64b5f6',
      dark: mode === 'dark' ? '#1565c0' : '#1976d2',
    },
    secondary: {
      main: config.ui.secondaryColor,
      light: mode === 'dark' ? '#f06292' : '#f48fb1',
      dark: mode === 'dark' ? '#c2185b' : '#d32f2f',
    },
    background: {
      default: mode === 'dark' ? '#121212' : '#fafafa',
      paper: mode === 'dark' ? '#1e1e1e' : '#ffffff',
    },
    text: {
      primary: mode === 'dark' ? '#ffffff' : '#000000',
      secondary: mode === 'dark' ? 'rgba(255, 255, 255, 0.7)' : 'rgba(0, 0, 0, 0.6)',
    },
    divider: mode === 'dark' ? 'rgba(255, 255, 255, 0.12)' : 'rgba(0, 0, 0, 0.12)',
    success: {
      main: mode === 'dark' ? '#66bb6a' : '#4caf50',
    },
    warning: {
      main: mode === 'dark' ? '#ffa726' : '#ff9800',
    },
    error: {
      main: mode === 'dark' ? '#f44336' : '#d32f2f',
    },
    info: {
      main: mode === 'dark' ? '#29b6f6' : '#0288d1',
    },
  },
  typography: {
    fontFamily: typography.fontFamily.sans,
    fontSize: 14,
    h1: { fontWeight: typography.fontWeight.bold },
    h2: { fontWeight: typography.fontWeight.bold },
    h3: { fontWeight: typography.fontWeight.semibold },
    h4: { fontWeight: typography.fontWeight.semibold },
    h5: { fontWeight: typography.fontWeight.medium },
    h6: { fontWeight: typography.fontWeight.medium },
  },
  shape: {
    borderRadius: borderRadius.md,
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          borderRadius: borderRadius.md,
          fontWeight: typography.fontWeight.medium,
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: borderRadius.lg,
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none', // Remove MUI default gradient in dark mode
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: borderRadius.sm,
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: borderRadius.md,
          },
        },
      },
    },
  },
});

// Main application pages
const Dashboard: React.FC = () => (
  <Box sx={{ height: '100%', overflow: 'auto', p: 3 }}>
    <h1>Dashboard</h1>
    <p>Welcome to the Local RAG System by Rohan !</p>
  </Box>
);

const ChatPage: React.FC<{ drawerOpen?: boolean }> = ({ drawerOpen = true }) => {
  const [selectedConversationId, setSelectedConversationId] = useState<string | undefined>();

  return (
    <Box sx={{ height: '100%', display: 'flex' }}>
      {/* Conversation Sidebar */}
      <Box
        sx={{
          width: 320,
          height: '100%',
          borderRight: 1,
          borderColor: 'divider',
          flexShrink: 0,
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        <ConversationList
          onConversationSelect={setSelectedConversationId}
          selectedConversationId={selectedConversationId}
          drawerOpen={drawerOpen}
        />
      </Box>

      {/* Chat Interface */}
      <Box
        sx={{
          flexGrow: 1,
          height: '100%',
          width: 0, // Force flex to calculate width
          overflow: 'hidden',
        }}
      >
        <ChatInterface conversationId={selectedConversationId} />
      </Box>
    </Box>
  );
};

const DocumentsPage: React.FC = () => {
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  const handleUploadComplete = () => {
    setRefreshTrigger(prev => prev + 1);
  };

  return (
    <Box sx={{ height: '100%', overflow: 'auto' }}>
      {/* Upload Section */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <DocumentUpload onUploadComplete={handleUploadComplete} />
      </Box>

      {/* Document List */}
      <Box>
        <DocumentList refreshTrigger={refreshTrigger} />
      </Box>
    </Box>
  );
};

const SettingsPage: React.FC = () => (
  <Box sx={{ height: '100%', overflow: 'auto' }}>
    <ModelSettings />
  </Box>
);

const SecurityPage: React.FC = () => (
  <Box sx={{ height: '100%', overflow: 'auto', p: 3 }}>
    <h1>Security Dashboard</h1>
    <p>Security monitoring and validation tools will be implemented here.</p>
  </Box>
);

const App: React.FC = () => {
  const [currentPage, setCurrentPage] = useState('chat');
  const [desktopDrawerOpen, setDesktopDrawerOpen] = useState(true);

  // Dark mode state with persistence
  const [darkMode, setDarkMode] = usePersistedState<boolean>('darkMode', false);

  // Memoize theme to prevent recreation on every render
  const theme = useMemo(
    () => createAppTheme(darkMode ? 'dark' : 'light'),
    [darkMode]
  );

  const renderCurrentPage = () => {
    switch (currentPage) {
      case 'dashboard':
        return <Dashboard />;
      case 'chat':
        return <ChatPage drawerOpen={desktopDrawerOpen} />;
      case 'documents':
        return <DocumentsPage />;
      case 'settings':
        return <SettingsPage />;
      case 'security':
        return <SecurityPage />;
      default:
        return <ChatPage drawerOpen={desktopDrawerOpen} />;
    }
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AuthProvider>
        <ChatProvider>
          <AuthWrapper>
            <AppLayout
              currentPage={currentPage}
              onPageChange={setCurrentPage}
              desktopDrawerOpen={desktopDrawerOpen}
              onDesktopDrawerChange={setDesktopDrawerOpen}
              darkMode={darkMode}
              onDarkModeToggle={() => setDarkMode(!darkMode)}
            >
              {renderCurrentPage()}
            </AppLayout>
          </AuthWrapper>
        </ChatProvider>
      </AuthProvider>
    </ThemeProvider>
  );
};

export default App;
