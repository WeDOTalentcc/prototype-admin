import { useEffect } from 'react'
import { getPageTheme, generateThemeCSS, type PageTheme } from '@/lib/theme-colors'

export function usePageTheme(currentPage: string) {
  const theme = getPageTheme(currentPage)

  useEffect(() => {
    // Remover estilos anteriores
    const existingStyle = document.getElementById('page-theme-styles')
    if (existingStyle) {
      existingStyle.remove()
    }

    // Adicionar novos estilos
    const style = document.createElement('style')
    style.id = 'page-theme-styles'
    style.textContent = generateThemeCSS(currentPage)
    document.head.appendChild(style)

    // Adicionar variáveis CSS ao root
    const root = document.documentElement
    root.style.setProperty('--current-theme-primary', theme.primary)
    root.style.setProperty('--current-theme-light', theme.light)
    root.style.setProperty('--current-theme-medium', theme.medium)
    root.style.setProperty('--current-theme-dark', theme.dark)
    root.style.setProperty('--current-theme-accent', theme.accent)
    root.style.setProperty('--current-theme-text', theme.text)
    root.style.setProperty('--current-theme-bg', theme.bg)
    root.style.setProperty('--current-theme-border', theme.border)
    root.style.setProperty('--current-theme-hover', theme.hover)

    // Cleanup on unmount
    return () => {
      const styleElement = document.getElementById('page-theme-styles')
      if (styleElement) {
        styleElement.remove()
      }
    }
  }, [currentPage, theme])

  return {
    theme,
    themeStyles: {
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
