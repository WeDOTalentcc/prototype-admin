// src/contexts/ToolSurfaceContext.tsx
import { createContext, useContext } from 'react'

/**
 * Superfície de renderização do tool result atual.
 * Default: 'inline' (chat). DynamicContextPanel define 'panel'.
 *
 * Card components leem este context para escolher sua apresentação:
 *   const surface = useToolSurface()
 *   if (surface === 'panel') return <FullListView />
 *   return <CompactPreview onOpenPanel={...} />
 */
export type ToolSurface = 'inline' | 'panel'

export const ToolSurfaceContext = createContext<ToolSurface>('inline')

export const useToolSurface = () => useContext(ToolSurfaceContext)

/**
 * Callback para abrir o painel focado num tool call específico.
 * Injetado por UnifiedChat.tsx apenas quando hasDynamicPanelFull=true.
 * null quando o painel não está disponível (sidebar/floating/sem wizard ativo).
 *
 * Cards checam: const activate = useToolActivate()
 * E renderizam o botão "Ver no painel" apenas quando activate != null.
 */
export const ToolActivateContext = createContext<((callId: string) => void) | null>(null)

export const useToolActivate = () => useContext(ToolActivateContext)
