"use client"

import { useState, useCallback, useRef, useEffect } from "react"
import type {
  TriagemSession,
  TriagemConfig,
  TriagemMessage,
  TriagemError,
  TriagemPageState,
  WSIProgress,
  TriagemCompletionSummary,
  SendMessagePayload,
  UseTriagemChatReturn,
} from "@/components/triagem/types"

const API_BASE = "/api/backend-proxy/triagem"
const DEBOUNCE_MS = 300
const TIMEOUT_MS = 30000
const MAX_RETRIES = 2
const LOCAL_STORAGE_KEY_PREFIX = "triagem_state_"

function base64ToAudioUrl(base64Data: string): string {
  const binaryStr = atob(base64Data)
  const bytes = new Uint8Array(binaryStr.length)
  for (let i = 0; i < binaryStr.length; i++) {
    bytes[i] = binaryStr.charCodeAt(i)
  }
  const blob = new Blob([bytes], { type: "audio/mp3" })
  return URL.createObjectURL(blob)
}

function mapBackendMessage(raw: Record<string, unknown>): TriagemMessage {
  let audioUrl: string | null = (raw.audio_url as string) ?? (raw.audioUrl as string) ?? null
  if (!audioUrl && raw.audio_base64) {
    try {
      audioUrl = base64ToAudioUrl(raw.audio_base64 as string)
    } catch {
      /* ignore decode errors */
    }
  }
  return {
    id: String(raw.id ?? ""),
    sessionId: String(raw.session_id ?? raw.sessionId ?? ""),
    role: (raw.sender as string) === "lia" || (raw.sender as string) === "candidate"
      ? (raw.sender as "lia" | "candidate")
      : (raw.role as "lia" | "candidate") ?? "lia",
    type: (raw.message_type as string) ?? (raw.type as string) ?? "text",
    content: String(raw.content ?? ""),
    options: (raw.options as TriagemMessage["options"]) ?? null,
    selectedOption: (raw.selected_option as string) ?? (raw.selectedOption as string) ?? null,
    likertValue: (raw.likert_value as number) ?? (raw.likertValue as number) ?? null,
    likertLabels: (raw.likert_labels as string[]) ?? (raw.likertLabels as string[]) ?? null,
    timestamp: String(raw.created_at ?? raw.timestamp ?? new Date().toISOString()),
    blockIndex: (raw.wsi_block as number) ?? (raw.blockIndex as number) ?? null,
    blockName: (raw.block_name as string) ?? (raw.blockName as string) ?? null,
    audioUrl,
  }
}

function mapBackendProgress(raw: Record<string, unknown>): WSIProgress {
  return {
    currentBlock: (raw.current_block as number) ?? (raw.currentBlock as number) ?? 0,
    totalBlocks: (raw.total_blocks as number) ?? (raw.totalBlocks as number) ?? 7,
    currentBlockName: String(raw.block_name ?? raw.currentBlockName ?? ""),
    questionsAnswered: (raw.questions_answered as number) ?? (raw.questionsAnswered as number) ?? 0,
    totalQuestions: (raw.total_questions as number) ?? (raw.totalQuestions as number) ?? 0,
    estimatedMinutesRemaining: (raw.estimated_minutes_remaining as number) ?? (raw.estimatedMinutesRemaining as number) ?? 0,
  }
}

function mapBackendSession(raw: Record<string, unknown>): TriagemSession {
  const progress = raw.progress
    ? mapBackendProgress(raw.progress as Record<string, unknown>)
    : {
        currentBlock: (raw.current_block as number) ?? 0,
        totalBlocks: (raw.total_blocks as number) ?? 7,
        currentBlockName: "",
        questionsAnswered: 0,
        totalQuestions: 0,
        estimatedMinutesRemaining: 0,
      }
  return {
    id: String(raw.id ?? ""),
    token: String(raw.token ?? ""),
    status: (raw.status as TriagemSession["status"]) ?? "invited",
    candidateId: String(raw.candidate_id ?? raw.candidateId ?? ""),
    candidateName: String(raw.candidate_name ?? raw.candidateName ?? ""),
    jobId: String(raw.job_id ?? raw.jobId ?? ""),
    jobTitle: String(raw.job_title ?? raw.jobTitle ?? ""),
    companyName: String(raw.company_name ?? raw.companyName ?? ""),
    companyLogoUrl: (raw.company_logo_url as string) ?? (raw.companyLogoUrl as string) ?? null,
    progress,
    createdAt: String(raw.created_at ?? raw.createdAt ?? ""),
    expiresAt: String(raw.expires_at ?? raw.expiresAt ?? ""),
    startedAt: (raw.started_at as string) ?? (raw.startedAt as string) ?? null,
    completedAt: (raw.completed_at as string) ?? (raw.completedAt as string) ?? null,
    wsiFinalScore: (raw.wsi_final_score as number) ?? (raw.wsiFinalScore as number) ?? null,
    recommendation: (raw.recommendation as TriagemSession["recommendation"]) ?? null,
  }
}

interface LocalPersistedState {
  messages: TriagemMessage[]
  pageState: TriagemPageState
}

