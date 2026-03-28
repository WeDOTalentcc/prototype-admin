"use client"

/**
 * useFloatConversation — Gerencia criação, histórico e persistência de conversa do float.
 *
 * Extrai de LiaChatPanel: criação de conversa, busca de histórico e
 * adição aos recentes, mantendo o componente abaixo de 150 linhas.
 *
 * Portabilidade Vue: mapeia para composable `useFloatConversation()`.
 */

import { useState, useCallback } from "react"

export interface FloatMessage {
  id: string
  sender: "lia" | "user"
  content: string
  timestamp: string
}

/** Tipos aceitos pelo backend como context_type */
export const FLOAT_CONTEXT_TYPE = "general" as const

const RECENTS_STORAGE_KEY = "lia-recent-items"
const RECENTS_MAX_ITEMS = 15

/** Máscara básica de PII no título antes de persistir no localStorage. */
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

function addToRecents(conversationId: string, title: string) {
  if (typeof window === "undefined") return
  try {
    const raw = localStorage.getItem(RECENTS_STORAGE_KEY)
    const existing: Array<{ id: string; type: string; title: string; timestamp: number; meta?: Record<string, unknown> }> =
      raw ? (JSON.parse(raw) as typeof existing) : []
    const filtered = existing.filter(
      item => !(item.id === conversationId && item.type === "chat")
    )
    const updated = [
      { id: conversationId, type: "chat", title, timestamp: Date.now(), meta: { conversationId } },
      ...filtered,
    ].slice(0, RECENTS_MAX_ITEMS)
    localStorage.setItem(RECENTS_STORAGE_KEY, JSON.stringify(updated))
  } catch {
    // storage unavailable
  }
}

interface UseFloatConversationResult {
  conversationId: string | null
  messages: FloatMessage[]
  isCreating: boolean
  isFetchingHistory: boolean
  /** Cria nova conversa com base na primeira mensagem do usuário. */
  initConversation: (firstMessage: string) => Promise<string | null>
  /** Carrega histórico de mensagens de uma conversa existente. */
  loadHistory: (id: string) => Promise<void>
  /** Adiciona uma mensagem ao estado local. */
  addMessage: (msg: FloatMessage) => void
  /** Substitui a lista de mensagens. */
  setMessages: React.Dispatch<React.SetStateAction<FloatMessage[]>>
  setConversationId: (id: string | null) => void
}

export function useFloatConversation(
  initialConversationId: string | null,
  externalSetMessages?: React.Dispatch<React.SetStateAction<FloatMessage[]>>,
): UseFloatConversationResult {
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
        addToRecents(id, title)
      }
      return id
    } catch {
      return null
    } finally {
      setIsCreating(false)
    }
  }, [])

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
      // falha silenciosa — histórico não crítico
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
