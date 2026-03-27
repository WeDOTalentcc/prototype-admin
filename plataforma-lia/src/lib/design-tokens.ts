/**
 * LIA Platform - Design Tokens (TypeScript)
 * 
 * Centraliza todos os tokens de design para uso programático em componentes React.
 * Mapeamento Tailwind → Vuetify preparado para migração futura.
 * 
 * @version 4.0.0
 * @updated 2026-02-02
 * 
 * ATUALIZAÇÃO v4.0: Alinhamento com Design System v4
 * 
 * TIPOGRAFIA (DS v4.1):
 * - Open Sans (60%): UI principal, títulos, labels, body text, sidebar
 * - Inter (40%): Números, métricas, dados tabulares
 * 
 * CORES (v4):
 * - 90% Grayscale (gray-50 a gray-950)
 * - 10% WeDo Accent Colors (cyan, green, orange, purple, magenta)
 * - Botões primários: bg-gray-900 (preto)
 * - Cyan reservado para LIA/IA e links
 * 
 * HIERARQUIA DE TEXTO (4 níveis):
 * - Title: gray-900 (light) / gray-50 (dark) - Títulos principais
 * - Body: gray-800 (light) / gray-200 (dark) - Texto principal, labels
 * - Secondary: gray-600 (light) / gray-400 (dark) - Descrições, captions
 * - Muted: gray-500 (light) / gray-500 (dark) - Placeholders, disabled
 */

export const colors = {
  primary: {
    DEFAULT: '#111827', // v4: gray-900 (preto) para ações primárias
    hover: '#1F2937',   // v4: gray-800
    active: '#030712',  // v4: gray-950
    light: '#F3F4F6',   // v4: gray-100
    // Aliases para compatibilidade com v3
    dark: '#030712',    // v4: DEPRECATED - use active
  },
  
  // v3 compatibility: accent color (cyan era primário em v3)
  accent: {
    DEFAULT: '#60BED1',
    hover: '#0E7490',
    light: 'rgba(96,190,209,0.1)',
  },
  
  gray: {
    50: '#F9FAFB',
    100: '#F3F4F6',
    200: '#E5E7EB',
    300: '#D1D5DB',
    400: '#9CA3AF',
    500: '#6B7280',
    600: '#4B5563',
    700: '#374151',
    800: '#1F2937',
    900: '#111827',
    950: '#030712',
  },
  
  text: {
    light: {
      title: '#111827',       // v4: gray-900 - Títulos principais
      body: '#1F2937',        // gray-800 - Texto principal, labels
      secondary: '#4B5563',   // gray-600 - Descrições, captions
      muted: '#6B7280',       // gray-500 - Placeholders, disabled
    },
    dark: {
      title: '#F9FAFB',       // gray-50 - Títulos principais
      body: '#E5E7EB',        // gray-200 - Texto principal, labels
      secondary: '#9CA3AF',   // gray-400 - Descrições, captions
      muted: '#6B7280',       // gray-500 - Placeholders, disabled
    },
  },
  
  status: {
    success: '#16A34A',       // v4: green-600
    successLight: '#DCFCE7',  // v4: green-100
    successText: '#166534',   // v4: green-800
    warning: '#D97706',       // v4: amber-600
    warningLight: '#FEF3C7',  // v4: amber-100
    warningText: '#92400E',   // v4: amber-800
    error: '#DC2626',         // v4: red-600
    errorLight: '#FEE2E2',    // v4: red-100
    errorText: '#991B1B',     // v4: red-800
    info: '#2563EB',          // v4: blue-600
    infoLight: '#DBEAFE',     // v4: blue-100
    infoText: '#1E40AF',      // v4: blue-800
  },
  
  wedo: {
    cyan: '#60BED1',
    cyanDark: '#0E7490',      // v4: para texto em fundo cyan light
    cyanLight: 'rgba(96,190,209,0.1)',
    green: '#5DA47A',
    greenDark: '#166534',
    greenLight: 'rgba(93,164,122,0.1)',
    orange: '#D19960',
    orangeDark: '#9A3412',
    orangeLight: 'rgba(209,153,96,0.1)',
    purple: '#9860D1',
    purpleDark: '#6B21A8',
    purpleLight: 'rgba(152,96,209,0.1)',
    magenta: '#D160AB',
    magentaDark: '#9D174D',
    magentaLight: 'rgba(209,96,171,0.1)',
  },
  
  background: {
    primary: '#FFFFFF',
    secondary: '#F9FAFB',
    tertiary: '#F3F4F6',
    overlay: 'rgba(0, 0, 0, 0.5)',
  },
  
  border: {
    light: '#F3F4F6',    // gray-100
    default: '#E5E7EB',  // gray-200
    medium: '#D1D5DB',   // gray-300
    dark: '#9CA3AF',     // gray-400
  },
} as const

