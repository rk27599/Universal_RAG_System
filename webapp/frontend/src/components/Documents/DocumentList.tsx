/**
 * Document List Component - Document Management Interface
 * Displays uploaded documents with search, filtering, and management capabilities
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  InputAdornment,
  IconButton,
  Button,
  Chip,
  Grid,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  CircularProgress,
  Tooltip,
  LinearProgress,
} from '@mui/material';
import {
  Search as SearchIcon,
  FilterList as FilterIcon,
  MoreVert as MoreVertIcon,
  Download as DownloadIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
  Description as DocumentIcon,
  PictureAsPdf as PdfIcon,
  InsertDriveFile as FileIcon,
  Code as HtmlIcon,
} from '@mui/icons-material';
import apiService, { Document } from '../../services/api';
import { useChat } from '../../contexts/ChatContext';

interface DocumentListProps {
  onDocumentSelect?: (document: Document) => void;
  refreshTrigger?: number;
}

const DocumentList: React.FC<DocumentListProps> = ({
  onDocumentSelect,
  refreshTrigger,
}) => {
  const { documentProgress } = useChat();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [filteredDocuments, setFilteredDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'completed' | 'processing' | 'failed'>('all');
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null);
  const [menuAnchor, setMenuAnchor] = useState<null | HTMLElement>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [documentToDelete, setDocumentToDelete] = useState<Document | null>(null);

  // Local progress state for API polling fallback (merged with WebSocket progress)
  const [localProgress, setLocalProgress] = useState<Record<number, { stage: string; progress: number }>>({});

  // Load documents
  const loadDocuments = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await apiService.getDocuments();
      if (response.success) {
        setDocuments(response.data);
      } else {
        setError(response.message || 'Failed to load documents');
      }
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to load documents');
    } finally {
      setLoading(false);
    }
  };

  // Initial load and refresh on trigger
  useEffect(() => {
    loadDocuments();
  }, [refreshTrigger]);

  // Filter documents based on search and status
  useEffect(() => {
    let filtered = documents;

    // Apply search filter
    if (searchQuery) {
      filtered = filtered.filter(doc =>
        doc.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        doc.filename.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    // Apply status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter(doc => doc.status === statusFilter);
    }

    setFilteredDocuments(filtered);
  }, [documents, searchQuery, statusFilter]);

  // Poll progress for processing documents (fallback when WebSocket state lost after refresh)
  useEffect(() => {
    const processingDocs = documents.filter(doc => doc.status === 'processing');

    if (processingDocs.length === 0) {
      return;
    }

    // Initial fetch for all processing documents
    const fetchInitialProgress = async () => {
      for (const doc of processingDocs) {
        try {
          const response = await apiService.getDocument(doc.id);
          if (response.success && response.data.progress !== undefined) {
            const docId = parseInt(doc.id, 10);
            const progressValue = response.data.progress ?? 0;
            setLocalProgress(prev => ({
              ...prev,
              [docId]: {
                stage: getStageFromProgress(progressValue),
                progress: progressValue
              }
            }));
          }
        } catch (error) {
          console.error(`Failed to fetch progress for document ${doc.id}:`, error);
        }
      }
    };

    fetchInitialProgress();

    // Poll every 2 seconds
    const intervalId = setInterval(async () => {
      for (const doc of processingDocs) {
        try {
          const response = await apiService.getDocument(doc.id);
          if (response.success) {
            const docId = parseInt(doc.id, 10);

            if (response.data.status === 'completed' || response.data.status === 'failed') {
              // Remove from local progress when done
              setLocalProgress(prev => {
                const updated = { ...prev };
                delete updated[docId];
                return updated;
              });

              // Refresh document list to update status
              loadDocuments();
            } else if (response.data.progress !== undefined) {
              // Update progress
              const progressValue = response.data.progress ?? 0;
              setLocalProgress(prev => ({
                ...prev,
                [docId]: {
                  stage: getStageFromProgress(progressValue),
                  progress: progressValue
                }
              }));
            }
          }
        } catch (error) {
          console.error(`Failed to poll progress for document ${doc.id}:`, error);
        }
      }
    }, 2000);

    return () => clearInterval(intervalId);
  }, [documents]);

  // Helper function to derive stage from progress percentage
  const getStageFromProgress = (progress: number): string => {
    if (progress < 5) return 'Starting PDF processing';
    if (progress < 40) return 'Extracting pages';
    if (progress < 60) return 'Extracting tables';
    if (progress < 80) return 'Extracting images';
    if (progress < 90) return 'Creating chunks';
    if (progress < 98) return 'Generating embeddings';
    return 'Building index';
  };

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, document: Document) => {
    event.stopPropagation();
    setMenuAnchor(event.currentTarget);
    setSelectedDocument(document);
  };

  const handleMenuClose = () => {
    setMenuAnchor(null);
    setSelectedDocument(null);
  };

  const handleDeleteClick = (document: Document) => {
    setDocumentToDelete(document);
    setDeleteDialogOpen(true);
    handleMenuClose();
  };

  const handleDeleteConfirm = async () => {
    if (!documentToDelete) return;

    try {
      const response = await apiService.deleteDocument(documentToDelete.id);
      if (response.success) {
        setDocuments(prev => prev.filter(doc => doc.id !== documentToDelete.id));
        setDeleteDialogOpen(false);
        setDocumentToDelete(null);
      } else {
        setError(response.message || 'Failed to delete document');
      }
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to delete document');
    }
  };

  const getFileIcon = (filename: string, status: string) => {
    const extension = filename.toLowerCase().split('.').pop();

    if (status === 'failed') {
      return <FileIcon color="error" />;
    }

    switch (extension) {
      case 'pdf':
        return <PdfIcon color="error" />;
      case 'html':
      case 'htm':
        return <HtmlIcon color="info" />;
      case 'doc':
      case 'docx':
        return <DocumentIcon color="primary" />;
      default:
        return <FileIcon color="action" />;
    }
  };

  const getStatusChip = (status: string) => {
    const config = {
      pending: { label: 'Pending', color: 'default' as const },
      processing: { label: 'Processing', color: 'warning' as const },
      completed: { label: 'Completed', color: 'success' as const },
      failed: { label: 'Failed', color: 'error' as const },
    };

    const { label, color } = config[status as keyof typeof config] || config.pending;

    return (
      <Chip
        size="small"
        label={label}
        color={color}
        variant={status === 'completed' ? 'filled' : 'outlined'}
      />
    );
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 200 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h5" gutterBottom>
          Documents
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Manage your uploaded documents and view processing status
        </Typography>
      </Box>

      {/* Search and Filters */}
      <Box sx={{ mb: 3, display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
        <TextField
          size="small"
          placeholder="Search documents..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon />
              </InputAdornment>
            ),
          }}
          sx={{ minWidth: 300 }}
        />

        <Box sx={{ display: 'flex', gap: 1 }}>
          <Chip
            label="All"
            onClick={() => setStatusFilter('all')}
            color={statusFilter === 'all' ? 'primary' : 'default'}
            variant={statusFilter === 'all' ? 'filled' : 'outlined'}
          />
          <Chip
            label="Completed"
            onClick={() => setStatusFilter('completed')}
            color={statusFilter === 'completed' ? 'primary' : 'default'}
            variant={statusFilter === 'completed' ? 'filled' : 'outlined'}
          />
          <Chip
            label="Processing"
            onClick={() => setStatusFilter('processing')}
            color={statusFilter === 'processing' ? 'primary' : 'default'}
            variant={statusFilter === 'processing' ? 'filled' : 'outlined'}
          />
          <Chip
            label="Failed"
            onClick={() => setStatusFilter('failed')}
            color={statusFilter === 'failed' ? 'primary' : 'default'}
            variant={statusFilter === 'failed' ? 'filled' : 'outlined'}
          />
        </Box>
      </Box>

      {/* Error Display */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Documents Grid */}
      {filteredDocuments.length === 0 ? (
        <Box sx={{ textAlign: 'center', py: 8 }}>
          <DocumentIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" color="text.secondary" gutterBottom>
            {searchQuery ? 'No documents found' : 'No documents uploaded'}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {searchQuery
              ? 'Try adjusting your search terms or filters'
              : 'Upload your first document to get started'}
          </Typography>
        </Box>
      ) : (
        <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 2 }}>
          {filteredDocuments.map((document) => (
              <Card
                sx={{
                  height: '100%',
                  cursor: onDocumentSelect ? 'pointer' : 'default',
                  transition: 'all 0.2s',
                  '&:hover': {
                    elevation: 4,
                    transform: onDocumentSelect ? 'translateY(-2px)' : 'none',
                  },
                }}
                onClick={() => onDocumentSelect?.(document)}
              >
                <CardContent>
                  {/* Header */}
                  <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1, mb: 2 }}>
                    {getFileIcon(document.filename, document.status)}
                    <Box sx={{ flexGrow: 1, minWidth: 0 }}>
                      <Tooltip title={document.title}>
                        <Typography
                          variant="subtitle2"
                          sx={{
                            fontWeight: 'bold',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap',
                          }}
                        >
                          {document.title}
                        </Typography>
                      </Tooltip>
                      {/* Only show filename for regular uploads, not for HTML documentation */}
                      {(document as any).sourceType !== 'html_documentation' &&
                       (document as any).sourceType !== 'html_folder' && (
                        <Typography
                          variant="caption"
                          color="text.secondary"
                          sx={{
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap',
                            display: 'block',
                          }}
                        >
                          {document.filename}
                        </Typography>
                      )}
                    </Box>
                    <IconButton
                      size="small"
                      onClick={(e) => handleMenuOpen(e, document)}
                    >
                      <MoreVertIcon fontSize="small" />
                    </IconButton>
                  </Box>

                  {/* Status */}
                  <Box sx={{ mb: 2 }}>
                    {getStatusChip(document.status)}
                  </Box>

                  {/* HTML Documentation Discovery Stats */}
                  {(document as any).sourceType === 'html_documentation' && (document as any).discoveryStats && (
                    <Box sx={{ mb: 2, p: 1, bgcolor: 'info.light', borderRadius: 1 }}>
                      <Typography variant="caption" sx={{ display: 'flex', alignItems: 'center', gap: 0.5, fontWeight: 'bold', color: 'info.dark' }}>
                        📚 HTML Documentation Collection
                      </Typography>
                      <Typography variant="caption" sx={{ display: 'block', color: 'info.dark', mt: 0.5 }}>
                        {(document as any).discoveryStats.totalFiles} file(s) discovered
                      </Typography>
                    </Box>
                  )}

                  {/* Processing Progress */}
                  {document.status === 'processing' && (() => {
                    const docId = parseInt(document.id, 10);
                    // Merge WebSocket progress (priority) with local API polling progress (fallback)
                    const progress = documentProgress[docId] || localProgress[docId];

                    return (
                      <Box sx={{ mb: 2 }}>
                        {progress ? (
                          <>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 0.5 }}>
                              <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 500 }}>
                                {progress.stage}
                              </Typography>
                              <Typography variant="caption" color="primary" sx={{ fontWeight: 'bold' }}>
                                {progress.progress.toFixed(1)}%
                              </Typography>
                            </Box>
                            <LinearProgress
                              variant="determinate"
                              value={progress.progress}
                              sx={{
                                height: 6,
                                borderRadius: 1,
                                backgroundColor: 'rgba(0, 0, 0, 0.1)',
                                '& .MuiLinearProgress-bar': {
                                  borderRadius: 1,
                                  transition: 'transform 0.4s ease-in-out',
                                },
                              }}
                            />
                          </>
                        ) : (
                          <>
                            <LinearProgress />
                            <Typography variant="caption" color="text.secondary">
                              Processing document...
                            </Typography>
                          </>
                        )}
                      </Box>
                    );
                  })()}

                  {/* Metadata */}
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                    <Typography variant="caption" color="text.secondary">
                      Size: {formatFileSize(document.size)}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Uploaded: {formatDate(document.uploadedAt)}
                    </Typography>
                    {document.chunksCount && (
                      <Typography variant="caption" color="text.secondary">
                        Chunks: {document.chunksCount}
                      </Typography>
                    )}
                    {document.processingTime && (
                      <Typography variant="caption" color="text.secondary">
                        Processed in: {document.processingTime.toFixed(2)}s
                      </Typography>
                    )}
                  </Box>
                </CardContent>
              </Card>
          ))}
        </Box>
      )}

      {/* Document Menu */}
      <Menu
        anchorEl={menuAnchor}
        open={Boolean(menuAnchor)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={() => {
          if (selectedDocument && onDocumentSelect) {
            onDocumentSelect(selectedDocument);
          }
          handleMenuClose();
        }}>
          <ListItemIcon>
            <ViewIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>View Details</ListItemText>
        </MenuItem>
        {/* Download Extracted Content (JSON) - Available for ALL documents */}
        <MenuItem onClick={async () => {
          if (selectedDocument) {
            try {
              const result = await apiService.exportDocumentChunks(selectedDocument.id);
              if (result.success && result.data) {
                const blob = new Blob([JSON.stringify(result.data, null, 2)], { type: 'application/json' });
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `${selectedDocument.title.replace(/[^a-z0-9]/gi, '_')}_extracted_${new Date().toISOString().split('T')[0]}.json`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
              } else {
                alert('Failed to export document chunks');
              }
            } catch (error) {
              console.error('Export error:', error);
              alert(`Error exporting document chunks: ${error}`);
            }
          }
          handleMenuClose();
        }}>
          <ListItemIcon>
            <DownloadIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Download Extracted Content (JSON)</ListItemText>
        </MenuItem>
        {/* Download Original File - Only for file-based uploads */}
        {selectedDocument?.sourceType === 'file' && selectedDocument?.filename && (
          <MenuItem onClick={() => {
            if (selectedDocument) {
              window.open(`/api/documents/${selectedDocument.id}/download`, '_blank');
            }
            handleMenuClose();
          }}>
            <ListItemIcon>
              <DownloadIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText>Download Original File</ListItemText>
          </MenuItem>
        )}
        <MenuItem
          onClick={() => selectedDocument && handleDeleteClick(selectedDocument)}
          sx={{ color: 'error.main' }}
        >
          <ListItemIcon>
            <DeleteIcon fontSize="small" color="error" />
          </ListItemIcon>
          <ListItemText>Delete</ListItemText>
        </MenuItem>
      </Menu>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialogOpen}
        onClose={() => setDeleteDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Delete Document</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete "{documentToDelete?.title}"?
            This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>
            Cancel
          </Button>
          <Button
            onClick={handleDeleteConfirm}
            color="error"
            variant="contained"
          >
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default DocumentList;