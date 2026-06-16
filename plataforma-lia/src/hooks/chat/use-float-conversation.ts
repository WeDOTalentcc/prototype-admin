"use client"

import { useState, useCallback, useRef } from "react"
import { useRecentItemsStore } from "@/stores/recent-items-store"
import { getPersisted, setPersisted } from "@/lib/lia-persistence"

// Onda 4-P2-6 (2026-05-24): chave canonical com TTL medium (30 dias).
// Antes era localStorage raw sem TTL — conversation IDs viravam lixo (stale
// referências de conversas deletadas há meses se usuário usa mesmo browser).
const RECENT_ITEMS_KEY = "lia-recent-items"
const RECENT_ITEMS_LIMIT = 15

export interface FloatMessage {
  id: string
  sender: "lia" | "user" | "system"
  content: string
  timestamp: string
  executionPlan?: Record<string, unknown>
  planProgressSteps?: Array<{ task_id: string; action_id: string; status: string }>
  // Sprint B.6 (P2-2 onboarding): backend marca pergunta com hint de quick_reply
  // pra UI renderizar botões inline em vez de exigir texto livre. Preset
  // corresponde aos canonical em QuickReplies.tsx (boolean, work_model, ...).
  metadata?: {
    quick_reply_preset?: "boolean" | "work_model" | "autonomy" | "channel" | "experience_policy" | "ai_tone"
    [k: string]: unknown
  }
}

export const FLOAT_CONTEXT_TYPE = "general" as const

function maskPII(text: string): string {
  return text
    .replace(/\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b/g, "[CPF]")
    .replace(/\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g, "[email]")
    .replace(/\b(?:\+55\s?)?(?:\(?\d{2}\)?\s?)(?:9\d{4}|\d{4})-?\d{4}\b/g, "[tel]")
}

import { formatMessageTime } from "./lia-chat-connection-types"

interface UseFloatConversationResult {
  conversationId: string | null
  messages: FloatMessage[]
  isCreating: boolean
  isFetchingHistory: boolean
  initConversation: (firstMessage: string) => Promise<string | null>
  loadHistory: (id: string) => Promise<void>
  addMessage: (msg: FloatMessage) => void
  setMessages: React.Dispatch<React.SetStateAction<FloatMessage[]>>
  setConversationId: (id: string | null) => void
}

export function useFloatConversation(
  initialConversationId: string | null,
  externalSetMessages?: React.Dispatch<React.SetStateAction<FloatMessage[]>>,
): UseFloatConversationResult {
  const recentItemsStore = useRecentItemsStore()
  const [conversationId, setConversationId] = useState<string | null>(initialConversationId)
  const [internalMessages, setInternalMessages] = useState<FloatMessage[]>([])
  const [isCreating, setIsCreating] = useState(false)
  const [isFetchingHistory, setIsFetchingHistory] = useState(false)

  const messages = internalMessages
  const setMessages = externalSetMessages ?? setInternalMessages

  const initConversation = useCallback(async (firstMessage: string): Promise<string | null> => {
    setIsCreating(true)
    try {
      const title = maskPII(firstMessage.length > 50 ? firstMessage.slice(0, 47) + "…" : firstMessage)
      const res = await fetch("/api/backend-proxy/conversations", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title, context_type: FLOAT_CONTEXT_TYPE }),
      })
      if (!res.ok) return null
      const data = await res.json() as { id?: string }
      const id = data.id ?? null
      if (id) {
        setConversationId(id)
        const newItem = {
          id,
          type: "chat" as const,
          title,
          timestamp: Date.now(),
          meta: { conversationId: id },
        }
        recentItemsStore.addItem(newItem)
        // Onda 4-P2-6: canonical persistence com TTL medium (30 dias)
        const existing = getPersisted<typeof newItem[]>(RECENT_ITEMS_KEY, [])
        const filtered = existing.filter(i => !(i.id === id && i.type === "chat"))
        setPersisted(RECENT_ITEMS_KEY, [newItem, ...filtered].slice(0, RECENT_ITEMS_LIMIT), "medium")
      }
      return id
    } catch {
      return null
    } finally {
      setIsCreating(false)
    }
  }, [recentItemsStore])

  // Stale-request guard (Task #570 review fix): protect setMessages from being
  // overwritten by an older fetch when the user switches conversations
  // before the previous load finishes.
  const loadHistoryTokenRef = useRef(0)

  const loadHistory = useCallback(async (id: string): Promise<void> => {
    const myToken = ++loadHistoryTokenRef.current
    setIsFetchingHistory(true)
    try {
      const res = await fetch(
        `/api/backend-proxy/conversations/${id}?include_messages=true&message_limit=50`
      )
      if (!res.ok) return
      if (loadHistoryTokenRef.current !== myToken) return
      const data = await res.json() as {
        messages?: Array<{ id: string; role: string; content: string; created_at?: string }>
      }
      const restored: FloatMessage[] = (data.messages ?? []).map(m => ({
        id: m.id,
        sender: m.role === "assistant" ? "lia" : "user",
        content: m.content,
        timestamp: formatMessageTime(m.created_at),
      }))
      if (loadHistoryTokenRef.current !== myToken) return
      setMessages(restored)
    } catch {
    } finally {
      if (loadHistoryTokenRef.current === myToken) {
        setIsFetchingHistory(false)
      }
    }
  }, [setMessages])

  const addMessage = useCallback((msg: FloatMessage) => {
    setMessages(prev => [...prev, msg])
  }, [setMessages])

  return {
    conversationId,
    messages,
    isCreating,
    isFetchingHistory,
    initConversation,
    loadHistory,
    addMessage,
    setMessages,
    setConversationId,
  }
}
