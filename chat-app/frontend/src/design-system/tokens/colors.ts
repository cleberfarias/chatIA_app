export const colors = {
  // WhatsApp Brand Colors
  primary: '#075e54',
  primaryLight: '#128c7e',
  secondary: '#25d366',
  
  // Message Colors
  sentMessage: '#dcf8c6',
  receivedMessage: '#ffffff',
  
  // Background
  chatBackground: '#e5ddd5',
  inputBackground: '#f0f0f0',
  
  // Text
  textPrimary: 'rgba(0, 0, 0, 0.87)',
  textSecondary: 'rgba(0, 0, 0, 0.6)',
  textHint: 'rgba(0, 0, 0, 0.45)',
  textWhite: '#ffffff',
  
  // Status
  online: '#25d366',
  offline: '#9e9e9e',
  typing: '#075e54',
  
  // UI Elements
  border: '#d1d1d1',
  divider: 'rgba(0, 0, 0, 0.12)',
  shadow: 'rgba(0, 0, 0, 0.1)',
  
  // Status Message
  success: '#4caf50',
  error: '#f44336',
  warning: '#ff9800',
  info: '#2196f3',
} as const;

export type ColorToken = keyof typeof colors;