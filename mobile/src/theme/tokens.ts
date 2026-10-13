/** Eigen design tokens — single source of truth for theme values. */

export const colors = {
  background: '#F7F5F0',
  surface: '#FFFFFF',
  surfaceMuted: '#EFEAE0',
  ink: '#1B2430',
  inkMuted: '#5B6572',
  accent: '#1D4ED8',
  accentInk: '#FFFFFF',
  success: '#166534',
  successBg: '#DCFCE7',
  warning: '#92400E',
  warningBg: '#FEF3C7',
  danger: '#B91C1C',
  dangerBg: '#FEE2E2',
  border: '#D8D2C4',
} as const;

export const spacing = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
} as const;

export const typography = {
  brand: 30,
  title: 22,
  heading: 18,
  body: 16,
  small: 14,
  mono: 15,
} as const;

export const layout = {
  /** Minimum accessible touch target (px). */
  touchTarget: 48,
  radius: 12,
  maxContentWidth: 640,
} as const;