function getStorageKey(token: string): string {
  return `${LOCAL_STORAGE_KEY_PREFIX}${token}`
}

function loadPersistedState(token: string): LocalPersistedState | null {
  try {
    const raw = localStorage.getItem(getStorageKey(token))
    if (!raw) return null
    return JSON.parse(raw) as LocalPersistedState
  } catch {
    return null
  }
}

function persistState(token: string, state: LocalPersistedState): void {
  try {
    localStorage.setItem(getStorageKey(token), JSON.stringify(state))
  } catch {
    /* storage full or unavailable */
  }
}

async function fetchWithTimeout(
  url: string,
  options: RequestInit,
  timeoutMs: number = TIMEOUT_MS,
): Promise<Response> {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeoutMs)
  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
    })
    return response
  } finally {
    clearTimeout(timer)
  }
}

async function fetchWithRetry(
  url: string,
  options: RequestInit,
  retries: number = MAX_RETRIES,
): Promise<Response> {
  let lastError: unknown
  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const response = await fetchWithTimeout(url, options)
      if (response.ok || response.status < 500) {
        return response
      }
      lastError = new Error(`Server error: ${response.status}`)
    } catch (err) {
      lastError = err
      if (attempt < retries) {
        await new Promise((resolve) => setTimeout(resolve, 1000 * (attempt + 1)))
      }
    }
  }
  throw lastError
}

function extractErrorMessage(body: Record<string, unknown>): string | undefined {
  return (body.detail as string) || (body.message as string) || undefined
}

function mapErrorResponse(status: number, body: Record<string, unknown>): TriagemError {
  const raw = extractErrorMessage(body)
  const isGeneric = !raw || raw === "Not Found" || raw === "Internal Server Error"
  const msg = isGeneric ? undefined : raw
  if (status === 404) {
    return { code: "TOKEN_INVALID", message: msg || "Token inválido ou não encontrado. Verifique o link recebido." }
  }
  if (status === 410) {
    return { code: "TOKEN_EXPIRED", message: msg || "Este link expirou. Solicite um novo convite ao recrutador." }
  }
  if (status === 409) {
    return { code: "SESSION_COMPLETED", message: msg || "Esta triagem já foi concluída." }
  }
  if (status === 429) {
    return { code: "RATE_LIMITED", message: msg || "Muitas requisições. Tente novamente em instantes." }
  }
  return { code: "SERVER_ERROR", message: msg || "Erro interno. Tente novamente." }
}

export function useTriagemChat(token: string): UseTriagemChatReturn {
  const [pageState, setPageState] = useState<TriagemPageState>("loading")
  const [session, setSession] = useState<TriagemSession | null>(null)
  const [config, setConfig] = useState<TriagemConfig | null>(null)
  const [messages, setMessages] = useState<TriagemMessage[]>([])
  const [progress, setProgress] = useState<WSIProgress | null>(null)
  const [error, setError] = useState<TriagemError | null>(null)
  const [completionSummary, setCompletionSummary] = useState<TriagemCompletionSummary | null>(null)
  const [isLiaTyping, setIsLiaTyping] = useState(false)
  const [isSending, setIsSending] = useState(false)
  const [isLoadingHistory, setIsLoadingHistory] = useState(false)

  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const mountedRef = useRef(true)

  useEffect(() => {
    mountedRef.current = true
    return () => {
      mountedRef.current = false
      if (debounceRef.current) {
        clearTimeout(debounceRef.current)
      }
    }
  }, [])

  useEffect(() => {
    if (messages.length > 0 && pageState !== "loading" && pageState !== "error") {
      persistState(token, { messages, pageState })
    }
  }, [messages, pageState, token])

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
        const persisted = loadPersistedState(token)
        if (persisted && persisted.messages.length > 0) {
          setMessages(persisted.messages)
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
          ? "Tempo limite excedido. Verifique sua conexão."
          : "Não foi possível carregar a triagem. Tente novamente.",
      })
      setPageState("error")
    }
  }, [token])

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
    [isSending, pageState, session?.id, progress, token, config?.voiceMode],
  )

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

      try {
        localStorage.removeItem(getStorageKey(token))
      } catch {
        /* ignore */
      }
    } catch {
      if (!mountedRef.current) return
      setError({ code: "SERVER_ERROR", message: "Erro ao finalizar triagem. Tente novamente." })
    } finally {
      if (mountedRef.current) {
        setIsSending(false)
      }
    }
  }, [token])

  const reviewSession = useCallback(() => {
    setPageState("chat")
  }, [])

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
      setError({ code: "SERVER_ERROR", message: "Erro ao carregar histórico." })
    } finally {
      if (mountedRef.current) {
        setIsLoadingHistory(false)
      }
    }
  }, [token])

  return {
    pageState,
    session,
    config,
    messages,
    progress,
    error,
    completionSummary,
    isLiaTyping,
    isSending,
    isLoadingHistory,
    initSession,
    startChat,
    sendMessage,
    completeSession,
    reviewSession,
    loadHistory,
  }
}