export const typography = {
  fontFamily: {
    primary: '"Open Sans", sans-serif',     // v4: 85% - UI principal
    data: '"Inter", sans-serif',            // v4: 10% - Números e métricas
    sidebar: '"Open Sans", sans-serif', // DS v4.1: Source Serif 4 removido
    mono: '"JetBrains Mono", monospace',
    // Aliases para compatibilidade com v3
    title: '"Open Sans", sans-serif',       // v4: DEPRECATED - use primary
    body: '"Open Sans", sans-serif',        // v4: DEPRECATED - use primary
  },
  
  fontSize: {
    xs: '10px',
    sm: '11px',
    base: '12px',
    md: '13px',
    lg: '14px',
    xl: '16px',
    '2xl': '18px',
    '3xl': '24px',
    '4xl': '32px',
  },
  
  fontWeight: {
    normal: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
  },
  
  lineHeight: {
    tight: 1.2,
    snug: 1.375,
    normal: 1.5,
    relaxed: 1.625,
  },
} as const

export const spacing = {
  px: '1px',
  0: '0',
  0.5: '2px',
  1: '4px',
  1.5: '6px',
  2: '8px',
  2.5: '10px',
  3: '12px',
  4: '16px',
  5: '20px',
  6: '24px',
  8: '32px',
  10: '40px',
  12: '48px',
  16: '64px',
} as const

export const shadows = {
  none: 'none',
  sm: '0 1px 2px rgba(0,0,0,0.05)',
  DEFAULT: '0 1px 3px rgba(0,0,0,0.1), 0 1px 2px rgba(0,0,0,0.06)',
  md: '0 4px 6px rgba(0,0,0,0.05)',
  lg: '0 10px 15px rgba(0,0,0,0.1), 0 4px 6px rgba(0,0,0,0.05)',
} as const

export const borderRadius = {
  none: '0',
  sm: '4px',
  DEFAULT: '6px',
  md: '8px',
  lg: '12px',    // v4.1: Containers grandes
  xl: '16px',
  '2xl': '20px',
  full: '9999px',
} as const

/**
 * v4: Classes utilitárias para hierarquia de texto
 * 
 * DS v4.1: Títulos e sidebar usam Open Sans (Source Serif 4 removido)
 */
