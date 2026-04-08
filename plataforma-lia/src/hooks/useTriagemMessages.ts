"use client"

/**
 * useTriagemMessages — Message sending and history loading for triagem chat.
 *
 * Handles optimistic updates, debouncing, and history fetching.
 */

import { useState, useCallback, useRef, useEffect } from "react"
import type {
  TriagemMessage,
  TriagemSession,
  TriagemConfig,
  TriagemError,
  TriagemPageState,
  WSIProgress,
  SendMessagePayload,
} from "@/components/triagem/types"
import {
  API_BASE,
  DEBOUNCE_MS,
  fetchWithRetry,
  mapErrorResponse,
  mapBackendSession,
  mapBackendProgress,
  mapBackendMessage,
} from "./triagem-chat-types"

export interface UseTriagemMessagesOptions {
  token: string
  pageState: TriagemPageState
  setPageState: React.Dispatch<React.SetStateAction<TriagemPageState>>
  session: TriagemSession | null
  setSession: React.Dispatch<React.SetStateAction<TriagemSession | null>>
  config: TriagemConfig | null
  messages: TriagemMessage[]
  setMessages: React.Dispatch<React.SetStateAction<TriagemMessage[]>>
  progress: WSIProgress | null
  setProgress: React.Dispatch<React.SetStateAction<WSIProgress | null>>
  setError: React.Dispatch<React.SetStateAction<TriagemError | null>>
  setIsLiaTyping: React.Dispatch<React.SetStateAction<boolean>>
  mountedRef: React.MutableRefObject<boolean>
  isSending: boolean
  setIsSending: React.Dispatch<React.SetStateAction<boolean>>
}

export interface UseTriagemMessagesReturn {
  sendMessage: (payload: SendMessagePayload) => Promise<void>
  loadHistory: () => Promise<void>
  isLoadingHistory: boolean
}

export function useTriagemMessages(options: UseTriagemMessagesOptions): UseTriagemMessagesReturn {
  const {
    token,
    pageState,
    setPageState,
    session,
    setSession,
    config,
    messages,
    setMessages,
    progress,
    setProgress,
    setError,
    setIsLiaTyping,
    mountedRef,
    isSending,
    setIsSending,
  } = options

  const [isLoadingHistory, setIsLoadingHistory] = useState(false)
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current)
      }
    }
  }, [])

  const sendMessage = useCallback(
    async (payload: SendMessagePayload) => {
      if (isSending || pageState !== "chat") return

      if (debounceRef.current) {
        clearTimeout(debounceRef.current)
      }

      return new Promise<void>((resolve) => {
        debounceRef.current = setTimeout(async () => {
          setIsSending(true)
          setError(null)

          const optimisticMessage: TriagemMessage = {
            id: `temp_${Date.now()}`,
            sessionId: session?.id ?? "",
            role: "candidate",
            type: payload.type,
            content: payload.content,
            options: null,
            selectedOption: payload.selectedOption ?? null,
            likertValue: payload.likertValue ?? null,
            likertLabels: null,
            timestamp: new Date().toISOString(),
            blockIndex: progress?.currentBlock ?? null,
            blockName: progress?.currentBlockName ?? null,
            audioUrl: null,
          }

          setMessages((prev) => [...prev, optimisticMessage])
          setIsLiaTyping(true)

          try {
            const response = await fetchWithRetry(`${API_BASE}/${token}/message`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                content: payload.content,
                message_type: payload.type,
                selected_option: payload.selectedOption,
                likert_value: payload.likertValue,
                voice_mode: payload.voiceMode ?? config?.voiceMode ?? undefined,
              }),
            })

            if (!response.ok) {
              const body = await response.json().catch(() => ({}))
              if (!mountedRef.current) return
              setMessages((prev) => prev.filter((m) => m.id !== optimisticMessage.id))
              setError(mapErrorResponse(response.status, body))
              return
            }

            const data = await response.json()
            if (!mountedRef.current) return

            setMessages((prev) => {
              const withoutOptimistic = prev.filter((m) => m.id !== optimisticMessage.id)
              const newMessages: TriagemMessage[] = []
              if (data.candidate_message) {
                newMessages.push(mapBackendMessage(data.candidate_message as Record<string, unknown>))
              }
              if (data.lia_response) {
                newMessages.push(mapBackendMessage(data.lia_response as Record<string, unknown>))
              }
              return [...withoutOptimistic, ...newMessages]
            })

            if (data.progress) {
              setProgress(mapBackendProgress(data.progress as Record<string, unknown>))
            }
            if (data.session) {
              setSession(mapBackendSession(data.session as Record<string, unknown>))
            }

            if (data.is_pre_completion || data.show_confirmation) {
              setPageState("confirmation")
            }
          } catch {
            if (!mountedRef.current) return
            setMessages((prev) => prev.filter((m) => m.id !== optimisticMessage.id))
            setError({ code: "SERVER_ERROR", message: "Erro ao enviar mensagem. Tente novamente." })
          } finally {
            if (mountedRef.current) {
              setIsLiaTyping(false)
              setIsSending(false)
            }
            resolve()
          }
        }, DEBOUNCE_MS)
      })
    },
    [isSending, pageState, session?.id, progress, token, config?.voiceMode, setMessages, setIsLiaTyping, setIsSending, setError, setProgress, setSession, setPageState, mountedRef],
  )

  const loadHistory = useCallback(async () => {
    setIsLoadingHistory(true)
    setError(null)

    try {
      const response = await fetchWithRetry(`${API_BASE}/${token}/history`, {
        method: "GET",
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

      if (data.messages && Array.isArray(data.messages)) {
        setMessages((data.messages as Record<string, unknown>[]).map(mapBackendMessage))
      }
      if (data.progress) {
        setProgress(mapBackendProgress(data.progress as Record<string, unknown>))
      }
    } catch {
      if (!mountedRef.current) return
      setError({ code: "SERVER_ERROR", message: "Erro ao carregar hist\u00f3rico." })
    } finally {
      if (mountedRef.current) {
        setIsLoadingHistory(false)
      }
    }
  }, [token, setMessages, setProgress, setError, mountedRef])

  return {
    sendMessage,
    loadHistory,
    isLoadingHistory,
  }
}
