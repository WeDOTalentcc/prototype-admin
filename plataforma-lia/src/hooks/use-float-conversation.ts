"use client"

import { useState, useCallback } from "react"
import { useRecentItemsStore } from "@/stores/recent-items-store"

export interface FloatMessage {
  id: string
  sender: "lia" | "user"
  content: string
  timestamp: string
  executionPlan?: Record<string, unknown>
  planProgressSteps?: Array<{ task_id: string; action_id: string; status: string }>
}

export const FLOAT_CONTEXT_TYPE = "general" as const

function maskPII(text: string): string {
  return text
    .replace(/\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b/g, "[CPF]")
    .replace(/\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g, "[email]")
    .replace(/\b(?:\+55\s?)?(?:\(?\d{2}\)?\s?)(?:9\d{4}|\d{4})-?\d{4}\b/g, "[tel]")
}

export function formatMessageTime(isoDate?: string): string {
  const d = isoDate ? new Date(isoDate) : new Date()
  return d.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })
}

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

  const loadHistory = useCallback(async (id: string): Promise<void> => {
    setIsFetchingHistory(true)
    try {
      const res = await fetch(
        `/api/backend-proxy/conversations/${id}?include_messages=true&message_limit=50`
      )
      if (!res.ok) return
      const data = await res.json() as {
        messages?: Array<{ id: string; role: string; content: string; created_at?: string }>
      }
      const restored: FloatMessage[] = (data.messages ?? []).map(m => ({
        id: m.id,
        sender: m.role === "assistant" ? "lia" : "user",
        content: m.content,
        timestamp: formatMessageTime(m.created_at),
      }))
      setMessages(restored)
    } catch {
    } finally {
      setIsFetchingHistory(false)
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