export const textStyles = {
  // DS v4.1: Títulos com Open Sans
  h1: "font-['Open_Sans',sans-serif] text-2xl font-semibold text-gray-900 dark:text-gray-50",
  h2: "font-['Open_Sans',sans-serif] text-lg font-semibold text-gray-900 dark:text-gray-50",
  h3: "font-['Open_Sans',sans-serif] text-sm font-semibold text-gray-900 dark:text-gray-50",
  h4: "font-['Open_Sans',sans-serif] text-base-ui font-semibold text-gray-900 dark:text-gray-50",
  
  // Aliases para compatibilidade
  title: "font-['Open_Sans',sans-serif] text-base-ui font-semibold text-gray-900 dark:text-gray-50",
  titleLarge: "font-['Open_Sans',sans-serif] text-base font-semibold text-gray-900 dark:text-gray-50",
  titleXl: "font-['Open_Sans',sans-serif] text-2xl font-semibold text-gray-900 dark:text-gray-50",
  
  // v4: Subtítulos
  subtitle: "font-['Open_Sans',sans-serif] text-xs font-medium text-gray-800 dark:text-gray-200",
  subtitleMuted: "font-['Open_Sans',sans-serif] text-xs font-medium text-gray-600 dark:text-gray-400",
  
  // v4: Corpo de texto
  body: "font-['Open_Sans',sans-serif] text-xs font-normal text-gray-800 dark:text-gray-200",
  bodySmall: "font-['Open_Sans',sans-serif] text-xs font-normal text-gray-800 dark:text-gray-200",
  bodyLarge: "font-['Open_Sans',sans-serif] text-base-ui font-normal text-gray-800 dark:text-gray-200",
  
  // v4: Descrições secundárias
  description: "font-['Open_Sans',sans-serif] text-xs font-normal text-gray-600 dark:text-gray-400",
  
  // v4: Captions e labels
  caption: "font-['Open_Sans',sans-serif] text-micro font-normal text-gray-600 dark:text-gray-400",
  captionBold: "font-['Open_Sans',sans-serif] text-micro font-medium text-gray-800 dark:text-gray-200",
  
  // v4: Labels
  label: "font-['Open_Sans',sans-serif] text-xs font-medium text-gray-800 dark:text-gray-200",
  labelSmall: "font-['Open_Sans',sans-serif] text-micro font-medium text-gray-800 dark:text-gray-200",
  
  // v4: Métricas com Inter
  metric: "font-['Inter',sans-serif] text-sm font-semibold text-gray-900 dark:text-gray-50 tabular-nums",
  metricLarge: "font-['Inter',sans-serif] text-2xl font-semibold text-gray-900 dark:text-gray-50 tabular-nums",
  metricSmall: "font-['Inter',sans-serif] text-xs font-medium text-gray-800 dark:text-gray-200 tabular-nums",
  
  // DS v4.1: Sidebar com Open Sans (Source Serif 4 removido)
  sidebarTitle: "font-['Open_Sans',sans-serif] text-base-ui font-semibold text-gray-900 dark:text-gray-50",
  sidebarItem: "font-['Open_Sans',sans-serif] text-xs font-medium text-gray-700 dark:text-gray-300",
  sidebarItemActive: "font-['Open_Sans',sans-serif] text-xs font-semibold text-gray-900 dark:text-gray-50",
  
  // v4: Links (cyan para LIA/IA)
  link: "font-['Open_Sans',sans-serif] text-xs font-medium text-wedo-cyan hover:text-wedo-cyan-dark transition-colors",
  linkSubtle: "font-['Open_Sans',sans-serif] text-xs font-medium text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-50 transition-colors",
} as const

/**
 * v4.1: Classes utilitárias para Cards
 * Border-radius padrão: 8px (rounded-md) conforme DS v4.1
 */
export const cardStyles = {
  default: 'bg-white border border-gray-200 rounded-md dark:bg-gray-800 dark:border-gray-700',
  elevated: 'bg-white border border-gray-200 rounded-md dark:bg-gray-800 dark:border-gray-700',
  interactive: 'bg-white border border-gray-200 rounded-md hover:border-gray-300 transition-all duration-200 cursor-pointer dark:bg-gray-800 dark:border-gray-700 dark:hover:border-gray-600',
  selected: 'bg-white border-2 border-gray-900 rounded-md dark:bg-gray-800 dark:border-gray-50',
  flat: 'bg-gray-50 border border-gray-200 rounded-md dark:bg-gray-900 dark:border-gray-700',
  compact: 'bg-white border border-gray-200 rounded-md p-3 dark:bg-gray-800 dark:border-gray-700',
  expanded: 'bg-white border border-gray-200 rounded-md p-4 dark:bg-gray-800 dark:border-gray-700',
} as const

/**
 * v4: Classes utilitárias para Botões
 * IMPORTANTE: Primary é PRETO (gray-900), não mais cyan
 * Suporte completo a dark mode
 */
