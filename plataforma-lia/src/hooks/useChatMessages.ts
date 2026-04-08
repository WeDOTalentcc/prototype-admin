"use client"

/**
 * useChatMessages — Conversation init, history loading, message sending, and approval.
 *
 * Manages the conversation lifecycle (create, load history, send messages)
 * and HITL approval flow. Uses either WebSocket or fetch fallback.
 */

import { useState, useCallback, useEffect } from "react"
import { useRecentItemsStore } from "@/stores/recent-items-store"
import type {
  LiaChatMessage,
  HITLPending,
} from "./lia-chat-connection-types"
import { maskPII, formatMessageTime } from "./lia-chat-connection-types"

export interface UseChatMessagesOptions {
  sessionId: string
  isConnected: boolean
  wsSend: (content: string, context: Record<string, unknown>, domain: string) => void
  sendRaw: (data: Record<string, unknown>) => void
  clearTokens: () => void
  hitlRef: React.MutableRefObject<HITLPending | null>
  setHitlPending: React.Dispatch<React.SetStateAction<HITLPending | null>>
  onMessageComplete?: (content: string, executionPlan?: Record<string, unknown>) => void
  /** Conversation ID synced from WS message events */
  conversationIdFromWs: string | null
}

export interface UseChatMessagesReturn {
  conversationId: string | null
  setConversationId: (id: string | null) => void
  isCreating: boolean
  isFetchingHistory: boolean
  sendMessage: (content: string, domain?: string, scope?: string) => Promise<void>
  sendApproval: (approved: boolean) => void
  initConversation: (firstMessage: string, contextType?: string) => Promise<string | null>
  loadHistory: (id: string) => Promise<LiaChatMessage[]>
}

