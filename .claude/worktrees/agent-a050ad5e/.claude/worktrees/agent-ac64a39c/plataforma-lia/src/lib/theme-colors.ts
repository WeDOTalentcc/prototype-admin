// Sistema de cores temáticas baseado na paleta tech 2024-2025
export const themeColors = {
  // Chat com LIA - AI Aqua (azul futurista para IA)
  'Chat com LIA': {
    primary: '#0094c6',
    light: '#e6f7ff',
    medium: '#b3e0ff',
    dark: '#006b94',
    accent: '#4db8e8',
    text: '#003d56',
    bg: '#f0fbff',
    border: '#b3e0ff',
    hover: '#f0fbff'
  },

  // Tarefas - Warm Energy (amarelo energético para produtividade)
  'Tarefas': {
    primary: '#f0b323',
    light: '#fff8e1',
    medium: '#ffe0b3',
    dark: '#b8851a',
    accent: '#f5c955',
    text: '#5c4a0f',
    bg: '#fffcf0',
    border: '#ffe0b3',
    hover: '#fffcf0'
  },

  // Candidatos - Ethereal Blue (azul suave para gestão de pessoas)
  'Candidatos': {
    primary: '#8bb923',
    light: '#f0f9e6',
    medium: '#d4e8b3',
    dark: '#698a1a',
    accent: '#a5c455',
    text: '#3d4f0f',
    bg: '#f8fcf0',
    border: '#d4e8b3',
    hover: '#f8fcf0'
  },

  // Vagas - Electric Red (vermelho vibrante para ação/urgência)
  'Vagas': {
    primary: '#de1c31',
    light: '#ffeaea',
    medium: '#ffb3b8',
    dark: '#a51524',
    accent: '#e55a6b',
    text: '#5c0a10',
    bg: '#fff5f5',
    border: '#ffb3b8',
    hover: '#fff5f5'
  },

  // Indicadores - Peach Fuzz (coral suave para análise e métricas)
  'Indicadores': {
    primary: '#f6a68c',
    light: '#fff2ef',
    medium: '#ffd4c4',
    dark: '#c27d69',
    accent: '#f8b8a3',
    text: '#5c2e21',
    bg: '#fffaf9',
    border: '#ffd4c4',
    hover: '#fffaf9'
  },

  // Biblioteca LIA - Purple Gradient (roxo tech para conhecimento)
  'Biblioteca LIA': {
    primary: '#8b5cf6',
    light: '#f3f0ff',
    medium: '#ddd6fe',
    dark: '#6d28d9',
    accent: '#a78bfa',
    text: '#4c1d95',
    bg: '#faf8ff',
    border: '#ddd6fe',
    hover: '#faf8ff'
  }
} as const

export type PageTheme = keyof typeof themeColors

// Função para obter as cores do tema da página atual
export function getPageTheme(pageName: string): typeof themeColors[PageTheme] {
  return themeColors[pageName as PageTheme] || themeColors['Tarefas']
}

// Função para gerar classes CSS dinâmicas
export function getThemeClasses(pageName: string) {
  const theme = getPageTheme(pageName)

  return {
    // Backgrounds
    primaryBg: `bg-[${theme.primary}]`,
    lightBg: `bg-[${theme.light}]`,
    mediumBg: `bg-[${theme.medium}]`,

    // Text colors
    primaryText: `text-[${theme.primary}]`,
    darkText: `text-[${theme.dark}]`,
    textColor: `text-[${theme.text}]`,

    // Borders
    primaryBorder: `border-[${theme.primary}]`,
    lightBorder: `border-[${theme.border}]`,

    // Hover states
    hoverBg: `hover:bg-[${theme.hover}]`,

    // CSS variables for dynamic styling
    cssVars: {
      '--theme-primary': theme.primary,
      '--theme-light': theme.light,
      '--theme-medium': theme.medium,
      '--theme-dark': theme.dark,
      '--theme-accent': theme.accent,
      '--theme-text': theme.text,
      '--theme-bg': theme.bg,
      '--theme-border': theme.border,
      '--theme-hover': theme.hover
    } as React.CSSProperties
  }
}

// CSS personalizado para ser injetado dinamicamente
export function generateThemeCSS(pageName: string) {
  const theme = getPageTheme(pageName)

  return `
    .theme-primary { background-color: ${theme.primary}; }
    .theme-light { background-color: ${theme.light}; }
    .theme-medium { background-color: ${theme.medium}; }
    .theme-text-primary { color: ${theme.primary}; }
    .theme-text-dark { color: ${theme.dark}; }
    .theme-border { border-color: ${theme.border}; }
    .theme-hover:hover { background-color: ${theme.hover}; }

    .theme-gradient {
      background: linear-gradient(135deg, ${theme.light} 0%, ${theme.medium} 100%);
    }

    .theme-shadow {
      box-shadow: 0 4px 12px ${theme.primary}20;
    }

    .theme-ring {
      --tw-ring-color: ${theme.primary}40;
    }
  `
}
