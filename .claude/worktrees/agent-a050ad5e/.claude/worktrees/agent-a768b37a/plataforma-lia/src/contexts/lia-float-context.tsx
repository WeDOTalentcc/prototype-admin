"use client"

/**
 * LiaFloatContext — Estado global do painel flutuante e split-view da LIA.
 *
 * Fornece:
 *   Float: isOpen, conversationId, open(), close(), toggle()
 *   Expanded (Super Prompt): isExpanded, expand(), collapse(), closeAll()
 *   Split-view: splitView {active, page}, openSplitView(page), closeSplitView()
 *   Shared Conversation: messages, addMessage, setMessages, conversationId (shared between mini and expanded)
 *
 * Usado por LiaChatButton, LiaChatPanel, LiaSuperPrompt, LiaSplitPanel e dashboard-app.
 * Compatível com Vue/Nuxt: mapeia para provide/inject + composable useLiaFloat().
 */

import { createContext, useContext, useState, useCallback, ReactNode } from "react"
import type { FloatMessage } from "@/hooks/use-float-conversation"

export interface SplitViewState {
  active: boolean
  page: string | null
  conversationId: string | null
}

interface LiaFloatState {
  isOpen: boolean
  isExpanded: boolean
  conversationId: string | null
  splitView: SplitViewState
}

interface LiaFloatContextType extends LiaFloatState {
  open: (conversationId?: string) => void
  close: () => void
  toggle: () => void
  expand: () => void
  collapse: () => void
  closeAll: () => void
  openSplitView: (page: string, conversationId?: string) => void
  closeSplitView: () => void
  sharedMessages: FloatMessage[]
  addSharedMessage: (msg: FloatMessage) => void
  setSharedMessages: React.Dispatch<React.SetStateAction<FloatMessage[]>>
  sharedConversationId: string | null
  setSharedConversationId: (id: string | null) => void
}

const LiaFloatContext = createContext<LiaFloatContextType | undefined>(undefined)

const INITIAL_SPLIT_VIEW: SplitViewState = { active: false, page: null, conversationId: null }

export function LiaFloatProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<LiaFloatState>({
    isOpen: false,
    isExpanded: false,
    conversationId: null,
    splitView: INITIAL_SPLIT_VIEW,
  })

  const [sharedMessages, setSharedMessages] = useState<FloatMessage[]>([])
  const [sharedConversationId, setSharedConversationId] = useState<string | null>(null)

  const addSharedMessage = useCallback((msg: FloatMessage) => {
    setSharedMessages(prev => [...prev, msg])
  }, [])

  const open = useCallback((conversationId?: string) => {
    setState(prev => ({
      ...prev,
      isOpen: true,
      isExpanded: false,
      conversationId: conversationId ?? prev.conversationId,
    }))
  }, [])

  const close = useCallback(() => {
    setState(prev => ({ ...prev, isOpen: false }))
  }, [])

  const toggle = useCallback(() => {
    setState(prev => ({ ...prev, isOpen: !prev.isOpen }))
  }, [])

  const expand = useCallback(() => {
    setState(prev => ({
      ...prev,
      isOpen: false,
      isExpanded: true,
    }))
  }, [])

  const collapse = useCallback(() => {
    setState(prev => ({
      ...prev,
      isExpanded: false,
      isOpen: true,
    }))
  }, [])

  const closeAll = useCallback(() => {
    setState(prev => ({
      ...prev,
      isOpen: false,
      isExpanded: false,
    }))
  }, [])

  const openSplitView = useCallback((page: string, conversationId?: string) => {
    setState(prev => ({
      ...prev,
      isOpen: false,
      isExpanded: false,
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
      value={{
        ...state,
        open, close, toggle, expand, collapse, closeAll,
        openSplitView, closeSplitView,
        sharedMessages, addSharedMessage, setSharedMessages,
        sharedConversationId, setSharedConversationId,
      }}
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