export function useChatMessages({
  sessionId,
  isConnected,
  wsSend,
  sendRaw,
  clearTokens,
  hitlRef,
  setHitlPending,
  onMessageComplete,
  conversationIdFromWs,
}: UseChatMessagesOptions): UseChatMessagesReturn {
  const recentItemsStore = useRecentItemsStore()

  const [conversationId, setConversationId] = useState<string | null>(null)
  const [isCreating, setIsCreating] = useState(false)
  const [isFetchingHistory, setIsFetchingHistory] = useState(false)

  const onCompleteRef = { current: onMessageComplete }

  // Sync conversationId from WS events
  useEffect(() => {
    if (conversationIdFromWs && conversationIdFromWs !== conversationId) {
      setConversationId(conversationIdFromWs)
    }
  }, [conversationIdFromWs]) // eslint-disable-line react-hooks/exhaustive-deps

  const getPageContext = useCallback((): Record<string, unknown> => {
    const ctx: Record<string, unknown> = {}
    try {
      const path = window.location.pathname

      const jobMatch = path.match(/\/jobs?\/([a-f0-9-]{36})/)
      if (jobMatch) {
        ctx.job_vacancy_id = jobMatch[1]
      }

      const candidateMatch = path.match(/\/candidat[eo]s?\/([a-f0-9-]{36})/)
      if (candidateMatch) {
        ctx.candidate_id = candidateMatch[1]
      }

      if (path.includes("/kanban") || path.includes("/pipeline")) {
        ctx.page_type = "kanban"
      } else if (path.includes("/candidat")) {
        ctx.page_type = "candidates"
      } else if (path.includes("/dashboard")) {
        ctx.page_type = "dashboard"
      } else if (path.includes("/job")) {
        ctx.page_type = "job_detail"
      }

      const jobContextEl = document.querySelector("[data-job-context]")
      if (jobContextEl) {
        try {
          const jobData = JSON.parse(jobContextEl.getAttribute("data-job-context") || "{}")
          if (jobData.id) ctx.job_vacancy_id = jobData.id
          if (jobData.title) ctx.job_title = jobData.title
          if (jobData.company_id) ctx.company_id = jobData.company_id
          ctx.job_context = jobData
        } catch {}
      }

      const candidatesEl = document.querySelector("[data-candidates-context]")
      if (candidatesEl) {
        try {
          const candidatesData = JSON.parse(candidatesEl.getAttribute("data-candidates-context") || "[]")
          if (Array.isArray(candidatesData) && candidatesData.length > 0) {
            ctx.candidates = candidatesData
          }
        } catch {}
      }
    } catch {}
    return ctx
  }, [])

  const sendMessage = useCallback(async (content: string, domain = "", scope?: string) => {
    clearTokens()
    const context: Record<string, unknown> = scope ? { scope } : {}
    if (conversationId) {
      context.conversation_id = conversationId
    }

    const pageContext = getPageContext()
    Object.assign(context, pageContext)

    if (isConnected) {
      wsSend(content, context, domain)
      return
    }

    try {
      const res = await fetch("/api/backend-proxy/chat/message", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          message: content,
          domain,
          session_id: sessionId,
          conversation_id: conversationId,
          context,
        }),
      })
      const data = await res.json() as {
        content?: string
        conversation_id?: string
        message_metadata?: {
          pending_action?: {
            pending_id?: string
            intent?: string
            action_id?: string
            awaiting_confirmation?: boolean
            missing_params?: string[]
            collected_params?: Record<string, unknown>
          }
        }
      }
      if (data.conversation_id && data.conversation_id !== conversationId) {
        setConversationId(data.conversation_id)
      }

      const pendingAction = data.message_metadata?.pending_action
      if (pendingAction?.awaiting_confirmation) {
        const pending: HITLPending = {
          pendingId: pendingAction.pending_id ?? "",
          threadId: data.conversation_id ?? conversationId ?? "",
          action: pendingAction.action_id ?? pendingAction.intent ?? "",
          description: data.content ?? "",
          data: pendingAction.collected_params ?? {},
        }
        hitlRef.current = pending
        setHitlPending(pending)
      }

      if (data.content) {
        onCompleteRef.current?.(data.content)
      }
    } catch {
      onCompleteRef.current?.("Erro ao conectar com a LIA. Tente novamente.")
    }
  }, [wsSend, clearTokens, isConnected, sessionId, conversationId, getPageContext, hitlRef, setHitlPending])

  const sendApproval = useCallback((approved: boolean) => {
    const pending = hitlRef.current
    if (!pending) return
    hitlRef.current = null
    sendRaw({
      type: "approval_response",
      approved,
      thread_id: pending.threadId,
      pending_id: pending.pendingId,
    })
    if (!approved) {
      setHitlPending(null)
    }
  }, [sendRaw, hitlRef, setHitlPending])

  const initConversation = useCallback(async (
    firstMessage: string,
    contextType = "general"
  ): Promise<string | null> => {
    setIsCreating(true)
    try {
      const title = maskPII(firstMessage.length > 50 ? firstMessage.slice(0, 47) + "\u2026" : firstMessage)
      const res = await fetch("/api/backend-proxy/conversations", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title, context_type: contextType }),
      })
      if (!res.ok) return null
      const data = await res.json() as { id?: string }
      const id = data.id ?? null
      if (id) {
        setConversationId(id)
        recentItemsStore.addItem({
          id,
          type: "chat",
          title,
          timestamp: Date.now(),
          meta: { conversationId: id },
        })
      }
      return id
    } catch {
      return null
    } finally {
      setIsCreating(false)
    }
  }, [recentItemsStore])

  const loadHistory = useCallback(async (id: string): Promise<LiaChatMessage[]> => {
    setIsFetchingHistory(true)
    try {
      const res = await fetch(
        `/api/backend-proxy/conversations/${id}?include_messages=true&message_limit=50`
      )
      if (!res.ok) return []
      const data = await res.json() as {
        messages?: Array<{ id: string; role: string; content: string; created_at?: string }>
      }
      return (data.messages ?? []).map(m => ({
        id: m.id,
        sender: m.role === "assistant" ? "lia" : "user",
        content: m.content,
        timestamp: formatMessageTime(m.created_at),
      }))
    } catch {
      return []
    } finally {
      setIsFetchingHistory(false)
    }
  }, [])

  return {
    conversationId,
    setConversationId,
    isCreating,
    isFetchingHistory,
    sendMessage,
    sendApproval,
    initConversation,
    loadHistory,
  }
}
