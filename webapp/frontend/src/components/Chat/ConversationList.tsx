/**
 * Conversation List - Chat History Management
 * Displays and manages chat conversations with search and organization
 */

import React, { useState } from 'react';
import {
  Box,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  ListItemIcon,
  IconButton,
  Typography,
  TextField,
  Fab,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Menu,
  MenuItem,
  Chip,
  Tooltip,
  InputAdornment,
  Alert,
} from '@mui/material';
import {
  Add as AddIcon,
  Chat as ChatIcon,
  Search as SearchIcon,
  MoreVert as MoreVertIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  Archive as ArchiveIcon,
  PushPin as PinIcon,
  FilterList as FilterIcon,
} from '@mui/icons-material';
import { useChat } from '../../contexts/ChatContext';
import { Conversation } from '../../services/api';

interface ConversationListProps {
  onConversationSelect: (conversationId: string) => void;
  selectedConversationId?: string;
  drawerOpen?: boolean;
}

const ConversationList: React.FC<ConversationListProps> = ({
  onConversationSelect,
  selectedConversationId,
  drawerOpen = true,
}) => {
  const {
    conversations,
    currentConversation,
    createConversation,
    selectConversation,
    deleteConversation,
    isLoading,
    error,
  } = useChat();

  const [searchQuery, setSearchQuery] = useState('');
  const [showNewConversationDialog, setShowNewConversationDialog] = useState(false);
  const [newConversationTitle, setNewConversationTitle] = useState('');
  const [conversationMenuAnchor, setConversationMenuAnchor] = useState<null | HTMLElement>(null);
  const [selectedConversationForMenu, setSelectedConversationForMenu] = useState<string | null>(null);
  const [filterBy, setFilterBy] = useState<'all' | 'active' | 'archived'>('all');

  // Filter conversations based on search and filter
  const filteredConversations = conversations.filter((conv) => {
    const matchesSearch = !searchQuery ||
      conv.title.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesFilter = filterBy === 'all' ||
      (filterBy === 'active' && conv.isActive) ||
      (filterBy === 'archived' && !conv.isActive);

    return matchesSearch && matchesFilter;
  });

  const handleCreateConversation = async () => {
    const title = newConversationTitle.trim() || undefined;
    const success = await createConversation(title);

    if (success) {
      setShowNewConversationDialog(false);
      setNewConversationTitle('');
    }
  };

  const handleConversationSelect = async (conversationId: string) => {
    await selectConversation(conversationId);
    onConversationSelect(conversationId);
  };

  const handleConversationMenuOpen = (event: React.MouseEvent<HTMLElement>, conversationId: string) => {
    event.stopPropagation();
    setConversationMenuAnchor(event.currentTarget);
    setSelectedConversationForMenu(conversationId);
  };

  const handleConversationMenuClose = () => {
    setConversationMenuAnchor(null);
    setSelectedConversationForMenu(null);
  };

  const handleDeleteConversation = async () => {
    if (selectedConversationForMenu) {
      await deleteConversation(selectedConversationForMenu);
    }
    handleConversationMenuClose();
  };

  const formatLastActivity = (lastActivity: string) => {
    const date = new Date(lastActivity);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffDays === 0) {
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } else if (diffDays === 1) {
      return 'Yesterday';
    } else if (diffDays < 7) {
      return `${diffDays} days ago`;
    } else {
      return date.toLocaleDateString();
    }
  };

  const renderConversation = (conversation: Conversation) => {
    const isSelected = conversation.id === selectedConversationId;

    return (
      <ListItem key={conversation.id} disablePadding>
        <ListItemButton
          selected={isSelected}
          onClick={() => handleConversationSelect(conversation.id)}
          sx={{
            borderRadius: 1,
            mx: 1,
            mb: 0.5,
            '&.Mui-selected': {
              backgroundColor: 'primary.main',
              color: 'primary.contrastText',
              '&:hover': {
                backgroundColor: 'primary.dark',
              },
            },
          }}
        >
          <ListItemIcon sx={{ color: isSelected ? 'inherit' : 'text.secondary' }}>
            <ChatIcon />
          </ListItemIcon>

          <ListItemText
            primary={
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Typography
                  variant="subtitle2"
                  sx={{
                    fontWeight: 'medium',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                    flex: 1,
                  }}
                >
                  {conversation.title || 'New Conversation'}
                </Typography>
                {!conversation.isActive && (
                  <Chip size="small" label="Archived" variant="outlined" sx={{ fontSize: '0.7rem' }} />
                )}
              </Box>
            }
            secondary={
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography variant="caption" sx={{ opacity: 0.8 }}>
                  {conversation.messageCount} messages
                </Typography>
                <Typography variant="caption" sx={{ opacity: 0.6 }}>
                  {formatLastActivity(conversation.lastActivity)}
                </Typography>
              </Box>
            }
          />

          <IconButton
            size="small"
            onClick={(e) => handleConversationMenuOpen(e, conversation.id)}
            sx={{
              color: isSelected ? 'inherit' : 'text.secondary',
              '&:hover': { backgroundColor: isSelected ? 'primary.light' : 'action.hover' },
            }}
          >
            <MoreVertIcon fontSize="small" />
          </IconButton>
        </ListItemButton>
      </ListItem>
    );
  };

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', position: 'relative' }}>
      {/* Header */}
      <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
        <Typography variant="h6" gutterBottom>
          Conversations
        </Typography>

        {/* Search */}
        <TextField
          size="small"
          fullWidth
          placeholder="Search conversations..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon fontSize="small" />
              </InputAdornment>
            ),
          }}
          sx={{ mb: 1 }}
        />

        {/* Filter Chips */}
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Chip
            size="small"
            label="All"
            onClick={() => setFilterBy('all')}
            color={filterBy === 'all' ? 'primary' : 'default'}
            variant={filterBy === 'all' ? 'filled' : 'outlined'}
          />
          <Chip
            size="small"
            label="Active"
            onClick={() => setFilterBy('active')}
            color={filterBy === 'active' ? 'primary' : 'default'}
            variant={filterBy === 'active' ? 'filled' : 'outlined'}
          />
          <Chip
            size="small"
            label="Archived"
            onClick={() => setFilterBy('archived')}
            color={filterBy === 'archived' ? 'primary' : 'default'}
            variant={filterBy === 'archived' ? 'filled' : 'outlined'}
          />
        </Box>
      </Box>

      {/* Conversation List */}
      <Box sx={{ flexGrow: 1, overflow: 'auto', pb: 10 }}>
        {filteredConversations.length === 0 ? (
          <Box sx={{ p: 3, textAlign: 'center' }}>
            <ChatIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" color="text.secondary" gutterBottom>
              {searchQuery ? 'No conversations found' : 'No conversations yet'}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {searchQuery ? 'Try adjusting your search terms' : 'Start a new conversation to get started'}
            </Typography>
          </Box>
        ) : (
          <List sx={{ py: 1 }}>
            {filteredConversations.map(renderConversation)}
          </List>
        )}
      </Box>

      {/* New Conversation FAB - Fixed at bottom */}
      <Box
        sx={{
          position: 'absolute',
          bottom: 0,
          left: 0,
          right: 0,
          p: 2,
          backgroundColor: 'background.paper',
          borderTop: 1,
          borderColor: 'divider',
        }}
      >
        <Fab
          color="primary"
          aria-label="new conversation"
          onClick={() => setShowNewConversationDialog(true)}
          variant="extended"
          sx={{
            width: '100%',
          }}
        >
          <AddIcon sx={{ mr: 1 }} />
          New Conversation
        </Fab>
      </Box>

      {/* New Conversation Dialog */}
      <Dialog
        open={showNewConversationDialog}
        onClose={() => setShowNewConversationDialog(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>New Conversation</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Conversation Title (Optional)"
            fullWidth
            variant="outlined"
            value={newConversationTitle}
            onChange={(e) => setNewConversationTitle(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !isLoading) {
                e.preventDefault();
                handleCreateConversation();
              }
            }}
            placeholder="Enter a title or leave blank for auto-generation"
            sx={{ mt: 1 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowNewConversationDialog(false)}>
            Cancel
          </Button>
          <Button
            onClick={handleCreateConversation}
            variant="contained"
            disabled={isLoading}
          >
            Create
          </Button>
        </DialogActions>
      </Dialog>

      {/* Conversation Menu */}
      <Menu
        anchorEl={conversationMenuAnchor}
        open={Boolean(conversationMenuAnchor)}
        onClose={handleConversationMenuClose}
      >
        <MenuItem onClick={handleConversationMenuClose}>
          <ListItemIcon>
            <EditIcon fontSize="small" />
          </ListItemIcon>
          Rename
        </MenuItem>
        <MenuItem onClick={handleConversationMenuClose}>
          <ListItemIcon>
            <PinIcon fontSize="small" />
          </ListItemIcon>
          Pin
        </MenuItem>
        <MenuItem onClick={handleConversationMenuClose}>
          <ListItemIcon>
            <ArchiveIcon fontSize="small" />
          </ListItemIcon>
          Archive
        </MenuItem>
        <MenuItem onClick={handleDeleteConversation} sx={{ color: 'error.main' }}>
          <ListItemIcon>
            <DeleteIcon fontSize="small" color="error" />
          </ListItemIcon>
          Delete
        </MenuItem>
      </Menu>
    </Box>
  );
};

export default ConversationList;