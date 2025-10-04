/**
 * Authentication Context - Security-First User Management
 * Provides secure authentication state management
 */

import React, { createContext, useContext, useReducer, useEffect, ReactNode } from 'react';
import apiService, { User } from '../services/api';

interface AuthState {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  error: string | null;
}

interface AuthContextType extends AuthState {
  login: (username: string, password: string) => Promise<boolean>;
  register: (userData: RegisterData) => Promise<boolean>;
  logout: () => void;
  clearError: () => void;
}

interface RegisterData {
  username: string;
  email: string;
  password: string;
  fullName: string;
}

type AuthAction =
  | { type: 'AUTH_START' }
  | { type: 'AUTH_SUCCESS'; payload: User }
  | { type: 'AUTH_FAILURE'; payload: string }
  | { type: 'AUTH_LOGOUT' }
  | { type: 'CLEAR_ERROR' };

const initialState: AuthState = {
  user: null,
  isLoading: false,
  isAuthenticated: false,
  error: null,
};

const authReducer = (state: AuthState, action: AuthAction): AuthState => {
  switch (action.type) {
    case 'AUTH_START':
      return {
        ...state,
        isLoading: true,
        error: null,
      };

    case 'AUTH_SUCCESS':
      return {
        ...state,
        user: action.payload,
        isLoading: false,
        isAuthenticated: true,
        error: null,
      };

    case 'AUTH_FAILURE':
      return {
        ...state,
        user: null,
        isLoading: false,
        isAuthenticated: false,
        error: action.payload,
      };

    case 'AUTH_LOGOUT':
      return {
        ...state,
        user: null,
        isAuthenticated: false,
        error: null,
      };

    case 'CLEAR_ERROR':
      return {
        ...state,
        error: null,
      };

    default:
      return state;
  }
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [state, dispatch] = useReducer(authReducer, initialState);

  // Check for existing auth token on mount
  useEffect(() => {
    const checkAuthStatus = async (retries = 3, delay = 1000) => {
      const token = localStorage.getItem('authToken');
      if (token) {
        dispatch({ type: 'AUTH_START' });

        for (let attempt = 0; attempt < retries; attempt++) {
          try {
            // Add per-request timeout
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 5000);

            const response = await apiService.getCurrentUser();
            clearTimeout(timeoutId);

            if (response.success && response.data) {
              dispatch({ type: 'AUTH_SUCCESS', payload: response.data });
              return; // Success - exit retry loop
            } else {
              localStorage.removeItem('authToken');
              dispatch({ type: 'AUTH_FAILURE', payload: 'Invalid session' });
              return;
            }
          } catch (error: any) {
            console.warn(`Auth check attempt ${attempt + 1}/${retries} failed:`, error.message);

            if (attempt < retries - 1) {
              // Wait before retrying (exponential backoff)
              await new Promise(resolve => setTimeout(resolve, delay * (attempt + 1)));
            } else {
              // Final attempt failed
              console.error('Auth check failed after all retries');
              localStorage.removeItem('authToken');
              dispatch({
                type: 'AUTH_FAILURE',
                payload: 'Cannot connect to server - please check if backend is running'
              });
            }
          }
        }
      }
    };

    checkAuthStatus();
  }, []);

  // Listen for auth logout events
  useEffect(() => {
    const handleAuthLogout = () => {
      dispatch({ type: 'AUTH_LOGOUT' });
    };

    window.addEventListener('auth:logout', handleAuthLogout);
    return () => window.removeEventListener('auth:logout', handleAuthLogout);
  }, []);

  const login = async (username: string, password: string): Promise<boolean> => {
    dispatch({ type: 'AUTH_START' });

    try {
      const response = await apiService.login(username, password);

      if (response.success && response.data) {
        const { token, user } = response.data;
        apiService.setAuthToken(token);
        dispatch({ type: 'AUTH_SUCCESS', payload: user });
        return true;
      } else {
        dispatch({ type: 'AUTH_FAILURE', payload: response.message || 'Login failed' });
        return false;
      }
    } catch (error: any) {
      const errorMessage = error.response?.data?.message || 'Login failed. Please try again.';
      dispatch({ type: 'AUTH_FAILURE', payload: errorMessage });
      return false;
    }
  };

  const register = async (userData: RegisterData): Promise<boolean> => {
    dispatch({ type: 'AUTH_START' });

    try {
      const response = await apiService.register(userData);

      if (response.success && response.data) {
        // After successful registration, attempt to login
        const loginSuccess = await login(userData.username, userData.password);
        return loginSuccess;
      } else {
        dispatch({ type: 'AUTH_FAILURE', payload: response.message || 'Registration failed' });
        return false;
      }
    } catch (error: any) {
      const errorMessage = error.response?.data?.message || 'Registration failed. Please try again.';
      dispatch({ type: 'AUTH_FAILURE', payload: errorMessage });
      return false;
    }
  };

  const logout = async (): Promise<void> => {
    try {
      await apiService.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      apiService.clearAuthToken();
      dispatch({ type: 'AUTH_LOGOUT' });
    }
  };

  const clearError = (): void => {
    dispatch({ type: 'CLEAR_ERROR' });
  };

  const contextValue: AuthContextType = {
    ...state,
    login,
    register,
    logout,
    clearError,
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
};

export default AuthContext;