export const buttonStyles = {
  // v4.1: Primário é PRETO (inverte em dark mode) — rounded-md (8px)
  primary: 'bg-gray-900 hover:bg-gray-800 active:bg-gray-950 text-white font-semibold rounded-md px-4 py-2 transition-colors focus:ring-2 focus:ring-gray-900/20 focus:outline-none disabled:bg-gray-400 disabled:cursor-not-allowed dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200 dark:active:bg-gray-300',
  
  // v4.1: Secundário
  secondary: 'bg-gray-100 hover:bg-gray-200 active:bg-gray-300 text-gray-700 font-semibold rounded-md px-4 py-2 transition-colors focus:ring-2 focus:ring-gray-500/20 focus:outline-none dark:bg-gray-700 dark:text-gray-200 dark:hover:bg-gray-600',
  
  // v4.1: Outline
  outline: 'bg-transparent border border-gray-300 hover:bg-gray-50 hover:border-gray-400 text-gray-700 font-semibold rounded-md px-4 py-2 transition-colors focus:ring-2 focus:ring-gray-500/20 focus:outline-none dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-800 dark:hover:border-gray-500',
  
  // v4.1: Ghost
  ghost: 'bg-transparent hover:bg-gray-100 text-gray-600 font-medium rounded-md px-4 py-2 transition-colors focus:ring-2 focus:ring-gray-500/20 focus:outline-none dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-gray-200',
  
  // v4.1: Destructive
  destructive: 'bg-red-600 hover:bg-red-700 active:bg-red-800 text-white font-semibold rounded-md px-4 py-2 transition-colors focus:ring-2 focus:ring-red-600/20 focus:outline-none',
  
  // v4.1: Link style
  link: 'bg-transparent text-gray-600 hover:text-gray-900 font-medium rounded-md px-2 py-1 transition-colors underline-offset-4 hover:underline dark:text-gray-400 dark:hover:text-gray-50',
  
  // Aliases para compatibilidade
  danger: 'bg-red-600 hover:bg-red-700 text-white font-semibold rounded-md px-4 py-2 transition-colors',
  success: 'bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200 font-semibold rounded-md px-4 py-2 transition-colors',
} as const

/**
 * v4: Classes utilitárias para Inputs
 * Focus ring usa gray-900 (preto)
 */
export const inputStyles = {
  default: 'border border-gray-300 hover:border-gray-400 rounded-md px-3 py-2 text-base-ui font-normal text-gray-800 placeholder:text-gray-400 focus:ring-2 focus:ring-gray-900/10 focus:border-gray-900 outline-none transition-all',
  error: 'border border-red-500 rounded-md px-3 py-2 text-base-ui font-normal text-gray-800 focus:ring-2 focus:ring-red-500/10 focus:border-red-500 outline-none',
  success: 'border border-green-500 rounded-md px-3 py-2 text-base-ui font-normal text-gray-800 focus:ring-2 focus:ring-green-500/10 focus:border-green-500 outline-none',
  disabled: 'border border-gray-200 bg-gray-100 rounded-md px-3 py-2 text-base-ui font-normal text-gray-400 cursor-not-allowed',
} as const

/**
 * v4: Classes utilitárias para Badges
 * Cores semânticas padronizadas com suporte a dark mode
 */
