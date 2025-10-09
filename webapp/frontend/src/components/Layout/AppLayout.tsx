/**
 * Main Application Layout - Security-First Design
 * Provides consistent layout with navigation and security monitoring
 */

import React, { useState } from 'react';
import {
  AppBar,
  Box,
  CssBaseline,
  Drawer,
  IconButton,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Typography,
  useTheme,
  useMediaQuery,
  Avatar,
  Menu,
  MenuItem,
  Chip,
  Tooltip,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Chat as ChatIcon,
  Description as DocumentIcon,
  Settings as SettingsIcon,
  Security as SecurityIcon,
  AccountCircle,
  Logout,
  Dashboard as DashboardIcon,
} from '@mui/icons-material';
import { useAuth } from '../../contexts/AuthContext';
import { useChat } from '../../contexts/ChatContext';

const drawerWidth = 280;

interface AppLayoutProps {
  children: React.ReactNode;
  currentPage?: string;
  onPageChange?: (page: string) => void;
  desktopDrawerOpen?: boolean;
  onDesktopDrawerChange?: (open: boolean) => void;
}

const AppLayout: React.FC<AppLayoutProps> = ({
  children,
  currentPage = 'chat',
  onPageChange,
  desktopDrawerOpen,
  onDesktopDrawerChange
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [mobileOpen, setMobileOpen] = useState(false);
  const [internalDesktopOpen, setInternalDesktopOpen] = useState(true);
  const [userMenuAnchor, setUserMenuAnchor] = useState<null | HTMLElement>(null);

  const { user, logout } = useAuth();
  const { isConnected, selectedModel, availableModels } = useChat();

  // Use controlled or uncontrolled state
  const desktopOpen = desktopDrawerOpen !== undefined ? desktopDrawerOpen : internalDesktopOpen;

  const navigationItems = [
    { id: 'dashboard', label: 'Dashboard', icon: <DashboardIcon />, path: '/dashboard' },
    { id: 'chat', label: 'Chat', icon: <ChatIcon />, path: '/chat' },
    { id: 'documents', label: 'Documents', icon: <DocumentIcon />, path: '/documents' },
    { id: 'settings', label: 'Settings', icon: <SettingsIcon />, path: '/settings' },
    { id: 'security', label: 'Security', icon: <SecurityIcon />, path: '/security' },
  ];

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const handleDesktopDrawerToggle = () => {
    const newState = !desktopOpen;
    if (onDesktopDrawerChange) {
      onDesktopDrawerChange(newState);
    } else {
      setInternalDesktopOpen(newState);
    }
  };

  const handleUserMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setUserMenuAnchor(event.currentTarget);
  };

  const handleUserMenuClose = () => {
    setUserMenuAnchor(null);
  };

  const handleLogout = async () => {
    handleUserMenuClose();
    await logout();
  };

  const handleNavigation = (pageId: string) => {
    if (onPageChange) {
      onPageChange(pageId);
    }
    if (isMobile) {
      setMobileOpen(false);
    }
  };

  const drawer = (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* App Title */}
      <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
        <Typography variant="h6" component="div" sx={{ fontWeight: 'bold' }}>
          🔒 Secure RAG
        </Typography>
        <Typography variant="caption" color="text.secondary">
          Local AI System
        </Typography>
      </Box>

      {/* Connection Status */}
      <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
          <Chip
            size="small"
            label={isConnected ? 'Connected' : 'Offline'}
            color={isConnected ? 'success' : 'error'}
            variant="outlined"
          />
          <Tooltip title={`Current AI Model: ${selectedModel}`}>
            <Chip
              size="small"
              label={selectedModel}
              color="primary"
              variant="outlined"
            />
          </Tooltip>
        </Box>
      </Box>

      {/* Navigation */}
      <Box sx={{ flexGrow: 1, overflow: 'auto' }}>
        <List>
          {navigationItems.map((item) => (
            <ListItem key={item.id} disablePadding>
              <ListItemButton
                selected={currentPage === item.id}
                onClick={() => handleNavigation(item.id)}
                sx={{
                  '&.Mui-selected': {
                    backgroundColor: theme.palette.primary.main + '20',
                    '&:hover': {
                      backgroundColor: theme.palette.primary.main + '30',
                    },
                  },
                }}
              >
                <ListItemIcon sx={{ color: currentPage === item.id ? 'primary.main' : 'inherit' }}>
                  {item.icon}
                </ListItemIcon>
                <ListItemText
                  primary={item.label}
                  sx={{
                    '& .MuiListItemText-primary': {
                      fontWeight: currentPage === item.id ? 'bold' : 'normal',
                      color: currentPage === item.id ? 'primary.main' : 'inherit',
                    }
                  }}
                />
              </ListItemButton>
            </ListItem>
          ))}
        </List>
      </Box>

      {/* Security Badge */}
      <Box sx={{ p: 2, borderTop: 1, borderColor: 'divider' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <SecurityIcon fontSize="small" color="success" />
          <Typography variant="caption" color="success.main">
            100% Local Processing
          </Typography>
        </Box>
        <Typography variant="caption" color="text.secondary" display="block">
          No external connections
        </Typography>
      </Box>
    </Box>
  );

  return (
    <Box sx={{ display: 'flex', height: '100vh' }}>
      <CssBaseline />

      {/* App Bar */}
      <AppBar
        position="fixed"
        sx={{
          width: { xs: '100%', md: desktopOpen ? `calc(100% - ${drawerWidth}px)` : '100%' },
          ml: { xs: 0, md: desktopOpen ? `${drawerWidth}px` : 0 },
          zIndex: theme.zIndex.drawer + 1,
          transition: theme.transitions.create(['width', 'margin'], {
            easing: theme.transitions.easing.sharp,
            duration: theme.transitions.duration.leavingScreen,
          }),
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2, display: { xs: 'block', md: 'none' } }}
          >
            <MenuIcon />
          </IconButton>

          <IconButton
            color="inherit"
            aria-label="toggle drawer"
            edge="start"
            onClick={handleDesktopDrawerToggle}
            sx={{ mr: 2, display: { xs: 'none', md: 'block' } }}
          >
            <MenuIcon />
          </IconButton>

          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
            {navigationItems.find(item => item.id === currentPage)?.label || 'Secure RAG System'}
          </Typography>

          {/* Model Selector */}
          <Tooltip title="Current AI Model">
            <Chip
              label={selectedModel}
              size="small"
              color="secondary"
              sx={{ mr: 2, color: 'white', borderColor: 'white' }}
              variant="outlined"
            />
          </Tooltip>

          {/* User Menu */}
          <IconButton
            size="large"
            aria-label="account of current user"
            aria-controls="user-menu"
            aria-haspopup="true"
            onClick={handleUserMenuOpen}
            color="inherit"
          >
            <Avatar sx={{ width: 32, height: 32, fontSize: '0.875rem' }}>
              {user?.fullName?.charAt(0).toUpperCase() || 'U'}
            </Avatar>
          </IconButton>

          <Menu
            id="user-menu"
            anchorEl={userMenuAnchor}
            keepMounted
            open={Boolean(userMenuAnchor)}
            onClose={handleUserMenuClose}
          >
            <MenuItem disabled>
              <Box>
                <Typography variant="subtitle2">{user?.fullName}</Typography>
                <Typography variant="caption" color="text.secondary">
                  {user?.email}
                </Typography>
              </Box>
            </MenuItem>
            <MenuItem onClick={() => { handleNavigation('settings'); handleUserMenuClose(); }}>
              <ListItemIcon>
                <SettingsIcon fontSize="small" />
              </ListItemIcon>
              Settings
            </MenuItem>
            <MenuItem onClick={handleLogout}>
              <ListItemIcon>
                <Logout fontSize="small" />
              </ListItemIcon>
              Logout
            </MenuItem>
          </Menu>
        </Toolbar>
      </AppBar>

      {/* Drawer */}
      <Box
        component="nav"
        sx={{
          width: { xs: 0, md: desktopOpen ? drawerWidth : 0 },
          flexShrink: 0,
          transition: theme.transitions.create('width', {
            easing: theme.transitions.easing.sharp,
            duration: theme.transitions.duration.leavingScreen,
          }),
        }}
      >
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{
            keepMounted: true, // Better open performance on mobile
          }}
          sx={{
            display: { xs: 'block', md: 'none' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
          }}
        >
          {drawer}
        </Drawer>
        {desktopOpen && (
          <Drawer
            variant="permanent"
            sx={{
              display: { xs: 'none', md: 'block' },
              '& .MuiDrawer-paper': {
                boxSizing: 'border-box',
                width: drawerWidth,
              },
            }}
            open
          >
            {drawer}
          </Drawer>
        )}
      </Box>

      {/* Main Content */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          height: '100vh',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        <Toolbar /> {/* Spacer for AppBar */}
        <Box sx={{ flexGrow: 1, height: 0, overflow: 'hidden' }}>
          {children}
        </Box>
      </Box>
    </Box>
  );
};

export default AppLayout;