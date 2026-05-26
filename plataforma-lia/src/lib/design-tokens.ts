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
 * - Botões primários: bg-lia-btn-primary-bg (preto)
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
    hover: 'var(--lia-text-primary)',   // v4: gray-800
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
    200: 'var(--lia-border-subtle)',
    300: 'var(--lia-border-default)',
    400: 'var(--lia-text-tertiary)',
    500: 'var(--lia-text-secondary)',
    600: 'var(--lia-text-secondary)',
    700: '#374151',
    800: 'var(--lia-text-primary)',
    900: '#111827',
    950: '#030712',
  },
  
  text: {
    light: {
      title: '#111827',       // v4: gray-900 - Títulos principais
      body: 'var(--lia-text-primary)',        // gray-800 - Texto principal, labels
      secondary: 'var(--lia-text-secondary)',   // gray-600 - Descrições, captions
      muted: 'var(--lia-text-secondary)',       // gray-500 - Placeholders, disabled
    },
    dark: {
      title: '#F9FAFB',       // gray-50 - Títulos principais
      body: 'var(--lia-border-subtle)',        // gray-200 - Texto principal, labels
      secondary: 'var(--lia-text-tertiary)',   // gray-400 - Descrições, captions
      muted: 'var(--lia-text-secondary)',       // gray-500 - Placeholders, disabled
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
    default: 'var(--lia-border-subtle)',  // gray-200
    medium: 'var(--lia-border-default)',   // gray-300
    dark: 'var(--lia-text-tertiary)',     // gray-400
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
    sm: '12px',
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
  h1: "font-sans text-2xl font-semibold text-lia-text-primary dark:text-lia-text-primary",
  h2: "font-sans text-lg font-semibold text-lia-text-primary dark:text-lia-text-primary",
  h3: "font-sans text-sm font-semibold text-lia-text-primary dark:text-lia-text-primary",
  h4: "font-sans text-base-ui font-semibold text-lia-text-primary dark:text-lia-text-primary",
  
  // Aliases para compatibilidade
  title: "font-sans text-base-ui font-semibold text-lia-text-primary dark:text-lia-text-primary",
  titleLarge: "font-sans text-base font-semibold text-lia-text-primary dark:text-lia-text-primary",
  titleXl: "font-sans text-2xl font-semibold text-lia-text-primary dark:text-lia-text-primary",
  
  // v4: Subtítulos
  subtitle: "font-sans text-xs font-medium text-lia-text-primary dark:text-lia-text-primary",
  subtitleMuted: "font-sans text-xs font-medium text-lia-text-secondary dark:text-lia-text-secondary",
  
  // v4: Corpo de texto
  body: "font-sans text-xs font-normal text-lia-text-primary dark:text-lia-text-primary",
  bodySmall: "font-sans text-xs font-normal text-lia-text-primary dark:text-lia-text-primary",
  bodyLarge: "font-sans text-base-ui font-normal text-lia-text-primary dark:text-lia-text-primary",
  
  // v4: Descrições secundárias
  description: "font-sans text-xs font-normal text-lia-text-secondary dark:text-lia-text-secondary",
  
  // v4: Captions e labels
  caption: "font-sans text-micro font-normal text-lia-text-secondary dark:text-lia-text-secondary",
  captionBold: "font-sans text-micro font-medium text-lia-text-primary dark:text-lia-text-primary",
  
  // v4: Labels
  label: "font-sans text-xs font-medium text-lia-text-primary dark:text-lia-text-primary",
  labelSmall: "font-sans text-micro font-medium text-lia-text-primary dark:text-lia-text-primary",
  
  // v4: Métricas com Inter
  metric: "font-sans text-sm font-semibold text-lia-text-primary dark:text-lia-text-primary tabular-nums",
  metricLarge: "font-sans text-2xl font-semibold text-lia-text-primary dark:text-lia-text-primary tabular-nums",
  metricSmall: "font-sans text-xs font-medium text-lia-text-primary dark:text-lia-text-primary tabular-nums",
  
  // DS v4.1: Sidebar com Open Sans (Source Serif 4 removido)
  sidebarTitle: "font-sans text-base-ui font-semibold text-lia-text-primary dark:text-lia-text-primary",
  sidebarItem: "font-sans text-xs font-medium text-lia-text-secondary dark:text-lia-text-secondary",
  sidebarItemActive: "font-sans text-xs font-semibold text-lia-text-primary dark:text-lia-text-primary",
  
  // v4: Links (cyan para LIA/IA)
  link: "font-sans text-xs font-medium text-wedo-cyan hover:text-wedo-cyan-dark transition-colors",
  linkSubtle: "font-sans text-xs font-medium text-lia-text-secondary hover:text-lia-text-primary dark:text-lia-text-secondary dark:hover:text-lia-text-inverse transition-colors",
} as const

/**
 * v4.1: Classes utilitárias para Cards
 * Border-radius padrão: 8px (rounded-md) conforme DS v4.1
 */
export const cardStyles = {
  default: 'bg-lia-bg-primary border border-lia-border-subtle rounded-md dark:bg-lia-bg-secondary dark:border-lia-border-subtle',
  elevated: 'bg-lia-bg-secondary border border-lia-border-subtle rounded-md dark:bg-lia-bg-tertiary dark:border-lia-border-subtle',
  interactive: 'bg-lia-bg-primary border border-lia-border-subtle rounded-md hover:border-lia-border-default transition-colors duration-200 cursor-pointer dark:bg-lia-bg-secondary dark:border-lia-border-subtle dark:hover:border-lia-border-medium',
  selected: 'bg-lia-bg-primary border-2 border-lia-btn-primary-bg rounded-md dark:bg-lia-bg-secondary dark:border-lia-border-medium',
  flat: 'bg-lia-bg-secondary border border-lia-border-subtle rounded-md dark:bg-lia-bg-primary dark:border-lia-border-subtle',
  compact: 'bg-lia-bg-primary border border-lia-border-subtle rounded-md p-3 dark:bg-lia-bg-secondary dark:border-lia-border-subtle',
  expanded: 'bg-lia-bg-primary border border-lia-border-subtle rounded-md p-4 dark:bg-lia-bg-secondary dark:border-lia-border-subtle',
} as const

/**
 * v4: Classes utilitárias para Botões
 * IMPORTANTE: Primary é PRETO (gray-900), não mais cyan
 * Suporte completo a dark mode
 */
export const buttonStyles = {
  // v4.1: Primário é PRETO (inverte em dark mode) — rounded-md (8px)
  primary: 'bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover active:bg-lia-btn-primary-bg text-lia-btn-primary-text font-semibold rounded-md px-4 py-2 transition-colors focus:ring-2 focus:ring-lia-btn-primary-bg/20 focus:outline-none disabled:bg-lia-border-medium disabled:cursor-not-allowed dark:bg-lia-bg-secondary dark:text-lia-text-disabled dark:hover:bg-lia-interactive-active dark:active:bg-lia-border-default',
  
  // v4.1: Secundário
  secondary: 'bg-lia-bg-tertiary hover:bg-lia-interactive-active active:bg-lia-border-default text-lia-text-secondary font-semibold rounded-md px-4 py-2 transition-colors focus:ring-2 focus:ring-lia-border-medium/20 focus:outline-none dark:bg-lia-bg-tertiary dark:text-lia-text-primary dark:hover:bg-lia-border-medium',
  
  // v4.1: Outline
  outline: 'bg-transparent border border-lia-border-default hover:bg-lia-bg-secondary hover:border-lia-border-medium text-lia-text-secondary font-semibold rounded-md px-4 py-2 transition-colors focus:ring-2 focus:ring-lia-border-medium/20 focus:outline-none dark:border-lia-border-default dark:text-lia-text-secondary dark:hover:bg-lia-btn-primary-hover dark:hover:border-lia-border-medium',
  
  // v4.1: Ghost
  ghost: 'bg-transparent hover:bg-lia-bg-tertiary text-lia-text-secondary font-medium rounded-md px-4 py-2 transition-colors focus:ring-2 focus:ring-lia-border-medium/20 focus:outline-none dark:text-lia-text-secondary dark:hover:bg-lia-btn-primary-hover dark:hover:text-lia-text-inverse',
  
  // v4.1: Destructive
  destructive: 'bg-status-error hover:bg-status-error active:bg-status-error text-white font-semibold rounded-md px-4 py-2 transition-colors focus:ring-2 focus:ring-status-error/20 focus:outline-none',
  
  // v4.1: Link style
  link: 'bg-transparent text-lia-text-secondary hover:text-lia-text-primary font-medium rounded-md px-2 py-1 transition-colors underline-offset-4 hover:underline dark:text-lia-text-secondary dark:hover:text-lia-text-inverse',
  
  // Aliases para compatibilidade
  danger: 'bg-status-error hover:bg-status-error text-white font-semibold rounded-md px-4 py-2 transition-colors',
  success: 'bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:bg-lia-bg-secondary dark:text-lia-text-disabled dark:hover:bg-lia-interactive-active font-semibold rounded-md px-4 py-2 transition-colors',
} as const

/**
 * v4: Classes utilitárias para Inputs
 * Focus ring usa gray-900 (preto)
 */
export const inputStyles = {
  default: 'border border-lia-border-default hover:border-lia-border-medium rounded-md px-3 py-2 text-base-ui font-normal text-lia-text-primary placeholder:text-lia-text-disabled focus:ring-2 focus:ring-lia-btn-primary-bg/10 focus:border-lia-btn-primary-bg outline-none transition-colors',
  error: 'border border-status-error/30 rounded-md px-3 py-2 text-base-ui font-normal text-lia-text-primary focus:ring-2 focus:ring-red-500/10 focus:border-status-error/30 outline-none',
  success: 'border border-status-success/30 rounded-md px-3 py-2 text-base-ui font-normal text-lia-text-primary focus:ring-2 focus:ring-green-500/10 focus:border-status-success/30 outline-none',
  disabled: 'border border-lia-border-subtle bg-lia-bg-tertiary rounded-md px-3 py-2 text-base-ui font-normal text-lia-text-disabled cursor-not-allowed',
} as const

/**
 * v4: Classes utilitárias para Badges
 * Cores semânticas padronizadas com suporte a dark mode
 */
export const badgeStyles = {
  // v4.1: Neutro/Default — rounded-full (pill) conforme DS v4.1
  default: 'inline-flex items-center px-2 py-0.5 rounded-full text-micro font-medium bg-lia-bg-tertiary text-lia-text-secondary dark:bg-lia-bg-secondary dark:text-lia-text-secondary',
  
  // v4.1: Estados semânticos com dark mode
  success: 'inline-flex items-center px-2 py-0.5 rounded-full text-micro font-medium bg-status-success/10 text-status-success dark:bg-status-success/30 dark:text-status-success',
  warning: 'inline-flex items-center px-2 py-0.5 rounded-full text-micro font-medium bg-status-warning/10 text-status-warning dark:bg-status-warning/30 dark:text-status-warning',
  error: 'inline-flex items-center px-2 py-0.5 rounded-full text-micro font-medium bg-status-error/10 text-status-error dark:bg-status-error/30 dark:text-status-error',
  info: 'inline-flex items-center px-2 py-0.5 rounded-full text-micro font-medium bg-wedo-cyan/10 text-wedo-cyan-dark dark:text-wedo-cyan-dark',
  
  // v4.1: WeDo accent colors (uso limitado - 10%) com dark mode
  cyan: 'inline-flex items-center px-2 py-0.5 rounded-full text-micro font-medium bg-wedo-cyan/10 text-wedo-cyan-dark dark:bg-wedo-cyan/20 dark:text-wedo-cyan',
  green: 'inline-flex items-center px-2 py-0.5 rounded-full text-micro font-medium bg-wedo-green/10 text-status-success dark:bg-wedo-green/20 dark:text-wedo-green',
  orange: 'inline-flex items-center px-2 py-0.5 rounded-full text-micro font-medium bg-wedo-orange/10 text-wedo-orange dark:bg-wedo-orange/20 dark:text-wedo-orange',
  purple: 'inline-flex items-center px-2 py-0.5 rounded-full text-micro font-medium bg-wedo-purple/10 text-wedo-purple dark:bg-wedo-purple/20 dark:text-wedo-purple',

  // Alias para compatibilidade
  primary: 'inline-flex items-center px-2 py-0.5 rounded-full text-micro font-medium bg-wedo-cyan/10 text-wedo-cyan-dark dark:bg-wedo-cyan/20 dark:text-wedo-cyan',
  
  // v4.1: Outline variants com dark mode
  outlineDefault: 'inline-flex items-center px-2 py-0.5 rounded-full text-micro font-medium bg-transparent border border-lia-border-default text-lia-text-secondary dark:border-lia-border-default dark:text-lia-text-secondary',
  outlineSuccess: 'inline-flex items-center px-2 py-0.5 rounded-full text-micro font-medium bg-transparent border border-status-success/30 text-status-success dark:border-status-success/30 dark:text-status-success',
  outlineWarning: 'inline-flex items-center px-2 py-0.5 rounded-full text-micro font-medium bg-transparent border border-status-warning/30 text-status-warning dark:border-status-warning/30 dark:text-status-warning',
  outlineError: 'inline-flex items-center px-2 py-0.5 rounded-full text-micro font-medium bg-transparent border border-status-error/30 text-status-error dark:border-status-error/30 dark:text-status-error',
} as const

/**
 * v4.2.2: Chip canônico para o painel de Preview de Candidato/Vaga.
 *
 * Fonte da verdade: o chip "LGPD" em CandidatePreviewHeader (text-micro 11px,
 * h-4 = 16px, px-1.5, py-0). Todo Chip de metadado dentro de
 * `candidate-preview/*` (seniority, anos, archetype, proficiência de idioma,
 * preferências, status de atividade, skills, etc.) DEVE compor a partir deste
 * token. Antes desta canonicalização, alguns chips usavam `badgeStyles.X`
 * (px-2 py-0.5) ou `text-xs` (13px), que destoavam visualmente do canônico.
 *
 * Uso:
 *   <Chip variant="neutral" muted className={previewChipClasses}>...</Chip>
 *   <Chip variant="neutral" muted className={cn(previewChipClasses, 'bg-X')}>...</Chip>
 *
 * Para variantes semânticas com cor + borda inclusas, ver `previewChipVariants`.
 */
// F11 Bug 3 (2026-05-24): adicionado `flex items-center` para alinhar baseline
// idêntica ao chip LGPD canonical (`text-micro px-1.5 py-0 h-4 flex items-center
// gap-0.5`). Sem flex explícito, o Chip baseline `inline-flex` cria differential
// vertical alignment quando outras classes (h-4 + py-0) competem com line-height,
// resultando em chips visualmente ~4px mais altos que o LGPD nos screenshots.
export const previewChipClasses = 'text-micro px-1.5 py-0 h-4 flex items-center' as const

export const previewChipVariants = {
  neutral:
    'text-micro px-1.5 py-0 h-4 flex items-center bg-lia-bg-tertiary text-lia-text-secondary dark:bg-lia-bg-secondary dark:text-lia-text-secondary',
  success:
    'text-micro px-1.5 py-0 h-4 flex items-center bg-status-success/10 text-status-success dark:bg-status-success/30 dark:text-status-success',
  warning:
    'text-micro px-1.5 py-0 h-4 flex items-center bg-status-warning/10 text-status-warning dark:bg-status-warning/30 dark:text-status-warning',
  error:
    'text-micro px-1.5 py-0 h-4 flex items-center bg-status-error/10 text-status-error dark:bg-status-error/30 dark:text-status-error',
} as const

/**
 * v4: Classes utilitárias para Tabs
 * Dois estilos: underline (tradicional) e pill (badges arredondadas)
 */
export const tabStyles = {
  // Estilo underline (tradicional)
  container: 'flex border-b border-lia-border-subtle dark:border-lia-border-subtle',
  tab: 'px-4 py-2 text-xs font-medium text-lia-text-secondary hover:text-lia-text-primary border-b-2 border-transparent hover:border-lia-border-default transition-colors cursor-pointer dark:text-lia-text-secondary dark:hover:text-lia-text-inverse',
  tabActive: 'px-4 py-2 text-xs font-semibold text-lia-text-primary border-b-2 border-lia-btn-primary-bg dark:text-lia-text-primary dark:border-lia-border-medium',
  tabDisabled: 'px-4 py-2 text-xs font-medium text-lia-text-disabled cursor-not-allowed',
  
  pillContainer: 'flex gap-1 p-1 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-lg w-fit',
  pill: "inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors cursor-pointer font-sans text-lia-text-secondary hover:bg-lia-bg-tertiary dark:text-lia-text-secondary dark:hover:bg-lia-btn-primary-hover",
  pillActive: "inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors cursor-pointer font-sans bg-lia-bg-primary text-lia-text-primary shadow-sm dark:bg-lia-bg-primary dark:text-lia-text-primary",
  pillIcon: 'w-3.5 h-3.5',
} as const

/**
 * v4.2: Toolbar canônica (vagas + candidatos)
 * Usado por <ViewToggle /> e <ToolbarButton /> em src/components/ui.
 */
export const toolbarStyles = {
  // Container do toggle de visualização (pílula segmentada)
  viewToggleContainer: 'inline-flex items-center bg-lia-bg-tertiary dark:bg-lia-bg-elevated rounded-lg',
  viewToggleContainerPad: {
    sm: 'p-0.5 gap-0.5',
    md: 'p-0.5 gap-0.5',
  },
  // Itens do toggle
  viewToggleItemBase:
    'inline-flex items-center justify-center rounded-md font-medium transition-colors motion-reduce:transition-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-lia-btn-primary-bg/20 dark:focus-visible:ring-lia-border-subtle/20',
  viewToggleItemSize: {
    sm: 'h-6 px-2 text-xs gap-1',
    md: 'h-7 px-2.5 text-xs gap-1.5',
    iconSm: 'h-7 w-7 text-xs',
    iconMd: 'h-8 w-8 text-xs',
  },
  viewToggleItemActive: 'bg-lia-bg-primary dark:bg-lia-bg-secondary text-lia-text-primary shadow-sm',
  viewToggleItemInactive:
    'text-lia-text-secondary hover:text-lia-text-primary dark:hover:text-lia-text-inverse',
  viewToggleIcon: {
    sm: 'w-3 h-3',
    md: 'w-3.5 h-3.5',
  },

  // Botões de toolbar (pílula rounded-full)
  toolbarBtnBase:
    'inline-flex items-center justify-center font-medium rounded-full transition-colors motion-reduce:transition-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-lia-btn-primary-bg/20 dark:focus-visible:ring-lia-border-subtle/20 disabled:opacity-50 disabled:cursor-not-allowed',
  toolbarBtnSize: {
    sm: 'h-7 px-3 text-xs gap-1.5',
    md: 'h-8 px-4 text-xs gap-2',
  },
  toolbarBtnActive:
    'bg-lia-btn-primary-bg text-lia-btn-primary-text hover:bg-lia-btn-primary-hover dark:bg-lia-bg-secondary dark:hover:bg-lia-interactive-active',
  toolbarBtnDefault:
    'bg-lia-bg-primary text-lia-text-primary border border-lia-border-subtle dark:bg-lia-bg-secondary dark:border-lia-border-default hover:bg-lia-bg-secondary dark:hover:bg-lia-bg-inverse',
} as const

/**
 * v4.2: Header de coluna do Kanban (vagas + candidatos)
 * Usado por <KanbanColumnHeader /> em src/components/pages/job-kanban.
 *
 * Densidades:
 * - `md`: kanban de vagas (página /jobs) — roomier.
 * - `sm`: kanban de candidatos dentro de uma vaga — denser.
 */
export const kanbanColumnHeaderStyles = {
  padding: {
    sm: 'p-2.5 pb-1.5',
    md: 'p-3',
  },
  titleGap: {
    sm: 'gap-1.5',
    md: 'gap-2',
  },
  dotSize: {
    sm: 'w-2 h-2',
    md: 'w-3 h-3',
  },
  title: {
    sm: "font-sans font-medium text-xs text-lia-text-primary dark:text-lia-text-primary",
    md: "font-sans font-medium text-sm text-lia-text-primary dark:text-lia-text-primary",
  },
  count: {
    sm: 'inline-flex items-center text-micro text-lia-text-primary bg-lia-bg-tertiary dark:bg-lia-bg-secondary px-1.5 py-0.5 rounded-full',
    md: 'inline-flex items-center text-micro text-lia-text-secondary bg-lia-bg-tertiary dark:bg-lia-bg-secondary px-2 py-0.5 rounded-full ml-1',
  },
  subtitle:
    "mt-1 font-sans text-micro font-normal text-lia-text-secondary dark:text-lia-text-secondary",
} as const

/**
 * v4.2: Card canônico do Kanban (vagas + candidatos)
 * Usado por <KanbanCardShell /> e <KanbanChip /> em src/components/pages/job-kanban.
 *
 * Densidades:
 * - `comfortable`: kanban de vagas (página /jobs).
 * - `compact`:    kanban de candidatos dentro de uma vaga.
 *
 * Tokens fixos garantem que ambos os contextos compartilhem fundo,
 * borda, raio, hover e tipografia, variando apenas a escala.
 */
export const kanbanCardStyles = {
  shell:
    'group relative overflow-hidden bg-lia-bg-primary dark:bg-lia-bg-secondary border border-lia-border-subtle dark:border-lia-border-subtle rounded-xl transition-colors motion-reduce:transition-none',
  shellInteractive:
    'hover:border-lia-border-default dark:hover:border-lia-border-medium',
  body: {
    comfortable: 'p-3',
    compact: 'p-2',
  },
  bodyGap: {
    comfortable: 'gap-2',
    compact: 'gap-1.5',
  },
  avatar: {
    comfortable: 'h-8 w-8',
    compact: 'w-7 h-7',
  },
  title: {
    comfortable:
      "font-sans font-medium text-sm text-lia-text-primary dark:text-lia-text-primary truncate",
    compact:
      "font-sans font-medium text-xs text-lia-text-primary dark:text-lia-text-primary truncate",
  },
  subtitle: {
    comfortable:
      "font-sans text-xs text-gray-700 dark:text-gray-300 truncate",
    compact:
      "font-sans text-xs text-gray-700 dark:text-gray-300 truncate",
  },
  tertiary: {
    comfortable:
      "font-sans text-xs text-gray-600 dark:text-gray-400 truncate",
    compact:
      "font-sans text-xs text-gray-600 dark:text-gray-400 truncate",
  },
  // Divisor inferior (footer)
  divider:
    'border-t border-lia-border-subtle dark:border-lia-border-subtle',
  // Ribbon (faixa superior, tipo "Ação Necessária")
  ribbon:
    'px-2 py-1 bg-lia-bg-tertiary dark:bg-lia-bg-tertiary',
} as const

/**
 * v4.2: Chip canônico do Kanban (tag/pílula em outline)
 *
 * Densidades:
 * - `comfortable`: usado pelo cartão de vagas.
 * - `compact`: usado pelo cartão de candidatos.
 *
 * Variantes semânticas adicionais ficam em `variant` para casos onde o
 * chip carrega significado de estado (success/warning/danger/info).
 * Quando `variant` é omitido, o chip usa a borda neutra padrão.
 */
export const kanbanChipStyles = {
  base:
    'inline-flex items-center gap-0.5 rounded-full border bg-transparent transition-colors motion-reduce:transition-none',
  size: {
    comfortable: 'text-micro px-1.5 py-0',
    compact: 'text-[10px] leading-[14px] px-1 py-0',
    // Audit 2026-05-22: densidade relaxed (12px) para contextos onde
    // text-micro (10px) era apertado demais (modais, previews, cards de
    // detalhe). 338 sites tinham override text-xs no className antes —
    // codemod migra esses para density="relaxed" canonical.
    relaxed: 'text-xs px-1.5 py-0.5',
  },
  variant: {
    neutral:
      'border-transparent dark:border-transparent bg-lia-bg-tertiary dark:bg-lia-bg-tertiary text-lia-text-primary dark:text-lia-text-primary',
    success:
      'border-status-success/30 dark:border-status-success/30 text-status-success dark:text-status-success',
    warning:
      'border-status-warning/30 dark:border-status-warning/30 text-status-warning dark:text-status-warning',
    danger:
      'border-status-error/30 dark:border-status-error/30 text-status-error dark:text-status-error',
    info:
      'border-wedo-cyan/30 dark:border-wedo-cyan/30 text-wedo-cyan-dark dark:text-wedo-cyan',
  },
  muted: 'text-lia-text-tertiary dark:text-lia-text-tertiary',
} as const

/**
 * v4.2: Casca canônica da coluna do Kanban (vagas + candidatos)
 * Usado por <KanbanColumnShell /> em src/components/pages/job-kanban.
 *
 * Densidades:
 * - `comfortable`: kanban de vagas (página /jobs).
 * - `compact`:    kanban de candidatos dentro de uma vaga.
 *
 * Centraliza largura, fundo (com variante dark consistente nas duas telas),
 * borda, raio e altura preferencial. Estado `isDropping` adiciona ring/tint
 * apenas no contexto de candidatos (que tem drag-and-drop ativo).
 */
export const kanbanColumnShellStyles = {
  base:
    'flex flex-col bg-lia-bg-primary dark:bg-lia-bg-primary rounded-xl border border-lia-border-subtle dark:border-lia-border-subtle transition-colors motion-reduce:transition-none duration-300',
  width: {
    comfortable: 'w-panel-sm min-w-panel-sm',
    compact: 'flex-1 min-w-[275px] max-w-[368px]',
  },
  height: {
    comfortable: '',
    compact: 'h-[calc(100vh-16rem)]',
  },
  dropping: 'ring-2 ring-lia-border-medium bg-lia-bg-secondary/20',
} as const

/**
 * v4: Classes utilitárias para Botões de Ação
 * Tamanhos padronizados para botões Editar, Salvar, Exportar, etc.
 */
export const actionButtonStyles = {
  // Botões pequenos para ações inline
  sm: "inline-flex items-center gap-1.5 py-1.5 px-2.5 text-xs font-medium rounded-md transition-colors",
  smPrimary: "inline-flex items-center gap-1.5 py-1.5 px-2.5 text-xs font-medium rounded-md transition-colors bg-lia-btn-primary-bg text-lia-btn-primary-text hover:bg-lia-btn-primary-hover dark:bg-lia-bg-secondary dark:text-lia-text-disabled dark:hover:bg-lia-interactive-active disabled:opacity-50",
  smSecondary: "inline-flex items-center gap-1.5 py-1.5 px-2.5 text-xs font-medium rounded-md transition-colors border border-lia-border-default bg-lia-bg-primary text-lia-text-secondary hover:bg-lia-bg-secondary dark:border-lia-border-default dark:bg-lia-bg-secondary dark:text-lia-text-secondary dark:hover:bg-lia-bg-inverse disabled:opacity-50",
  smOutline: "inline-flex items-center gap-1.5 py-1.5 px-2.5 text-xs font-medium rounded-md transition-colors border border-lia-border-default bg-transparent text-lia-text-secondary hover:bg-lia-bg-secondary dark:border-lia-border-default dark:text-lia-text-secondary dark:hover:bg-lia-btn-primary-hover",
  // Ícones padrão para botões de ação
  icon: 'w-3.5 h-3.5',
} as const

/**
 * v4: Classes utilitárias para Modais
 */
export const modalStyles = {
  overlay: 'fixed inset-0 bg-lia-overlay backdrop-blur-[1px] z-50',
  container: 'bg-lia-bg-primary border border-lia-border-subtle rounded-md',
  header: 'px-6 py-4 border-b border-lia-border-subtle',
  headerTitle: "font-sans text-base font-semibold text-lia-text-primary",
  body: 'px-6 py-4',
  footer: 'px-6 py-4 border-t border-lia-border-subtle flex justify-end gap-3',
} as const

/**
 * v4: Classes utilitárias para estados de formulário
 */
export const formStyles = {
  fieldGroup: 'space-y-1.5',
  label: "font-sans text-xs font-medium text-lia-text-secondary",
  labelRequired: "font-sans text-xs font-medium text-lia-text-secondary after:content-['*'] after:ml-0.5 after:text-status-error",
  helperText: "font-sans text-micro font-normal text-lia-text-tertiary mt-1",
  errorText: "font-sans text-micro font-normal text-status-error mt-1",
} as const

/**
 * v4: Mapeamento Tailwind → Vuetify 3 para migração futura
 */
export const tailwindToVuetify = {
  colors: {
    'bg-lia-btn-primary-bg': 'color="grey-darken-4"',
    'bg-lia-bg-tertiary': 'class="bg-grey-lighten-4"',
    'bg-lia-bg-secondary': 'class="bg-grey-lighten-5"',
    'border-lia-border-subtle': 'class="border-grey-lighten-3"',
    'border-lia-border-default': 'class="border-grey-lighten-2"',
    'text-lia-text-primary': 'class="text-grey-darken-3"',
    'text-lia-text-secondary': 'class="text-grey-darken-1"',
    'text-lia-text-tertiary': 'class="text-grey"',
    'border': 'elevation="0"',
  },
  
  typography: {
    // text-xs = 12px neste projeto → Vuetify text-caption (≈12px)
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
    // Legado — removido (duplicatas de text-xs e text-micro acima)
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
    Card: '<v-card variant="outlined" rounded-md="xl">',
    CardInteractive: '<v-card variant="outlined" hover rounded-md="xl">',
    Button: '<v-btn color="grey-darken-4" variant="flat">',
    ButtonSecondary: '<v-btn color="grey-lighten-4" variant="flat">',
    ButtonOutline: '<v-btn variant="outlined">',
    ButtonGhost: '<v-btn variant="text">',
    Input: '<v-text-field variant="outlined" density="compact">',
    Badge: '<v-chip size="small" variant="tonal">',
    Modal: '<v-dialog> com <v-card rounded-md="xl"> interno',
    Tabs: '<v-tabs density="compact">',
    Tab: '<v-tab>',
    Tooltip: '<v-tooltip location="top">',
  },
  
  notes: {
    primaryColor: 'Em Vuetify, configure grey-darken-4 (#111827) como cor primária para botões',
    typography: 'Configure Open Sans como fonte padrão no theme do Vuetify',
    borderRadius: 'Use rounded-md="md" (8px) para botões/inputs/cards/modais, rounded-md="pill" para badges/tabs conforme DS v4.1',
    elevation: 'Sem sombras — usar bordas (border border-lia-border-subtle) para separação visual',
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

  // Layout
  '--layout-panel-sm': '300px',
  '--layout-panel-md': '350px',
  '--layout-panel-lg': '400px',
  '--layout-panel-xl': '500px',
  '--layout-sidebar': '200px',
  '--layout-chart-h': '200px',

  // Z-Index
  '--z-base': '0',
  '--z-raised': '10',
  '--z-dropdown': '40',
  '--z-sticky': '50',
  '--z-overlay': '60',
  '--z-toast': '100',
  '--z-select': '200',
  '--z-backdrop': '9998',
  '--z-modal': '9999',
  '--z-max': '10000',

  // Spacing
  '--space-xs': '4px',
  '--space-sm': '8px',
  '--space-md': '16px',
  '--space-lg': '24px',
  '--space-xl': '32px',
  '--space-2xl': '48px',
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
    // WSI escala 0-10 (Task #512 / PR3 do #497). Cutoffs canônicos em
    // `lib/wsi/visual.ts` — aqui mantemos a versão simplificada de 3 níveis
    // só para compat com call-sites legados que usam `getScoreColor(_, 'wsi')`.
    // 3-tier WSI 0-10: ver `lib/wsi/visual.ts` (WSI_VISUAL_3TIER).
    if (score >= 7.5) return { text: 'text-status-success', bg: 'bg-status-success/10', border: 'border-status-success/30' }
    if (score >= 6.0) return { text: 'text-status-warning', bg: 'bg-status-warning/10', border: 'border-status-warning/30' }
    return { text: 'text-status-error', bg: 'bg-status-error/10', border: 'border-status-error/30' }
  }
  
  if (score >= 80) return { text: 'text-status-success', bg: 'bg-status-success/10', border: 'border-status-success/30' }
  if (score >= 60) return { text: 'text-status-warning', bg: 'bg-status-warning/10', border: 'border-status-warning/30' }
  return { text: 'text-status-error', bg: 'bg-status-error/10', border: 'border-status-error/30' }
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
    'active': { text: 'text-status-success', bg: 'bg-status-success/10', label: 'Ativo' },
    'ativa': { text: 'text-status-success', bg: 'bg-status-success/10', label: 'Ativa' },
    'approved': { text: 'text-status-success', bg: 'bg-status-success/10', label: 'Aprovado' },
    'aprovado': { text: 'text-status-success', bg: 'bg-status-success/10', label: 'Aprovado' },
    'completed': { text: 'text-status-success', bg: 'bg-status-success/10', label: 'Concluído' },
    'pending': { text: 'text-status-warning', bg: 'bg-status-warning/10', label: 'Pendente' },
    'pendente': { text: 'text-status-warning', bg: 'bg-status-warning/10', label: 'Pendente' },
    'waiting': { text: 'text-status-warning', bg: 'bg-status-warning/10', label: 'Aguardando' },
    'aguardando': { text: 'text-status-warning', bg: 'bg-status-warning/10', label: 'Aguardando' },
    'inactive': { text: 'text-lia-text-secondary', bg: 'bg-lia-bg-tertiary', label: 'Inativo' },
    'inativa': { text: 'text-lia-text-secondary', bg: 'bg-lia-bg-tertiary', label: 'Inativa' },
    'draft': { text: 'text-lia-text-secondary', bg: 'bg-lia-bg-tertiary', label: 'Rascunho' },
    'rascunho': { text: 'text-lia-text-secondary', bg: 'bg-lia-bg-tertiary', label: 'Rascunho' },
    'error': { text: 'text-status-error', bg: 'bg-status-error/10', label: 'Erro' },
    'erro': { text: 'text-status-error', bg: 'bg-status-error/10', label: 'Erro' },
    'rejected': { text: 'text-status-error', bg: 'bg-status-error/10', label: 'Rejeitado' },
    'rejeitado': { text: 'text-status-error', bg: 'bg-status-error/10', label: 'Rejeitado' },
    'cancelled': { text: 'text-status-error', bg: 'bg-status-error/10', label: 'Cancelado' },
    'cancelado': { text: 'text-status-error', bg: 'bg-status-error/10', label: 'Cancelado' },
  }
  
  const key = status.toLowerCase()
  return statusMap[key] || { text: 'text-lia-text-secondary', bg: 'bg-lia-bg-tertiary', label: status }
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
      return { text: 'text-status-success', bg: 'bg-status-success/10', label: 'APROVADO' }
    case 'PENDING':
    case 'PENDENTE':
      return { text: 'text-status-warning', bg: 'bg-status-warning/10', label: 'PENDENTE' }
    case 'NOT_APPROVED':
    case 'NAO_APROVADO':
    case 'NÃO APROVADO':
      return { text: 'text-status-error', bg: 'bg-status-error/10', label: 'NÃO APROVADO' }
    default:
      return { text: 'text-lia-text-secondary', bg: 'bg-lia-bg-tertiary', label: recommendation }
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

const designTokens = {
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
export default designTokens
