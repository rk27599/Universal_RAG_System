/**
 * Auth Wrapper Component - Authentication Flow Management
 * Handles login/register switching and protected route access
 */

import React, { useState } from 'react';
import { Box, Fade } from '@mui/material';
import { useAuth } from '../../contexts/AuthContext';
import LoginForm from './LoginForm';
import RegisterForm from './RegisterForm';
import AppLayout from '../Layout/AppLayout';

interface AuthWrapperProps {
  children: React.ReactNode;
}

const AuthWrapper: React.FC<AuthWrapperProps> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login');

  // Show loading state while checking authentication
  if (isLoading) {
    return (
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        }}
      >
        <Box sx={{ textAlign: 'center' }}>
          <Box
            sx={{
              width: 60,
              height: 60,
              border: '4px solid rgba(255,255,255,0.3)',
              borderTop: '4px solid white',
              borderRadius: '50%',
              animation: 'spin 1s linear infinite',
              mx: 'auto',
              mb: 2,
              '@keyframes spin': {
                '0%': { transform: 'rotate(0deg)' },
                '100%': { transform: 'rotate(360deg)' },
              },
            }}
          />
          <Box sx={{ color: 'white', fontSize: '1.2rem', fontWeight: 'bold' }}>
            Secure RAG System
          </Box>
          <Box sx={{ color: 'rgba(255,255,255,0.8)', fontSize: '0.9rem', mt: 1 }}>
            Initializing secure session...
          </Box>
        </Box>
      </Box>
    );
  }

  // If authenticated, show the protected content
  if (isAuthenticated) {
    return <>{children}</>;
  }

  // If not authenticated, show the authentication forms
  return (
    <Fade in timeout={500}>
      <Box>
        {authMode === 'login' ? (
          <LoginForm onSwitchToRegister={() => setAuthMode('register')} />
        ) : (
          <RegisterForm onSwitchToLogin={() => setAuthMode('login')} />
        )}
      </Box>
    </Fade>
  );
};

export default AuthWrapper;