export const badgeStyles = {
  // v4.1: Neutro/Default — rounded-full (pill) conforme DS v4.1
  default: 'inline-flex items-center px-2 py-0.5 rounded-full text-micro font-medium bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300',
  
  // v4.1: Estados semânticos com dark mode
  success: 'inline-flex items-center px-2 py-0.5 rounded-full text-micro font-medium bg-green-50 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  warning: 'inline-flex items-center px-2 py-0.5 rounded-full text-micro font-medium bg-amber-50 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
  error: 'inline-flex items-center px-2 py-0.5 rounded-full text-micro font-medium bg-red-50 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  info: 'inline-flex items-center px-2 py-0.5 rounded-full text-micro font-medium bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  
  // v4.1: WeDo accent colors (uso limitado - 10%) com dark mode
  cyan: 'inline-flex items-center px-2 py-0.5 rounded-full text-micro font-medium bg-wedo-cyan/10 text-wedo-cyan-dark dark:bg-wedo-cyan/20 dark:text-wedo-cyan',
  green: 'inline-flex items-center px-2 py-0.5 rounded-full text-micro font-medium bg-wedo-green/10 text-status-success dark:bg-wedo-green/20 dark:text-wedo-green',
  orange: 'inline-flex items-center px-2 py-0.5 rounded-full text-micro font-medium bg-wedo-orange/10 text-wedo-orange dark:bg-wedo-orange/20 dark:text-wedo-orange',
  purple: 'inline-flex items-center px-2 py-0.5 rounded-full text-micro font-medium bg-wedo-purple/10 text-wedo-purple dark:bg-wedo-purple/20 dark:text-wedo-purple',

  // Alias para compatibilidade
  primary: 'inline-flex items-center px-2 py-0.5 rounded-full text-micro font-medium bg-wedo-cyan/10 text-wedo-cyan-dark dark:bg-wedo-cyan/20 dark:text-wedo-cyan',
  
  // v4.1: Outline variants com dark mode
  outlineDefault: 'inline-flex items-center px-2 py-0.5 rounded-full text-micro font-medium bg-transparent border border-gray-300 text-gray-700 dark:border-gray-600 dark:text-gray-300',
  outlineSuccess: 'inline-flex items-center px-2 py-0.5 rounded-full text-micro font-medium bg-transparent border border-green-300 text-green-700 dark:border-green-700 dark:text-green-400',
  outlineWarning: 'inline-flex items-center px-2 py-0.5 rounded-full text-micro font-medium bg-transparent border border-amber-300 text-amber-700 dark:border-amber-700 dark:text-amber-400',
  outlineError: 'inline-flex items-center px-2 py-0.5 rounded-full text-micro font-medium bg-transparent border border-red-300 text-red-700 dark:border-red-700 dark:text-red-400',
} as const

/**
 * v4: Classes utilitárias para Tabs
 * Dois estilos: underline (tradicional) e pill (badges arredondadas)
 */
export const tabStyles = {
  // Estilo underline (tradicional)
  container: 'flex border-b border-gray-200 dark:border-gray-700',
  tab: 'px-4 py-2 text-xs font-medium text-gray-600 hover:text-gray-900 border-b-2 border-transparent hover:border-gray-300 transition-colors cursor-pointer dark:text-gray-400 dark:hover:text-gray-200',
  tabActive: 'px-4 py-2 text-xs font-semibold text-gray-900 border-b-2 border-gray-900 dark:text-gray-50 dark:border-gray-50',
  tabDisabled: 'px-4 py-2 text-xs font-medium text-gray-400 cursor-not-allowed',
  
  // Estilo pill (badges arredondadas) - PADRÃO para Settings hubs
  pillContainer: 'flex items-center gap-1 flex-wrap',
  pill: "inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-colors cursor-pointer font-['Open_Sans',sans-serif] text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800",
  pillActive: "inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-colors cursor-pointer font-['Open_Sans',sans-serif] bg-gray-900 text-white dark:bg-gray-50 dark:text-gray-900",
  pillIcon: 'w-3.5 h-3.5',
} as const

/**
 * v4: Classes utilitárias para Botões de Ação
 * Tamanhos padronizados para botões Editar, Salvar, Exportar, etc.
 */
export const actionButtonStyles = {
  // Botões pequenos para ações inline
  sm: "inline-flex items-center gap-1.5 py-1.5 px-2.5 text-xs font-medium rounded-md transition-colors",
  smPrimary: "inline-flex items-center gap-1.5 py-1.5 px-2.5 text-xs font-medium rounded-md transition-colors bg-gray-900 text-white hover:bg-gray-800 dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200 disabled:opacity-50",
  smSecondary: "inline-flex items-center gap-1.5 py-1.5 px-2.5 text-xs font-medium rounded-md transition-colors border border-gray-300 bg-white text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700 disabled:opacity-50",
  smOutline: "inline-flex items-center gap-1.5 py-1.5 px-2.5 text-xs font-medium rounded-md transition-colors border border-gray-300 bg-transparent text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-800",
  // Ícones padrão para botões de ação
  icon: 'w-3.5 h-3.5',
} as const

/**
 * v4: Classes utilitárias para Modais
 */
