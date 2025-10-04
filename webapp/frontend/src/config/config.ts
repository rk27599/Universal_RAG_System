/**
 * Frontend Configuration - Security-First Design
 * All connections must be localhost-only for data sovereignty
 */

export const config = {
  // API Configuration - LOCALHOST ONLY
  api: {
    baseUrl: process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000',
    timeout: 30000,
    retries: 3
  },

  // WebSocket Configuration - LOCALHOST ONLY (Socket.IO)
  websocket: {
    url: process.env.REACT_APP_WS_URL || 'http://127.0.0.1:8000',
    reconnectAttempts: 5,
    reconnectDelay: 1000
  },

  // Application Settings
  app: {
    name: 'Secure RAG System',
    version: '1.0.0',
    description: 'Local-only RAG system with complete data sovereignty'
  },

  // Security Settings
  security: {
    validateLocalhostOnly: true,
    maxFileSize: 50 * 1024 * 1024, // 50MB
    allowedFileTypes: [
      'text/plain',
      'text/html',
      'text/markdown',
      'application/pdf',
      'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'application/json',
      'application/jsonl',
      'application/x-ndjson'
    ]
  },

  // UI Configuration
  ui: {
    theme: 'light',
    primaryColor: '#1976d2',
    secondaryColor: '#dc004e',
    maxMessages: 1000,
    autoScrollThreshold: 100
  },

  // Model Configuration
  models: {
    defaultModel: 'mistral',
    availableModels: ['mistral', 'llama2', 'codellama'],
    maxTokens: 4096,
    temperature: 0.7
  }
};

// Security validation: Ensure all URLs are localhost
export const validateSecurityConfig = (): boolean => {
  const urls = [config.api.baseUrl, config.websocket.url];

  for (const url of urls) {
    if (!url.includes('localhost') && !url.includes('127.0.0.1')) {
      console.error('🚨 SECURITY VIOLATION: Non-localhost URL detected:', url);
      return false;
    }
  }

  return true;
};

// Initialize security validation
if (config.security.validateLocalhostOnly && !validateSecurityConfig()) {
  throw new Error('Security validation failed: Non-localhost configuration detected');
}

export default config;