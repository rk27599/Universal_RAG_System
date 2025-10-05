/**
 * Main App Component - Secure RAG System
 * Integrates all components with security-first architecture
 */

import React, { useState } from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
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

// Create Material-UI theme
const theme = createTheme({
  palette: {
    primary: {
      main: config.ui.primaryColor,
    },
    secondary: {
      main: config.ui.secondaryColor,
    },
    mode: config.ui.theme as 'light' | 'dark',
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          borderRadius: 8,
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 12,
        },
      },
    },
  },
});

// Main application pages
const Dashboard: React.FC = () => (
  <Box sx={{ p: 3 }}>
    <h1>Dashboard</h1>
    <p>Welcome to the Secure RAG System!</p>
  </Box>
);

const ChatPage: React.FC = () => {
  const [selectedConversationId, setSelectedConversationId] = useState<string | undefined>();

  return (
    <Box sx={{ height: '100%', display: 'flex' }}>
      {/* Conversation Sidebar */}
      <Box sx={{ width: 320, borderRight: 1, borderColor: 'divider' }}>
        <ConversationList
          onConversationSelect={setSelectedConversationId}
          selectedConversationId={selectedConversationId}
        />
      </Box>

      {/* Chat Interface */}
      <Box sx={{ flexGrow: 1 }}>
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
    <Box>
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
  <ModelSettings />
);

const SecurityPage: React.FC = () => (
  <Box sx={{ p: 3 }}>
    <h1>Security Dashboard</h1>
    <p>Security monitoring and validation tools will be implemented here.</p>
  </Box>
);

const App: React.FC = () => {
  const [currentPage, setCurrentPage] = useState('chat');

  const renderCurrentPage = () => {
    switch (currentPage) {
      case 'dashboard':
        return <Dashboard />;
      case 'chat':
        return <ChatPage />;
      case 'documents':
        return <DocumentsPage />;
      case 'settings':
        return <SettingsPage />;
      case 'security':
        return <SecurityPage />;
      default:
        return <ChatPage />;
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
