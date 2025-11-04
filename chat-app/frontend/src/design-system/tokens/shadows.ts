export const shadows = {
  none: 'none',
  sm: '0 1px 2px rgba(0, 0, 0, 0.1)',
  md: '0 2px 4px rgba(0, 0, 0, 0.15)',
  lg: '0 4px 8px rgba(0, 0, 0, 0.2)',
  xl: '0 8px 16px rgba(0, 0, 0, 0.25)',
} as const;

export type ShadowToken = keyof typeof shadows;