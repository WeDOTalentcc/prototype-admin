"use client"

/**
 * useTriagemSession — Session lifecycle: init, start, complete, review.
 *
 * Handles loading session data, transitioning page states, and session completion.
 */

import { useState, useCallback, useRef, useEffect } from "react"
import { useTriagemStore } from "@/stores/triagem-store"
import type {
  TriagemSession,
  TriagemConfig,
  TriagemMessage,
  TriagemError,
  TriagemPageState,
  WSIProgress,
  TriagemCompletionSummary,
} from "@/components/triagem/types"
import {
  API_BASE,
  fetchWithRetry,
  mapErrorResponse,
  mapBackendSession,
  mapBackendProgress,
  mapBackendMessage,
} from "./triagem-chat-types"

export interface UseTriagemSessionOptions {
  token: string
}

export interface UseTriagemSessionReturn {
  pageState: TriagemPageState
  setPageState: React.Dispatch<React.SetStateAction<TriagemPageState>>
  session: TriagemSession | null
  setSession: React.Dispatch<React.SetStateAction<TriagemSession | null>>
  config: TriagemConfig | null
  messages: TriagemMessage[]
  setMessages: React.Dispatch<React.SetStateAction<TriagemMessage[]>>
  progress: WSIProgress | null
  setProgress: React.Dispatch<React.SetStateAction<WSIProgress | null>>
  error: TriagemError | null
  setError: React.Dispatch<React.SetStateAction<TriagemError | null>>
  completionSummary: TriagemCompletionSummary | null
  isLiaTyping: boolean
  setIsLiaTyping: React.Dispatch<React.SetStateAction<boolean>>
  mountedRef: React.MutableRefObject<boolean>
  initSession: () => Promise<void>
  startChat: (voiceMode?: boolean) => Promise<void>
  completeSession: () => Promise<void>
  reviewSession: () => void
  isSending: boolean
  setIsSending: React.Dispatch<React.SetStateAction<boolean>>
}

