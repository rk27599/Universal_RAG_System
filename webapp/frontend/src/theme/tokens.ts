/**
 * Design Token System
 * Centralized design values for consistent UI
 */

export const spacing = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
  xxl: 48,
  xxxl: 64,
};

export const borderRadius = {
  none: 0,
  sm: 4,
  md: 8,
  lg: 12,
  xl: 16,
  full: 9999,
};

export const shadows = {
  none: 'none',
  sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
  base: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
  md: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
  lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
  xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
  card: '0 2px 8px rgba(0, 0, 0, 0.1)',
  elevated: '0 4px 16px rgba(0, 0, 0, 0.15)',
  inner: 'inset 0 2px 4px 0 rgba(0, 0, 0, 0.06)',
};

export const typography = {
  fontFamily: {
    sans: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    mono: '"Fira Code", "Consolas", "Monaco", "Courier New", monospace',
  },
  fontSize: {
    xs: '0.75rem',    // 12px
    sm: '0.875rem',   // 14px
    base: '1rem',     // 16px
    lg: '1.125rem',   // 18px
    xl: '1.25rem',    // 20px
    '2xl': '1.5rem',  // 24px
    '3xl': '1.875rem', // 30px
    '4xl': '2.25rem', // 36px
  },
  fontWeight: {
    light: 300,
    normal: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
  },
  lineHeight: {
    tight: 1.25,
    normal: 1.5,
    relaxed: 1.75,
  },
};

export const transitions = {
  duration: {
    fast: '150ms',
    base: '200ms',
    slow: '300ms',
    slower: '500ms',
  },
  timing: {
    ease: 'cubic-bezier(0.4, 0, 0.2, 1)',
    easeIn: 'cubic-bezier(0.4, 0, 1, 1)',
    easeOut: 'cubic-bezier(0, 0, 0.2, 1)',
    easeInOut: 'cubic-bezier(0.4, 0, 0.2, 1)',
  },
};

export const zIndex = {
  dropdown: 1000,
  sticky: 1020,
  fixed: 1030,
  modalBackdrop: 1040,
  modal: 1050,
  popover: 1060,
  tooltip: 1070,
};

// Semantic colors (will be used in theme)
export const colors = {
  success: {
    light: '#4caf50',
    main: '#2e7d32',
    dark: '#1b5e20',
  },
  warning: {
    light: '#ff9800',
    main: '#f57c00',
    dark: '#e65100',
  },
  error: {
    light: '#ef5350',
    main: '#d32f2f',
    dark: '#c62828',
  },
  info: {
    light: '#29b6f6',
    main: '#0288d1',
    dark: '#01579b',
  },
};

// Breakpoints (matches MUI defaults)
export const breakpoints = {
  xs: 0,
  sm: 600,
  md: 900,
  lg: 1200,
  xl: 1536,
};

export default {
  spacing,
  borderRadius,
  shadows,
  typography,
  transitions,
  zIndex,
  colors,
  breakpoints,
};
