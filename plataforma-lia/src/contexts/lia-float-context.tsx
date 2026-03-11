"use client"

/**
 * LiaFloatContext — Estado global do painel flutuante e split-view da LIA.
 *
 * Fornece:
 *   Float: isOpen, conversationId, open(), close(), toggle()
 *   Split-view: splitView {active, page}, openSplitView(page), closeSplitView()
 *
 * Usado por LiaChatButton, LiaChatPanel, LiaSplitPanel e dashboard-app.
 * Compatível com Vue/Nuxt: mapeia para provide/inject + composable useLiaFloat().
 */

import { createContext, useContext, useState, useCallback, ReactNode } from "react"

export interface SplitViewState {
  active: boolean
  /** Nome da página a renderizar (ex: "Vagas", "Funil de Talentos") */
  page: string | null
  conversationId: string | null
}

interface LiaFloatState {
  isOpen: boolean
  conversationId: string | null
  splitView: SplitViewState
}

interface LiaFloatContextType extends LiaFloatState {
  open: (conversationId?: string) => void
  close: () => void
  toggle: () => void
  openSplitView: (page: string, conversationId?: string) => void
  closeSplitView: () => void
}

const LiaFloatContext = createContext<LiaFloatContextType | undefined>(undefined)

const INITIAL_SPLIT_VIEW: SplitViewState = { active: false, page: null, conversationId: null }

export function LiaFloatProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<LiaFloatState>({
    isOpen: false,
    conversationId: null,
    splitView: INITIAL_SPLIT_VIEW,
  })

  const open = useCallback((conversationId?: string) => {
    setState(prev => ({
      ...prev,
      isOpen: true,
      conversationId: conversationId ?? prev.conversationId,
    }))
  }, [])

  const close = useCallback(() => {
    setState(prev => ({ ...prev, isOpen: false }))
  }, [])

  const toggle = useCallback(() => {
    setState(prev => ({ ...prev, isOpen: !prev.isOpen }))
  }, [])

  /** Fecha o float e abre o split-view com a página indicada. */
  const openSplitView = useCallback((page: string, conversationId?: string) => {
    setState(prev => ({
      ...prev,
      isOpen: false,
      splitView: {
        active: true,
        page,
        conversationId: conversationId ?? prev.conversationId,
      },
    }))
  }, [])

  const closeSplitView = useCallback(() => {
    setState(prev => ({
      ...prev,
      splitView: INITIAL_SPLIT_VIEW,
    }))
  }, [])

  return (
    <LiaFloatContext.Provider
      value={{ ...state, open, close, toggle, openSplitView, closeSplitView }}
    >
      {children}
    </LiaFloatContext.Provider>
  )
}

export function useLiaFloat(): LiaFloatContextType {
  const ctx = useContext(LiaFloatContext)
  if (!ctx) throw new Error("useLiaFloat deve ser usado dentro de LiaFloatProvider")
  return ctx
}