export function useTriagemSession({ token }: UseTriagemSessionOptions): UseTriagemSessionReturn {
  const triagemStore = useTriagemStore()
  const [pageState, setPageState] = useState<TriagemPageState>("loading")
  const [session, setSession] = useState<TriagemSession | null>(null)
  const [config, setConfig] = useState<TriagemConfig | null>(null)
  const [messages, setMessages] = useState<TriagemMessage[]>([])
  const [progress, setProgress] = useState<WSIProgress | null>(null)
  const [error, setError] = useState<TriagemError | null>(null)
  const [completionSummary, setCompletionSummary] = useState<TriagemCompletionSummary | null>(null)
  const [isLiaTyping, setIsLiaTyping] = useState(false)
  const [isSending, setIsSending] = useState(false)

  const mountedRef = useRef(true)

  useEffect(() => {
    mountedRef.current = true
    return () => {
      mountedRef.current = false
    }
  }, [])

  useEffect(() => {
    if (messages.length > 0 && pageState !== "loading" && pageState !== "error") {
      triagemStore.setSessionState(token, { messages, pageState })
    }
  }, [messages, pageState, token, triagemStore])

  const initSession = useCallback(async () => {
    setPageState("loading")
    setError(null)

    try {
      const response = await fetchWithRetry(`${API_BASE}/${token}`, {
        method: "GET",
        headers: { "Content-Type": "application/json" },
      })

      if (!response.ok) {
        const body = await response.json().catch(() => ({}))
        const err = mapErrorResponse(response.status, body)
        if (!mountedRef.current) return
        setError(err)
        setPageState("error")
        return
      }

      const data = await response.json()
      if (!mountedRef.current) return

      const sessionData = data.session
        ? mapBackendSession(data.session as Record<string, unknown>)
        : null
      const configData = data.config as TriagemConfig

      if (sessionData) {
        setSession(sessionData)
        setProgress(sessionData.progress)
      }
      if (configData) {
        setConfig(configData)
      }

      if (sessionData?.status === "completed") {
        setCompletionSummary(data.completion_summary ?? null)
        setPageState("completion")
        if (data.messages && Array.isArray(data.messages)) {
          setMessages((data.messages as Record<string, unknown>[]).map(mapBackendMessage))
        }
        return
      }

      if (sessionData?.status === "in_progress" || sessionData?.status === "started") {
        const persisted = triagemStore.getSessionState(token)
        if (persisted && Array.isArray(persisted.messages) && persisted.messages.length > 0) {
          setMessages(persisted.messages as TriagemMessage[])
        }
        if (data.messages && Array.isArray(data.messages) && (data.messages as unknown[]).length > 0) {
          setMessages((data.messages as Record<string, unknown>[]).map(mapBackendMessage))
        }
        setPageState("chat")
        return
      }

      setPageState("welcome")
    } catch (err) {
      if (!mountedRef.current) return
      setError({
        code: "SERVER_ERROR",
        message: err instanceof Error && err.name === "AbortError"
          ? "Tempo limite excedido. Verifique sua conex\u00e3o."
          : "N\u00e3o foi poss\u00edvel carregar a triagem. Tente novamente.",
      })
      setPageState("error")
    }
  }, [token, triagemStore])

  const startChat = useCallback(async (voiceMode?: boolean) => {
    if (!session) return

    setPageState("chat")
    setIsLiaTyping(true)

    try {
      const isVoice = voiceMode ?? config?.voiceMode ?? false
      const response = await fetchWithRetry(`${API_BASE}/${token}/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ voice_mode: isVoice || undefined }),
      })

      if (!response.ok) {
        const body = await response.json().catch(() => ({}))
        if (!mountedRef.current) return
        setError(mapErrorResponse(response.status, body))
        return
      }

      const data = await response.json()
      if (!mountedRef.current) return

      if (data.session) {
        setSession(mapBackendSession(data.session as Record<string, unknown>))
      }
      if (data.progress) {
        setProgress(mapBackendProgress(data.progress as Record<string, unknown>))
      }
      if (data.lia_response) {
        setMessages((prev) => [...prev, mapBackendMessage(data.lia_response as Record<string, unknown>)])
      }
    } catch {
      if (!mountedRef.current) return
      setError({ code: "SERVER_ERROR", message: "Erro ao iniciar conversa. Tente novamente." })
    } finally {
      if (mountedRef.current) {
        setIsLiaTyping(false)
      }
    }
  }, [session, token, config?.voiceMode])

  const completeSession = useCallback(async () => {
    setIsSending(true)
    setError(null)

    try {
      const response = await fetchWithRetry(`${API_BASE}/${token}/complete`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      })

      if (!response.ok) {
        const body = await response.json().catch(() => ({}))
        if (!mountedRef.current) return
        setError(mapErrorResponse(response.status, body))
        return
      }

      const data = await response.json()
      if (!mountedRef.current) return

      if (data.session) {
        setSession(mapBackendSession(data.session as Record<string, unknown>))
      }
      if (data.completion_summary) {
        setCompletionSummary(data.completion_summary as TriagemCompletionSummary)
      }
      if (data.completion_message) {
        setMessages((prev) => [...prev, mapBackendMessage(data.completion_message as Record<string, unknown>)])
      }

      setPageState("completion")

      triagemStore.removeSessionState(token)
    } catch {
      if (!mountedRef.current) return
      setError({ code: "SERVER_ERROR", message: "Erro ao finalizar triagem. Tente novamente." })
    } finally {
      if (mountedRef.current) {
        setIsSending(false)
      }
    }
  }, [token, triagemStore])

  const reviewSession = useCallback(() => {
    setPageState("chat")
  }, [])

  return {
    pageState,
    setPageState,
    session,
    setSession,
    config,
    messages,
    setMessages,
    progress,
    setProgress,
    error,
    setError,
    completionSummary,
    isLiaTyping,
    setIsLiaTyping,
    mountedRef,
    initSession,
    startChat,
    completeSession,
    reviewSession,
    isSending,
    setIsSending,
  }
}
