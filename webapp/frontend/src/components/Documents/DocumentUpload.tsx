/**
 * Document Upload Component - Secure File Processing
 * Handles file uploads with security validation and progress tracking
 */

import React, { useState, useCallback } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  LinearProgress,
  Alert,
  Chip,
  IconButton,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ListItemSecondaryAction,
  Card,
  CardContent,
  Grid,
  Tooltip,
  Snackbar,
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  Description as FileIcon,
  Cancel as CancelIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material';
import { useDropzone } from 'react-dropzone';
import apiService, { Document } from '../../services/api';
import config from '../../config/config';

interface UploadingFile {
  file: File;
  progress: number;
  status: 'uploading' | 'processing' | 'completed' | 'error';
  error?: string;
  documentId?: string;
  embeddingsEnabled?: boolean;
  processingMethod?: string;
}

interface DocumentUploadProps {
  onUploadComplete?: (document: Document) => void;
  onUploadError?: (error: string) => void;
}

const DocumentUpload: React.FC<DocumentUploadProps> = ({
  onUploadComplete,
  onUploadError,
}) => {
  const [uploadingFiles, setUploadingFiles] = useState<UploadingFile[]>([]);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [snackbarSeverity, setSnackbarSeverity] = useState<'success' | 'error' | 'info'>('info');

  const validateFile = (file: File): string | null => {
    // Check file size
    if (file.size > config.security.maxFileSize) {
      return `File too large. Maximum size: ${(config.security.maxFileSize / 1024 / 1024).toFixed(1)}MB`;
    }

    // Check file type - also accept by extension for .jsonl files
    const fileExtension = file.name.toLowerCase().split('.').pop();
    const allowedExtensions = ['txt', 'html', 'htm', 'md', 'pdf', 'doc', 'docx', 'json', 'jsonl', 'ndjson'];

    const isValidByType = config.security.allowedFileTypes.includes(file.type);
    const isValidByExtension = fileExtension && allowedExtensions.includes(fileExtension);

    if (!isValidByType && !isValidByExtension) {
      return `Unsupported file type: ${file.type} (.${fileExtension})`;
    }

    return null;
  };

  const showSnackbar = (message: string, severity: 'success' | 'error' | 'info' = 'info') => {
    setSnackbarMessage(message);
    setSnackbarSeverity(severity);
  };

  const uploadFile = async (file: File) => {
    const uploadId = Date.now().toString();

    // Add to uploading files
    const uploadingFile: UploadingFile = {
      file,
      progress: 0,
      status: 'uploading',
    };

    setUploadingFiles(prev => [...prev, uploadingFile]);

    try {
      // Simulate progress for demo (replace with actual progress tracking)
      const updateProgress = (progress: number, status: UploadingFile['status']) => {
        setUploadingFiles(prev =>
          prev.map(f =>
            f.file === file ? { ...f, progress, status } : f
          )
        );
      };

      updateProgress(25, 'uploading');

      // Upload file
      const response = await apiService.uploadDocument(file, {
        uploadId,
        timestamp: new Date().toISOString(),
      });

      if (response.success) {
        updateProgress(50, 'processing');

        // Show embedding status
        if (response.data.embeddingsEnabled) {
          showSnackbar(`🎯 Processing with semantic embeddings for best search quality!`, 'info');
        } else {
          showSnackbar(`⚡ Processing with TF-IDF (fast mode - embeddings not available)`, 'info');
        }

        // Store embedding info
        setUploadingFiles(prev =>
          prev.map(f =>
            f.file === file
              ? {
                  ...f,
                  embeddingsEnabled: response.data.embeddingsEnabled,
                  processingMethod: response.data.processingMethod
                } as UploadingFile
              : f
          )
        );

        // Poll for processing completion
        let processingComplete = false;
        let attempts = 0;
        const maxAttempts = 30; // 30 seconds timeout

        while (!processingComplete && attempts < maxAttempts) {
          await new Promise(resolve => setTimeout(resolve, 1000));

          try {
            const docResponse = await apiService.getDocument(response.data.id);
            if (docResponse.success) {
              const document = docResponse.data;
              // Use server-side progress if available, otherwise estimate
              const serverProgress = document.progress || 0;
              const progress = serverProgress > 0 ? serverProgress : Math.min(90, 50 + (attempts * 2));
              updateProgress(progress, 'processing');

              if (document.status === 'completed') {
                updateProgress(100, 'completed');
                processingComplete = true;

                // Update with document ID
                setUploadingFiles(prev =>
                  prev.map(f =>
                    f.file === file
                      ? { ...f, documentId: document.id }
                      : f
                  )
                );

                if (onUploadComplete) {
                  onUploadComplete(document);
                }

                showSnackbar(`Document "${file.name}" processed successfully!`, 'success');
              } else if (document.status === 'failed') {
                updateProgress(0, 'error');
                const error = document.processingError || 'Processing failed';
                setUploadingFiles(prev =>
                  prev.map(f =>
                    f.file === file ? { ...f, error } : f
                  )
                );

                if (onUploadError) {
                  onUploadError(error);
                }

                showSnackbar(`Failed to process "${file.name}": ${error}`, 'error');
                break;
              }
            }
          } catch (error) {
            console.error('Error checking processing status:', error);
          }

          attempts++;
        }

        if (!processingComplete && attempts >= maxAttempts) {
          updateProgress(0, 'error');
          const error = 'Processing timeout';
          setUploadingFiles(prev =>
            prev.map(f =>
              f.file === file ? { ...f, error } : f
            )
          );

          showSnackbar(`Processing timeout for "${file.name}"`, 'error');
        }

      } else {
        updateProgress(0, 'error');
        const error = response.message || 'Upload failed';
        setUploadingFiles(prev =>
          prev.map(f =>
            f.file === file ? { ...f, error } : f
          )
        );

        if (onUploadError) {
          onUploadError(error);
        }

        showSnackbar(`Failed to upload "${file.name}": ${error}`, 'error');
      }

    } catch (error: any) {
      const errorMessage = error.response?.data?.message || 'Upload failed';
      setUploadingFiles(prev =>
        prev.map(f =>
          f.file === file
            ? { ...f, progress: 0, status: 'error', error: errorMessage }
            : f
        )
      );

      if (onUploadError) {
        onUploadError(errorMessage);
      }

      showSnackbar(`Error uploading "${file.name}": ${errorMessage}`, 'error');
    }
  };

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    for (const file of acceptedFiles) {
      const validationError = validateFile(file);
      if (validationError) {
        showSnackbar(validationError, 'error');
        continue;
      }

      await uploadFile(file);
    }
  }, []);

  const removeUploadingFile = (file: File) => {
    setUploadingFiles(prev => prev.filter(f => f.file !== file));
  };

  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop,
    accept: {
      'text/plain': ['.txt'],
      'text/html': ['.html'],
      'text/markdown': ['.md'],
      'application/pdf': ['.pdf'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'application/json': ['.json', '.jsonl'],
      'application/jsonl': ['.jsonl'],
      'application/x-ndjson': ['.jsonl', '.ndjson'],
    },
    maxSize: config.security.maxFileSize,
    multiple: true,
  });

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getStatusIcon = (status: UploadingFile['status']) => {
    switch (status) {
      case 'uploading':
      case 'processing':
        return <InfoIcon color="info" />;
      case 'completed':
        return <SuccessIcon color="success" />;
      case 'error':
        return <ErrorIcon color="error" />;
      default:
        return <FileIcon />;
    }
  };

  const getStatusColor = (status: UploadingFile['status']) => {
    switch (status) {
      case 'uploading':
      case 'processing':
        return 'info';
      case 'completed':
        return 'success';
      case 'error':
        return 'error';
      default:
        return 'default';
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Upload Area */}
      <Paper
        {...getRootProps()}
        sx={{
          p: 4,
          border: '2px dashed',
          borderColor: isDragActive
            ? 'primary.main'
            : isDragReject
            ? 'error.main'
            : 'grey.300',
          backgroundColor: isDragActive
            ? 'primary.light'
            : isDragReject
            ? 'error.light'
            : 'grey.50',
          cursor: 'pointer',
          textAlign: 'center',
          transition: 'all 0.2s ease-in-out',
          '&:hover': {
            borderColor: 'primary.main',
            backgroundColor: 'primary.light',
          },
        }}
      >
        <input {...getInputProps()} />

        <UploadIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />

        <Typography variant="h6" gutterBottom>
          {isDragActive
            ? 'Drop files here...'
            : isDragReject
            ? 'Some files are not supported'
            : 'Drag & drop files here, or click to select'}
        </Typography>

        <Typography variant="body2" color="text.secondary" gutterBottom>
          Supported formats: PDF, Word, HTML, Markdown, Text, JSON
        </Typography>

        <Typography variant="caption" color="text.secondary">
          Maximum file size: {(config.security.maxFileSize / 1024 / 1024).toFixed(1)}MB
        </Typography>

        <Box sx={{ mt: 2 }}>
          <Button variant="contained" component="span" startIcon={<UploadIcon />}>
            Select Files
          </Button>
        </Box>
      </Paper>

      {/* Security Notice */}
      <Alert severity="info" sx={{ mt: 2 }}>
        🔒 <strong>Local Processing:</strong> All files are processed locally on your system.
        No data is sent to external services.
      </Alert>

      {/* Uploading Files */}
      {uploadingFiles.length > 0 && (
        <Card sx={{ mt: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Upload Progress
            </Typography>

            <List>
              {uploadingFiles.map((uploadingFile) => (
                <ListItem key={uploadingFile.file.name} divider>
                  <ListItemIcon>
                    {getStatusIcon(uploadingFile.status)}
                  </ListItemIcon>

                  <ListItemText
                    primary={uploadingFile.file.name}
                    secondary={
                      <Box>
                        <Typography variant="caption" component="div">
                          {formatFileSize(uploadingFile.file.size)} • {uploadingFile.file.type}
                        </Typography>

                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 1 }}>
                          <LinearProgress
                            variant="determinate"
                            value={uploadingFile.progress}
                            sx={{ flexGrow: 1, height: 6, borderRadius: 3 }}
                            color={getStatusColor(uploadingFile.status) as any}
                          />
                          <Box sx={{ minWidth: 80, textAlign: 'right' }}>
                            <Chip
                              size="small"
                              label={`${Math.round(uploadingFile.progress)}%`}
                              color={getStatusColor(uploadingFile.status) as any}
                              variant="outlined"
                            />
                          </Box>
                        </Box>

                        {/* Show embedding status badge */}
                        {uploadingFile.embeddingsEnabled !== undefined && (
                          <Box sx={{ mt: 0.5 }}>
                            <Chip
                              size="small"
                              label={uploadingFile.embeddingsEnabled ? '🎯 Semantic Embeddings' : '⚡ TF-IDF Fallback'}
                              color={uploadingFile.embeddingsEnabled ? 'success' : 'warning'}
                              variant="filled"
                              sx={{ fontSize: '0.7rem', height: 20 }}
                            />
                          </Box>
                        )}

                        {uploadingFile.error && (
                          <Typography variant="caption" color="error" component="div">
                            {uploadingFile.error}
                          </Typography>
                        )}
                      </Box>
                    }
                  />

                  <ListItemSecondaryAction>
                    <Tooltip title="Remove">
                      <IconButton
                        edge="end"
                        onClick={() => removeUploadingFile(uploadingFile.file)}
                        size="small"
                      >
                        {uploadingFile.status === 'completed' ? <DeleteIcon /> : <CancelIcon />}
                      </IconButton>
                    </Tooltip>
                  </ListItemSecondaryAction>
                </ListItem>
              ))}
            </List>
          </CardContent>
        </Card>
      )}

      {/* File Type Information */}
      <Card sx={{ mt: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Supported File Types
          </Typography>

          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' }, gap: 2 }}>
            <Box>
              <Typography variant="subtitle2" gutterBottom>
                Documents
              </Typography>
              <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                <Chip size="small" label="PDF" variant="outlined" />
                <Chip size="small" label="Word (.doc, .docx)" variant="outlined" />
                <Chip size="small" label="Text (.txt)" variant="outlined" />
              </Box>
            </Box>

            <Box>
              <Typography variant="subtitle2" gutterBottom>
                Web & Data
              </Typography>
              <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                <Chip size="small" label="HTML" variant="outlined" />
                <Chip size="small" label="Markdown (.md)" variant="outlined" />
                <Chip size="small" label="JSON (.json, .jsonl)" variant="outlined" />
              </Box>
            </Box>
          </Box>

          <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
            Files are automatically processed and indexed for search and RAG functionality.
            Large documents are intelligently chunked to optimize retrieval performance.
          </Typography>
        </CardContent>
      </Card>

      {/* Snackbar for notifications */}
      <Snackbar
        open={!!snackbarMessage}
        autoHideDuration={6000}
        onClose={() => setSnackbarMessage('')}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert
          onClose={() => setSnackbarMessage('')}
          severity={snackbarSeverity}
          sx={{ width: '100%' }}
        >
          {snackbarMessage}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default DocumentUpload;