export const modalStyles = {
  overlay: 'fixed inset-0 bg-black/50 backdrop-blur-[1px] z-50',
  container: 'bg-white border border-gray-200 rounded-md',
  header: 'px-6 py-4 border-b border-gray-200',
  headerTitle: "font-['Open_Sans',sans-serif] text-base font-semibold text-gray-900",
  body: 'px-6 py-4',
  footer: 'px-6 py-4 border-t border-gray-200 flex justify-end gap-3',
} as const

/**
 * v4: Classes utilitárias para estados de formulário
 */
export const formStyles = {
  fieldGroup: 'space-y-1.5',
  label: "font-['Open_Sans',sans-serif] text-xs font-medium text-gray-700",
  labelRequired: "font-['Open_Sans',sans-serif] text-xs font-medium text-gray-700 after:content-['*'] after:ml-0.5 after:text-red-500",
  helperText: "font-['Open_Sans',sans-serif] text-micro font-normal text-gray-500 mt-1",
  errorText: "font-['Open_Sans',sans-serif] text-micro font-normal text-red-600 mt-1",
} as const

/**
 * v4: Mapeamento Tailwind → Vuetify 3 para migração futura
 */
export const tailwindToVuetify = {
  colors: {
    'bg-gray-900': 'color="grey-darken-4"',
    'bg-gray-100': 'class="bg-grey-lighten-4"',
    'bg-gray-50': 'class="bg-grey-lighten-5"',
    'border-gray-200': 'class="border-grey-lighten-3"',
    'border-gray-300': 'class="border-grey-lighten-2"',
    'text-gray-900': 'class="text-grey-darken-4"',
    'text-gray-800': 'class="text-grey-darken-3"',
    'text-gray-600': 'class="text-grey-darken-1"',
    'text-gray-500': 'class="text-grey"',
    'border': 'elevation="0"',
  },
  
  typography: {
    // text-xs = 11px neste projeto → Vuetify text-caption (≈12px)
    'text-xs font-medium':        'class="text-caption font-weight-medium"',
    'text-xs font-normal':        'class="text-caption"',
    // text-micro = 10px → Vuetify text-overline (10px, exato)
    'text-micro font-normal':     'class="text-overline"',
    'text-micro font-medium':     'class="text-overline font-weight-medium"',
    // text-sm-ui = 12px → Vuetify text-caption (12px, exato)
    'text-sm-ui font-normal':     'class="text-caption"',
    'text-sm-ui font-medium':     'class="text-caption font-weight-medium"',
    // text-base-ui = 13px → Vuetify text-body-2 (≈14px)
    'text-base-ui font-semibold': 'class="text-subtitle-2 font-weight-bold"',
    'text-base-ui font-normal':   'class="text-body-2"',
    // text-sm = 14px → Vuetify text-body-2 (14px, exato)
    'text-sm font-normal':        'class="text-body-2"',
    'text-sm font-medium':        'class="text-body-2 font-weight-medium"',
    // Legado — manter como referência durante migração
    'text-[13px] font-semibold':  'class="text-subtitle-2 font-weight-bold"',
    'text-[11px] font-normal':    'class="text-caption"',
    'text-[10px] font-normal':    'class="text-overline"',
  },
  
  spacing: {
    'p-2': 'class="pa-2"',
    'p-3': 'class="pa-3"',
    'p-4': 'class="pa-4"',
    'p-6': 'class="pa-6"',
    'px-4': 'class="px-4"',
    'py-2': 'class="py-2"',
    'gap-2': 'style="gap: 8px"',
    'gap-3': 'style="gap: 12px"',
    'gap-4': 'style="gap: 16px"',
  },
  
  layout: {
    'flex': 'class="d-flex"',
    'flex items-center': 'class="d-flex align-center"',
    'flex justify-between': 'class="d-flex justify-space-between"',
    'flex justify-center': 'class="d-flex justify-center"',
    'flex flex-col': 'class="d-flex flex-column"',
    'flex-1': 'class="flex-grow-1"',
    'flex-wrap': 'class="flex-wrap"',
    'grid': 'class="d-grid"',
  },
  
  components: {
    Card: '<v-card variant="outlined" rounded="xl">',
    CardInteractive: '<v-card variant="outlined" hover rounded="xl">',
    Button: '<v-btn color="grey-darken-4" variant="flat">',
    ButtonSecondary: '<v-btn color="grey-lighten-4" variant="flat">',
    ButtonOutline: '<v-btn variant="outlined">',
    ButtonGhost: '<v-btn variant="text">',
    Input: '<v-text-field variant="outlined" density="compact">',
    Badge: '<v-chip size="small" variant="tonal">',
    Modal: '<v-dialog> com <v-card rounded="xl"> interno',
    Tabs: '<v-tabs density="compact">',
    Tab: '<v-tab>',
    Tooltip: '<v-tooltip location="top">',
  },
  
  notes: {
    primaryColor: 'Em Vuetify, configure grey-darken-4 (#111827) como cor primária para botões',
    typography: 'Configure Open Sans como fonte padrão no theme do Vuetify',
    borderRadius: 'Use rounded="md" (8px) para botões/inputs/cards/modais, rounded="pill" para badges/tabs conforme DS v4.1',
    elevation: 'Sem sombras — usar bordas (border border-gray-200) para separação visual',
  },
} as const

