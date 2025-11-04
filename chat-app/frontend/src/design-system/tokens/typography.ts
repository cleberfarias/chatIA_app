export const typography = {
  fontFamily: {
    primary: '"Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
    monospace: '"Courier New", Courier, monospace',
  },
  
  fontSize: {
    xs: '11px',
    sm: '12px',
    base: '14px',
    md: '16px',
    lg: '18px',
    xl: '20px',
    xxl: '24px',
  },
  
  fontWeight: {
    light: 300,
    regular: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
  },
  
  lineHeight: {
    tight: 1.2,
    normal: 1.4,
    relaxed: 1.6,
  },
} as const;

export type TypographyToken = keyof typeof typography;
