# TypeScript Design Tokens - Design System LIA v4.1

```typescript
export const colors = {
  bg: { primary: '#FFFFFF', secondary: '#F9FAFB', tertiary: '#F3F4F6', elevated: '#FFFFFF' },
  text: { primary: '#111827', body: '#1F2937', secondary: '#4B5563', muted: '#6B7280', disabled: '#9CA3AF' },
  border: { subtle: '#E5E7EB', default: '#D1D5DB', medium: '#9CA3AF' },
  wedo: {
    cyan: '#60BED1', cyanDark: '#4DA8BB', cyanLight: 'rgba(96, 190, 209, 0.1)',
    green: '#5DA47A', greenLight: 'rgba(93, 164, 122, 0.1)',
    orange: '#D19960', orangeLight: 'rgba(209, 153, 96, 0.1)',
    purple: '#9860D1', purpleLight: 'rgba(152, 96, 209, 0.1)',
    magenta: '#D160AB', magentaLight: 'rgba(209, 96, 171, 0.1)',
    amber: '#F59E0B',
  },
  semantic: {
    success: { bg: '#F0FDF4', text: '#15803D', border: '#BBF7D0' },
    warning: { bg: '#FFFBEB', text: '#B45309', border: '#FDE68A' },
    error: { bg: '#FEF2F2', text: '#B91C1C', border: '#FECACA' },
    info: { bg: '#EFF6FF', text: '#1D4ED8', border: '#BFDBFE' },
  },
} as const;

export const typography = {
  fonts: {
    brand: "'Open Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif",
    data: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif",
  },
  sizes: {
    display: { size: '40px', lineHeight: '50px', weight: 700 },
    h1: { size: '32px', lineHeight: '40px', weight: 700 },
    h2: { size: '24px', lineHeight: '30px', weight: 700 },
    h3: { size: '20px', lineHeight: '30px', weight: 600 },
    h4: { size: '16px', lineHeight: '24px', weight: 600 },
    h5: { size: '14px', lineHeight: '21px', weight: 600 },
    bodyLarge: { size: '16px', lineHeight: '24px', weight: 400 },
    body: { size: '14px', lineHeight: '21px', weight: 400 },
    bodySmall: { size: '12px', lineHeight: '18px', weight: 400 },
    caption: { size: '12px', lineHeight: '18px', weight: 400 },
    label: { size: '11px', lineHeight: '16.5px', weight: 600 },
    micro: { size: '10px', lineHeight: '15px', weight: 500 },
  },
} as const;

export const spacing = {
  0: '0px', 0.5: '4px', 1: '8px', 1.5: '12px', 2: '16px',
  2.5: '20px', 3: '24px', 4: '32px', 5: '40px', 6: '48px', 8: '64px',
} as const;

export const borderRadius = {
  sm: '4px', default: '6px', md: '8px', lg: '12px', xl: '16px', full: '9999px',
} as const;

export const shadows = {
  sm: '0 1px 2px rgba(0, 0, 0, 0.05)',
  default: '0 2px 4px rgba(0, 0, 0, 0.06), 0 1px 2px rgba(0, 0, 0, 0.04)',
  md: '0 4px 8px rgba(0, 0, 0, 0.08), 0 2px 4px rgba(0, 0, 0, 0.06)',
  lg: '0 8px 16px rgba(0, 0, 0, 0.10), 0 4px 8px rgba(0, 0, 0, 0.08)',
  xl: '0 16px 32px rgba(0, 0, 0, 0.12), 0 8px 16px rgba(0, 0, 0, 0.10)',
  focus: '0 0 0 3px rgba(17, 24, 39, 0.2)',
} as const;

export const transitions = {
  fast: '100ms cubic-bezier(0.4, 0, 0.2, 1)',
  default: '150ms cubic-bezier(0.4, 0, 0.2, 1)',
  slow: '200ms cubic-bezier(0.4, 0, 0.2, 1)',
} as const;

export const breakpoints = { sm: 640, md: 768, lg: 1024, xl: 1280, '2xl': 1536 } as const;

export const buttonStyles = {
  primary: {
    default: { bg: colors.text.primary, text: '#FFFFFF', border: 'none' },
    hover: { bg: colors.text.body, transform: 'translateY(-1px)' },
    focus: { ring: shadows.focus },
    disabled: { bg: colors.border.default, text: colors.text.muted, cursor: 'not-allowed' },
  },
  secondary: {
    default: { bg: 'transparent', text: colors.text.primary, border: `1px solid ${colors.border.default}` },
    hover: { bg: colors.bg.secondary },
  },
  ghost: {
    default: { bg: 'transparent', text: colors.text.secondary },
    hover: { bg: colors.bg.tertiary, text: colors.text.primary },
  },
} as const;

export function getButtonClasses(variant: 'primary' | 'secondary' | 'ghost' = 'primary') {
  const base = 'px-4 py-2 rounded text-sm font-semibold transition-all duration-150 focus:outline-none';
  const variants = {
    primary: 'bg-gray-900 text-white hover:bg-gray-800 focus:ring-2 focus:ring-gray-900/20 disabled:bg-gray-300 disabled:text-gray-500',
    secondary: 'bg-transparent text-gray-900 border border-gray-300 hover:bg-gray-50 focus:ring-2 focus:ring-gray-900/20',
    ghost: 'bg-transparent text-gray-700 hover:bg-gray-100 hover:text-gray-900',
  };
  return `${base} ${variants[variant]}`;
}

export function getBadgeClasses(type: 'success' | 'warning' | 'error' | 'info' | 'neutral') {
  const base = 'inline-flex items-center px-2 py-1 rounded text-xs font-medium border';
  const variants = {
    success: 'bg-green-50 text-green-700 border-green-200',
    warning: 'bg-amber-50 text-amber-700 border-amber-200',
    error: 'bg-red-50 text-red-700 border-red-200',
    info: 'bg-blue-50 text-blue-700 border-blue-200',
    neutral: 'bg-gray-100 text-gray-700 border-gray-200',
  };
  return `${base} ${variants[type]}`;
}

export type ColorToken = keyof typeof colors;
export type SpacingToken = keyof typeof spacing;
export type ShadowToken = keyof typeof shadows;
```