/**
 * v4: CSS Variables disponíveis
 */
export const cssVariables = {
  // Typography
  '--lia-font-primary': '"Open Sans", sans-serif',
  '--lia-font-data': '"Inter", sans-serif',
  '--lia-font-sidebar': '"Open Sans", sans-serif',
  
  // Colors - Primary (gray-900)
  '--lia-primary': colors.gray[900],
  '--lia-primary-hover': colors.gray[800],
  '--lia-primary-active': colors.gray[950],
  
  // Colors - Text
  '--lia-text-title': colors.gray[900],
  '--lia-text-body': colors.gray[800],
  '--lia-text-secondary': colors.gray[600],
  '--lia-text-muted': colors.gray[500],
  
  // Colors - Borders
  '--lia-border-light': colors.border.light,
  '--lia-border-default': colors.border.default,
  '--lia-border-medium': colors.border.medium,
  
  // Colors - Background
  '--lia-bg-primary': colors.background.primary,
  '--lia-bg-secondary': colors.background.secondary,
  
  // Colors - WeDo accent
  '--wedo-cyan': colors.wedo.cyan,
  '--wedo-green': colors.wedo.green,
  '--wedo-orange': colors.wedo.orange,
  '--wedo-purple': colors.wedo.purple,
  '--wedo-magenta': colors.wedo.magenta,
  
  // Shadows (deprecated — flat design, usar bordas)
  '--lia-shadow-sm': 'none',
  '--lia-shadow-default': 'none',
  '--lia-shadow-md': 'none',
  
  // Border radius
  '--lia-radius-sm': borderRadius.sm,
  '--lia-radius-default': borderRadius.DEFAULT,
  '--lia-radius-lg': borderRadius.lg,
} as const

/**
 * Helper function para aplicar múltiplos estilos
 */
export function cn(...classes: (string | undefined | null | false)[]): string {
  return classes.filter(Boolean).join(' ')
}

/**
 * v4: Score color helper - retorna cor baseada no score
 */
export function getScoreColor(score: number, type: 'lia' | 'wsi' = 'lia'): {
  text: string
  bg: string
  border: string
} {
  if (type === 'wsi') {
    if (score >= 4.0) return { text: 'text-green-700', bg: 'bg-green-50', border: 'border-green-200' }
    if (score >= 3.0) return { text: 'text-amber-700', bg: 'bg-amber-50', border: 'border-amber-200' }
    return { text: 'text-red-700', bg: 'bg-red-50', border: 'border-red-200' }
  }
  
  if (score >= 80) return { text: 'text-green-700', bg: 'bg-green-50', border: 'border-green-200' }
  if (score >= 60) return { text: 'text-amber-700', bg: 'bg-amber-50', border: 'border-amber-200' }
  return { text: 'text-red-700', bg: 'bg-red-50', border: 'border-red-200' }
}

/**
 * v4: Status badge helper - retorna estilo baseado no status
 */
