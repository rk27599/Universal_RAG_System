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
  TextField,
  Slider,
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
  const [folderPath, setFolderPath] = useState('');
  const [chunkSize, setChunkSize] = useState(2000); // Default 2000 characters

  const validateFile = useCallback((file: File): string | null => {
    // Check file size
    if (file.size > config.security.maxFileSize) {
      return `File too large. Maximum size: ${(config.security.maxFileSize / 1024 / 1024).toFixed(1)}MB`;
    }

    // Check file type - also accept by extension for .jsonl files and images
    const fileExtension = file.name.toLowerCase().split('.').pop();
    const allowedExtensions = ['txt', 'html', 'htm', 'md', 'pdf', 'doc', 'docx', 'json', 'jsonl', 'ndjson',
                              'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'webp'];

    const isValidByType = config.security.allowedFileTypes.includes(file.type);
    const isValidByExtension = fileExtension && allowedExtensions.includes(fileExtension);

    if (!isValidByType && !isValidByExtension) {
      return `Unsupported file type: ${file.type} (.${fileExtension})`;
    }

    return null;
  }, []);

  const showSnackbar = useCallback((message: string, severity: 'success' | 'error' | 'info' = 'info') => {
    setSnackbarMessage(message);
    setSnackbarSeverity(severity);
  }, []);

  const handleHtmlDocsUpload = async (file: File) => {
    const validationError = validateFile(file);
    if (validationError) {
      showSnackbar(validationError, 'error');
      return;
    }

    const uploadingFile: UploadingFile = {
      file,
      progress: 0,
      status: 'uploading',
    };

    setUploadingFiles(prev => [...prev, uploadingFile]);

    try {
      updateProgress(25, 'uploading');

      // Upload HTML documentation
      const response = await apiService.uploadHtmlDocumentation(file, {
        uploadId: Date.now().toString(),
        timestamp: new Date().toISOString(),
      });

      if (response.success) {
        updateProgress(50, 'processing');

        // Show discovery stats
        const stats = response.data.discoveryStats;
        if (stats) {
          showSnackbar(
            `📚 Found ${stats.total_files_discovered} HTML files! Processing ${stats.total_sections} sections...`,
            'info'
          );
        }

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
        await pollProcessingStatus(file, response.data.id);

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

    function updateProgress(progress: number, status: UploadingFile['status']) {
      setUploadingFiles(prev =>
        prev.map(f =>
          f.file === file ? { ...f, progress, status } : f
        )
      );
    }
  };

  const handleFolderUpload = async () => {
    if (!folderPath.trim()) {
      showSnackbar('Please enter a folder path', 'error');
      return;
    }

    // Create a pseudo-file for tracking
    const pseudoFile = new File([], folderPath.split(/[\\\/]/).pop() || 'Folder', { type: 'text/html' });

    const uploadingFile: UploadingFile = {
      file: pseudoFile,
      progress: 0,
      status: 'uploading',
    };

    setUploadingFiles(prev => [...prev, uploadingFile]);

    try {
      updateProgress(10, 'uploading');

      // Upload HTML folder
      const response = await apiService.uploadHtmlFolder(
        folderPath,
        {
          uploadId: Date.now().toString(),
          timestamp: new Date().toISOString(),
        },
        chunkSize
      );

      if (response.success) {
        updateProgress(30, 'processing');

        // Show discovery stats
        const stats = response.data.discoveryStats;
        if (stats) {
          showSnackbar(
            `🎉 Found ${stats.total_files_discovered} HTML files! Processed ${stats.total_files_processed} files with ${stats.total_sections} sections...`,
            'success'
          );
        }

        // Show embedding status
        if (response.data.embeddingsEnabled) {
          showSnackbar(`🎯 Processing with semantic embeddings for best search quality!`, 'info');
        } else {
          showSnackbar(`⚡ Processing with TF-IDF (fast mode - embeddings not available)`, 'info');
        }

        // Store embedding info
        setUploadingFiles(prev =>
          prev.map(f =>
            f.file === pseudoFile
              ? {
                  ...f,
                  embeddingsEnabled: response.data.embeddingsEnabled,
                  processingMethod: response.data.processingMethod
                } as UploadingFile
              : f
          )
        );

        // Poll for processing completion
        await pollProcessingStatus(pseudoFile, response.data.id);

        // Clear folder path on success
        setFolderPath('');

      } else {
        updateProgress(0, 'error');
        const error = response.message || 'Folder processing failed';
        setUploadingFiles(prev =>
          prev.map(f =>
            f.file === pseudoFile ? { ...f, error } : f
          )
        );

        if (onUploadError) {
          onUploadError(error);
        }

        showSnackbar(`Failed to process folder: ${error}`, 'error');
      }

    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.response?.data?.message || 'Folder processing failed';
      setUploadingFiles(prev =>
        prev.map(f =>
          f.file === pseudoFile
            ? { ...f, progress: 0, status: 'error', error: errorMessage }
            : f
        )
      );

      if (onUploadError) {
        onUploadError(errorMessage);
      }

      showSnackbar(`Error processing folder: ${errorMessage}`, 'error');
    }

    function updateProgress(progress: number, status: UploadingFile['status']) {
      setUploadingFiles(prev =>
        prev.map(f =>
          f.file === pseudoFile ? { ...f, progress, status } : f
        )
      );
    }
  };

  const pollProcessingStatus = useCallback(async (file: File, documentId: string) => {
    let processingComplete = false;
    let attempts = 0;
    const maxAttempts = 30; // 30 seconds timeout

    const updateProgress = (progress: number, status: UploadingFile['status']) => {
      setUploadingFiles(prev =>
        prev.map(f =>
          f.file === file ? { ...f, progress, status } : f
        )
      );
    };

    while (!processingComplete && attempts < maxAttempts) {
      await new Promise(resolve => setTimeout(resolve, 1000));

      try {
        const docResponse = await apiService.getDocument(documentId);
        if (docResponse.success) {
          const document = docResponse.data;
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

            showSnackbar(`Documentation "${file.name}" processed successfully!`, 'success');
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
  }, [onUploadComplete, onUploadError, showSnackbar]);

  const uploadFile = useCallback(async (file: File) => {
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
      const response = await apiService.uploadDocument(
        file,
        {
          uploadId,
          timestamp: new Date().toISOString(),
        },
        chunkSize
      );

      if (response.success) {
        updateProgress(50, 'processing');

        // Show embedding status
        if (response.data.embeddingsEnabled) {
          showSnackbar(`🎯 Processing "${file.name}" with semantic embeddings!`, 'info');
        } else {
          showSnackbar(`⚡ Processing "${file.name}" with TF-IDF (fast mode)`, 'info');
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
  }, [chunkSize, onUploadComplete, onUploadError, showSnackbar]);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    // Process all files in parallel for better UX
    const uploadPromises = acceptedFiles.map(async (file) => {
      const validationError = validateFile(file);
      if (validationError) {
        showSnackbar(validationError, 'error');
        return;
      }

      await uploadFile(file);
    });

    // Wait for all uploads to complete
    await Promise.all(uploadPromises);
  }, [uploadFile, validateFile, showSnackbar]);

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
      {/* File Type Information */}
      <Card sx={{ mb: 3 }}>
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
                <Chip size="small" label="PDF ✨" variant="outlined" color="primary" />
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

          <Typography variant="body2" color="primary" sx={{ mt: 1, fontWeight: 'medium' }}>
            📄 PDF Processing: Extracts text, code blocks, images, and preserves page numbers for accurate citations.
          </Typography>
        </CardContent>
      </Card>

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

        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
          Maximum file size: {(config.security.maxFileSize / 1024 / 1024).toFixed(1)}MB
        </Typography>

        <Typography variant="caption" color="primary" sx={{ display: 'block', fontWeight: 'bold' }}>
          ✨ NEW: Full PDF support with text & image extraction!
        </Typography>

        <Box sx={{ mt: 2 }}>
          <Button variant="contained" component="span" startIcon={<UploadIcon />}>
            Select Files
          </Button>
        </Box>
      </Paper>

      {/* Chunk Size Control for Regular Upload */}
      <Box sx={{ mt: 2, px: 2, py: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
        <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 'bold' }}>
          📏 Chunk Size Settings
        </Typography>
        <Typography variant="caption" sx={{ display: 'block', mb: 1, color: 'text.secondary' }}>
          Current: {chunkSize} characters
        </Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
          <Chip
            label="Small"
            size="small"
            onClick={() => setChunkSize(1000)}
            color={chunkSize === 1000 ? 'primary' : 'default'}
            variant={chunkSize === 1000 ? 'filled' : 'outlined'}
          />
          <Chip
            label="Medium"
            size="small"
            onClick={() => setChunkSize(2000)}
            color={chunkSize === 2000 ? 'primary' : 'default'}
            variant={chunkSize === 2000 ? 'filled' : 'outlined'}
          />
          <Chip
            label="Large"
            size="small"
            onClick={() => setChunkSize(4000)}
            color={chunkSize === 4000 ? 'primary' : 'default'}
            variant={chunkSize === 4000 ? 'filled' : 'outlined'}
          />
          <Chip
            label="XL"
            size="small"
            onClick={() => setChunkSize(8000)}
            color={chunkSize === 8000 ? 'primary' : 'default'}
            variant={chunkSize === 8000 ? 'filled' : 'outlined'}
          />
        </Box>
        <Slider
          value={chunkSize}
          onChange={(_, value) => setChunkSize(value as number)}
          min={500}
          max={10000}
          step={100}
          size="small"
          sx={{ mt: 0.5 }}
          valueLabelDisplay="auto"
        />
        <Typography variant="caption" sx={{ display: 'block', color: 'text.secondary', fontStyle: 'italic' }}>
          ℹ️ Larger chunks = better context preservation, fewer fragments
        </Typography>
      </Box>

      {/* Security Notice */}
      <Alert severity="info" sx={{ mt: 2 }}>
        🔒 <strong>Local Processing:</strong> All files are processed locally on your system.
        No data is sent to external services.
      </Alert>

      {/* HTML Documentation Upload Section */}
      <Card sx={{ mt: 3, border: '2px solid', borderColor: 'primary.light' }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            📚 HTML Documentation
          </Typography>

          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Process local HTML documentation files for semantic search
          </Typography>

          {/* Folder Path Input - Primary Option */}
          <Box sx={{ mb: 3 }}>
            <Typography variant="subtitle2" gutterBottom>
              📁 Folder Path (Recommended)
            </Typography>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <TextField
                fullWidth
                size="small"
                placeholder="C:\Program Files (x86)\Windows Kits\10\bin\10.0.26100.0\arm64\AccChecker"
                value={folderPath}
                onChange={(e) => setFolderPath(e.target.value)}
                helperText="Processes all .htm files in folder and subfolders"
              />
              <Button
                variant="contained"
                onClick={handleFolderUpload}
                disabled={!folderPath.trim()}
                startIcon={<UploadIcon />}
                sx={{ minWidth: 120 }}
              >
                Process
              </Button>
            </Box>

            {/* Chunk Size Control */}
            <Box sx={{ mt: 2, px: 1 }}>
              <Typography variant="caption" sx={{ display: 'block', mb: 0.5, color: 'text.secondary' }}>
                📏 Chunk Size: {chunkSize} characters
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Chip
                  label="Small"
                  size="small"
                  onClick={() => setChunkSize(1000)}
                  color={chunkSize === 1000 ? 'primary' : 'default'}
                  variant={chunkSize === 1000 ? 'filled' : 'outlined'}
                />
                <Chip
                  label="Medium"
                  size="small"
                  onClick={() => setChunkSize(2000)}
                  color={chunkSize === 2000 ? 'primary' : 'default'}
                  variant={chunkSize === 2000 ? 'filled' : 'outlined'}
                />
                <Chip
                  label="Large"
                  size="small"
                  onClick={() => setChunkSize(4000)}
                  color={chunkSize === 4000 ? 'primary' : 'default'}
                  variant={chunkSize === 4000 ? 'filled' : 'outlined'}
                />
                <Chip
                  label="XL"
                  size="small"
                  onClick={() => setChunkSize(8000)}
                  color={chunkSize === 8000 ? 'primary' : 'default'}
                  variant={chunkSize === 8000 ? 'filled' : 'outlined'}
                />
              </Box>
              <Slider
                value={chunkSize}
                onChange={(_, value) => setChunkSize(value as number)}
                min={500}
                max={10000}
                step={100}
                size="small"
                sx={{ mt: 1 }}
                valueLabelDisplay="auto"
              />
              <Typography variant="caption" sx={{ display: 'block', color: 'text.secondary', fontStyle: 'italic' }}>
                ℹ️ Larger chunks = better context, fewer fragments
              </Typography>
            </Box>
          </Box>

          {/* OR Divider */}
          <Box sx={{ display: 'flex', alignItems: 'center', my: 2 }}>
            <Box sx={{ flexGrow: 1, height: 1, bgcolor: 'divider' }} />
            <Typography variant="caption" sx={{ px: 2, color: 'text.secondary' }}>
              OR
            </Typography>
            <Box sx={{ flexGrow: 1, height: 1, bgcolor: 'divider' }} />
          </Box>

          {/* Single File Upload - Alternative Option */}
          <Box>
            <Typography variant="subtitle2" gutterBottom>
              📄 Single File
            </Typography>
            <input
              accept=".htm,.html"
              style={{ display: 'none' }}
              id="html-docs-upload"
              type="file"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) {
                  handleHtmlDocsUpload(file);
                }
              }}
            />
            <label htmlFor="html-docs-upload">
              <Button
                variant="outlined"
                component="span"
                startIcon={<UploadIcon />}
              >
                Upload .htm File
              </Button>
            </label>
            <Typography variant="caption" color="text.secondary" sx={{ ml: 2 }}>
              Upload home page to discover linked files
            </Typography>
          </Box>
        </CardContent>
      </Card>

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
                    secondaryTypographyProps={{ component: 'div' }}
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