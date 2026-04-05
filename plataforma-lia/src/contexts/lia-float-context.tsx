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

export interface EntityContext {
  type: "candidate" | "job" | null
  id?: string | number
  name?: string
  meta?: Record<string, unknown>
}

export type DynamicPanelType =
  | "calibration"
  | "candidate_review"
  | "profile"
  | "job_creation"
  | "scheduling"

export interface DynamicPanelData {
  panelType: DynamicPanelType
  data: Record<string, unknown>
  title?: string
}

interface LiaFloatState {
  isOpen: boolean
  isExpanded: boolean
  conversationId: string | null
  splitView: SplitViewState
  contextPage: string | null
  entityContext: EntityContext | null
  dynamicPanel: DynamicPanelData | null
}

interface LiaFloatContextType extends LiaFloatState {
  open: (conversationId?: string) => void
  close: () => void
  toggle: () => void
  expand: () => void
  collapse: () => void
  closeAll: () => void
  navigateToChat: () => void
  setContextPage: (page: string | null) => void
  setEntityContext: (ctx: EntityContext | null) => void
  openWithEntity: (entity: EntityContext) => void
  openSplitView: (page: string, conversationId?: string) => void
  closeSplitView: () => void
  openDynamicPanel: (panel: DynamicPanelData) => void
  closeDynamicPanel: () => void
  updateDynamicPanelData: (data: Record<string, unknown>) => void
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
    contextPage: null,
    entityContext: null,
    dynamicPanel: null,
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
    setState(prev => ({ ...prev, isOpen: false, entityContext: null, dynamicPanel: null }))
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
      entityContext: null,
      dynamicPanel: null,
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

  const setContextPage = useCallback((page: string | null) => {
    setState(prev => ({ ...prev, contextPage: page }))
  }, [])

  const setEntityContext = useCallback((ctx: EntityContext | null) => {
    setState(prev => ({ ...prev, entityContext: ctx }))
  }, [])

  const openWithEntity = useCallback((entity: EntityContext) => {
    setState(prev => ({
      ...prev,
      isOpen: true,
      isExpanded: false,
      entityContext: entity,
    }))
  }, [])

  const openDynamicPanel = useCallback((panel: DynamicPanelData) => {
    setState(prev => ({ ...prev, dynamicPanel: panel }))
  }, [])

  const closeDynamicPanel = useCallback(() => {
    setState(prev => ({ ...prev, dynamicPanel: null }))
  }, [])

  const updateDynamicPanelData = useCallback((data: Record<string, unknown>) => {
    setState(prev => {
      if (!prev.dynamicPanel) return prev
      return {
        ...prev,
        dynamicPanel: {
          ...prev.dynamicPanel,
          data: { ...prev.dynamicPanel.data, ...data },
        },
      }
    })
  }, [])

  const navigateToChat = useCallback(() => {
    setState(prev => ({
      ...prev,
      isOpen: false,
      isExpanded: false,
      splitView: INITIAL_SPLIT_VIEW,
    }))
    if (document.querySelector("[data-dashboard-shell]")) {
      window.dispatchEvent(new CustomEvent("lia:navigate-chat-page"))
    } else {
      window.location.href = "/?page=chat-lia"
    }
  }, [])

  return (
    <LiaFloatContext.Provider
      value={{
        ...state,
        open, close, toggle, expand, collapse, closeAll,
        navigateToChat, setContextPage, setEntityContext, openWithEntity,
        openSplitView, closeSplitView,
        openDynamicPanel, closeDynamicPanel, updateDynamicPanelData,
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