export function getStatusStyle(status: string): {
  text: string
  bg: string
  label: string
} {
  const statusMap: Record<string, { text: string; bg: string; label: string }> = {
    'active': { text: 'text-green-700', bg: 'bg-green-50', label: 'Ativo' },
    'ativa': { text: 'text-green-700', bg: 'bg-green-50', label: 'Ativa' },
    'approved': { text: 'text-green-700', bg: 'bg-green-50', label: 'Aprovado' },
    'aprovado': { text: 'text-green-700', bg: 'bg-green-50', label: 'Aprovado' },
    'completed': { text: 'text-green-700', bg: 'bg-green-50', label: 'Concluído' },
    'pending': { text: 'text-amber-700', bg: 'bg-amber-50', label: 'Pendente' },
    'pendente': { text: 'text-amber-700', bg: 'bg-amber-50', label: 'Pendente' },
    'waiting': { text: 'text-amber-700', bg: 'bg-amber-50', label: 'Aguardando' },
    'aguardando': { text: 'text-amber-700', bg: 'bg-amber-50', label: 'Aguardando' },
    'inactive': { text: 'text-gray-600', bg: 'bg-gray-100', label: 'Inativo' },
    'inativa': { text: 'text-gray-600', bg: 'bg-gray-100', label: 'Inativa' },
    'draft': { text: 'text-gray-600', bg: 'bg-gray-100', label: 'Rascunho' },
    'rascunho': { text: 'text-gray-600', bg: 'bg-gray-100', label: 'Rascunho' },
    'error': { text: 'text-red-700', bg: 'bg-red-50', label: 'Erro' },
    'erro': { text: 'text-red-700', bg: 'bg-red-50', label: 'Erro' },
    'rejected': { text: 'text-red-700', bg: 'bg-red-50', label: 'Rejeitado' },
    'rejeitado': { text: 'text-red-700', bg: 'bg-red-50', label: 'Rejeitado' },
    'cancelled': { text: 'text-red-700', bg: 'bg-red-50', label: 'Cancelado' },
    'cancelado': { text: 'text-red-700', bg: 'bg-red-50', label: 'Cancelado' },
  }
  
  const key = status.toLowerCase()
  return statusMap[key] || { text: 'text-gray-700', bg: 'bg-gray-100', label: status }
}

/**
 * Recommendation badge helper
 */
export function getRecommendationStyle(recommendation: string): {
  text: string
  bg: string
  label: string
} {
  switch (recommendation.toUpperCase()) {
    case 'APPROVED':
    case 'APROVADO':
      return { text: 'text-green-700', bg: 'bg-green-50', label: 'APROVADO' }
    case 'PENDING':
    case 'PENDENTE':
      return { text: 'text-amber-700', bg: 'bg-amber-50', label: 'PENDENTE' }
    case 'NOT_APPROVED':
    case 'NAO_APROVADO':
    case 'NÃO APROVADO':
      return { text: 'text-red-700', bg: 'bg-red-50', label: 'NÃO APROVADO' }
    default:
      return { text: 'text-gray-700', bg: 'bg-gray-100', label: recommendation }
  }
}

/**
 * Formata um score percentual com o número correto de casas decimais
 */
export function formatScore(score: number | string | null | undefined, decimals: number = 1): string {
  if (score === null || score === undefined) return '0'
  const numScore = typeof score === 'string' ? parseFloat(score) : score
  if (isNaN(numScore)) return '0'
  return numScore.toFixed(decimals)
}

/**
 * Formata um score percentual com símbolo de porcentagem
 */
export function formatScorePercent(score: number | string | null | undefined, decimals: number = 1): string {
  return `${formatScore(score, decimals)}%`
}

export default {
  colors,
  typography,
  spacing,
  shadows,
  borderRadius,
  textStyles,
  cardStyles,
  buttonStyles,
  inputStyles,
  badgeStyles,
  tabStyles,
  modalStyles,
  formStyles,
  tailwindToVuetify,
  cssVariables,
  cn,
  getScoreColor,
  getStatusStyle,
  getRecommendationStyle,
  formatScore,
  formatScorePercent,
}
