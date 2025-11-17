/**
 * Status Badge Component
 * Connection and status indicators
 */

import React from 'react';
import { Chip, ChipProps } from '@mui/material';
import {
  CheckCircle,
  Error as ErrorIcon,
  Warning,
  Info,
  Circle,
} from '@mui/icons-material';

export interface StatusBadgeProps extends Omit<ChipProps, 'color'> {
  status: 'online' | 'offline' | 'connected' | 'disconnected' | 'error' | 'warning' | 'info' | 'idle';
  showIcon?: boolean;
}

const statusConfig = {
  online: {
    label: 'Online',
    color: 'success' as const,
    icon: CheckCircle,
  },
  offline: {
    label: 'Offline',
    color: 'error' as const,
    icon: ErrorIcon,
  },
  connected: {
    label: 'Connected',
    color: 'success' as const,
    icon: CheckCircle,
  },
  disconnected: {
    label: 'Disconnected',
    color: 'error' as const,
    icon: ErrorIcon,
  },
  error: {
    label: 'Error',
    color: 'error' as const,
    icon: ErrorIcon,
  },
  warning: {
    label: 'Warning',
    color: 'warning' as const,
    icon: Warning,
  },
  info: {
    label: 'Info',
    color: 'info' as const,
    icon: Info,
  },
  idle: {
    label: 'Idle',
    color: 'default' as const,
    icon: Circle,
  },
};

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  showIcon = true,
  label,
  ...chipProps
}) => {
  const config = statusConfig[status];
  const Icon = config.icon;

  return (
    <Chip
      size="small"
      label={label || config.label}
      color={config.color}
      variant="outlined"
      icon={showIcon ? <Icon fontSize="small" /> : undefined}
      {...chipProps}
    />
  );
};

export interface ConnectionStatusProps {
  isConnected: boolean;
  variant?: 'outlined' | 'filled';
}

export const ConnectionStatus: React.FC<ConnectionStatusProps> = ({
  isConnected,
  variant = 'outlined',
}) => (
  <StatusBadge
    status={isConnected ? 'connected' : 'disconnected'}
    variant={variant}
  />
);

export default StatusBadge;
