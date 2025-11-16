/**
 * API Service - Security-First HTTP Client
 * Handles all communication with the FastAPI backend
 */

import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import config from '../config/config';

export interface ApiResponse<T = any> {
  data: T;
  message?: string;
  success: boolean;
}

export interface DocumentSource {
  documentId: number;
  documentTitle: string;
  section: string;
  similarity: number;
  chunkId: number;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  metadata?: {
    model?: string;
    responseTime?: number;
    tokenCount?: number;
    similarity?: number;
    rating?: number;
    sources?: DocumentSource[];
  };
}

export interface Document {
  id: string;
  title: string;
  filename: string;
  size: number;
  uploadedAt: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress?: number;
  chunksCount?: number;
  processingTime?: number;
  processingError?: string;
  embeddingsEnabled?: boolean;
  processingMethod?: string;
  sourceType?: string;
  discoveryStats?: {
    discoveredFiles: string[];
    totalFiles: number;
  };
}

export interface User {
  id: string;
  username: string;
  email: string;
  fullName: string;
  isAdmin: boolean;
  createdAt: string;
}

export interface Conversation {
  id: string;
  title: string;
  messageCount: number;
  lastActivity: string;
  isActive: boolean;
  modelName: string;
}

class ApiService {
  private client: AxiosInstance;
  private authToken: string | null = null;

  constructor() {
    this.client = axios.create({
      baseURL: config.api.baseUrl,
      timeout: config.api.timeout,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors(): void {
    // Request interceptor for auth token
    this.client.interceptors.request.use(
      (config) => {
        if (this.authToken) {
          config.headers.Authorization = `Bearer ${this.authToken}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          this.handleAuthError();
        }
        return Promise.reject(error);
      }
    );
  }

  private handleAuthError(): void {
    this.authToken = null;
    localStorage.removeItem('authToken');
    // Redirect to login or emit event
    window.dispatchEvent(new CustomEvent('auth:logout'));
  }

  setAuthToken(token: string): void {
    this.authToken = token;
    localStorage.setItem('authToken', token);
  }

  clearAuthToken(): void {
    this.authToken = null;
    localStorage.removeItem('authToken');
  }

  // Authentication endpoints
  async login(username: string, password: string): Promise<ApiResponse<{ token: string; user: User }>> {
    const response = await this.client.post('/api/auth/login', { username, password });
    return response.data;
  }

  async register(userData: {
    username: string;
    email: string;
    password: string;
    fullName: string;
  }): Promise<ApiResponse<User>> {
    const response = await this.client.post('/api/auth/register', userData);
    return response.data;
  }

  async getCurrentUser(): Promise<ApiResponse<User>> {
    const response = await this.client.get('/api/auth/me');
    return response.data;
  }

  async logout(): Promise<ApiResponse> {
    const response = await this.client.post('/api/auth/logout');
    this.clearAuthToken();
    return response.data;
  }

  // Document management
  async uploadDocument(file: File, metadata?: any, chunkSize?: number): Promise<ApiResponse<Document>> {
    const formData = new FormData();
    formData.append('file', file);
    if (metadata) {
      formData.append('metadata', JSON.stringify(metadata));
    }
    formData.append('chunk_size', String(chunkSize || 2000));

    const response = await this.client.post('/api/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  async uploadHtmlDocumentation(file: File, metadata?: any): Promise<ApiResponse<Document & { discoveryStats?: any }>> {
    const formData = new FormData();
    formData.append('file', file);
    if (metadata) {
      formData.append('metadata', JSON.stringify(metadata));
    }

    const response = await this.client.post('/api/documents/upload-html-docs', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  async uploadHtmlFolder(folderPath: string, metadata?: any, chunkSize?: number): Promise<ApiResponse<Document & { discoveryStats?: any }>> {
    const response = await this.client.post('/api/documents/upload-html-folder', {
      folder_path: folderPath,
      metadata,
      chunk_size: chunkSize || 2000
    });
    return response.data;
  }

  async getDocuments(): Promise<ApiResponse<Document[]>> {
    const response = await this.client.get('/api/documents');
    return response.data;
  }

  async getDocument(id: string): Promise<ApiResponse<Document>> {
    const response = await this.client.get(`/api/documents/${id}`);
    return response.data;
  }

  async deleteDocument(id: string): Promise<ApiResponse> {
    const response = await this.client.delete(`/api/documents/${id}`);
    return response.data;
  }

  async exportDocumentChunks(id: string): Promise<ApiResponse<any>> {
    const response = await this.client.get(`/api/documents/${id}/export-chunks`);
    return response.data;
  }

  async searchDocuments(query: string, filters?: any): Promise<ApiResponse<any[]>> {
    const response = await this.client.post('/api/documents/search', { query, filters });
    return response.data;
  }

  // Chat and conversation management
  async getConversations(): Promise<ApiResponse<Conversation[]>> {
    const response = await this.client.get('/api/chat/conversations');
    return response.data;
  }

  async createConversation(title?: string): Promise<ApiResponse<Conversation>> {
    const response = await this.client.post('/api/chat/conversations', { title });
    return response.data;
  }

  async getConversation(
    id: string,
    limit: number = 10,
    offset: number = 0
  ): Promise<ApiResponse<{ conversation: Conversation; messages: ChatMessage[]; pagination: { total: number; limit: number; offset: number; hasMore: boolean } }>> {
    const response = await this.client.get(`/api/chat/conversations/${id}`, {
      params: { limit, offset }
    });
    return response.data;
  }

  async deleteConversation(id: string): Promise<ApiResponse> {
    const response = await this.client.delete(`/api/chat/conversations/${id}`);
    return response.data;
  }

  // Chat messaging
  async sendMessage(
    conversationId: string,
    message: string,
    options?: {
      model?: string;
      temperature?: number;
      maxTokens?: number;
      useRAG?: boolean;
      documentIds?: string[];
    }
  ): Promise<ApiResponse<ChatMessage>> {
    const response = await this.client.post(`/api/chat/message`, {
      conversationId,
      content: message,
      ...options,
    });
    return response.data;
  }

  async regenerateMessage(conversationId: string, messageId: string): Promise<ApiResponse<ChatMessage>> {
    const response = await this.client.post(`/api/chat/conversations/${conversationId}/regenerate/${messageId}`);
    return response.data;
  }

  async rateMessage(messageId: string, rating: number, feedback?: string): Promise<ApiResponse> {
    const response = await this.client.post(`/api/chat/messages/${messageId}/rate`, { rating, feedback });
    return response.data;
  }

  // Model management
  async getAvailableModels(): Promise<ApiResponse<string[]>> {
    const response = await this.client.get('/api/models');
    return response.data;
  }

  async getModelInfo(modelName: string): Promise<ApiResponse<any>> {
    const response = await this.client.get(`/api/models/${modelName}`);
    return response.data;
  }

  // System information
  async getSystemStatus(): Promise<ApiResponse<{
    ollama: { status: string; models: string[] };
    database: { status: string; connections: number };
    security: { score: number; violations: number };
  }>> {
    const response = await this.client.get('/api/system/status');
    return response.data;
  }

  async getSecurityReport(): Promise<ApiResponse<any>> {
    const response = await this.client.get('/api/system/security');
    return response.data;
  }

  // Settings
  async getUserSettings(): Promise<ApiResponse<any>> {
    const response = await this.client.get('/api/settings');
    return response.data;
  }

  async updateUserSettings(settings: any): Promise<ApiResponse<any>> {
    const response = await this.client.put('/api/settings', settings);
    return response.data;
  }

  async resetUserSettings(): Promise<ApiResponse<any>> {
    const response = await this.client.post('/api/settings/reset');
    return response.data;
  }
}

// Create singleton instance
const apiService = new ApiService();

// Initialize auth token from localStorage
const savedToken = localStorage.getItem('authToken');
if (savedToken) {
  apiService.setAuthToken(savedToken);
}

export default apiService;