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
  MessageCompleteExtras,
} from "./lia-chat-connection-types"
import { maskPII, formatMessageTime } from "./lia-chat-connection-types"

import type { TransportMode } from "./lia-chat-connection-types"

export interface UseChatMessagesOptions {
  sessionId: string
  isConnected: boolean
  transportMode: TransportMode
  wsSend: (content: string, context: Record<string, unknown>, domain: string) => boolean
  sendRaw: (data: Record<string, unknown>) => void
  clearTokens: () => void
  sendMessageViaSSE: (
    sessionId: string,
    message: string,
    domain?: string,
    context?: Record<string, unknown>,
    conversationId?: string | null,
  ) => void
  /** Task #383 (F2): tick contador de eventos WS — usado pelo watchdog que cai
   *  pra REST quando o `wsSend` é aceito mas nenhum evento chega de volta. */
  wsEventTickRef?: React.MutableRefObject<number>
  hitlRef: React.MutableRefObject<HITLPending | null>
  setHitlPending: React.Dispatch<React.SetStateAction<HITLPending | null>>
  onMessageComplete?: (
    content: string,
    executionPlan?: Record<string, unknown>,
    extras?: MessageCompleteExtras,
  ) => void
  conversationIdFromWs: string | null
  /** Setter de isThinking do socket — usado para acender o indicador "LIA digitando" também nos caminhos REST/SSE (BUG-13). */
  setIsThinking?: React.Dispatch<React.SetStateAction<boolean>>
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
  transportMode,
  wsSend,
  sendRaw,
  clearTokens,
  sendMessageViaSSE,
  wsEventTickRef,
  hitlRef,
  setHitlPending,
  onMessageComplete,
  conversationIdFromWs,
  setIsThinking,
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
      } else if (path.includes("/agent-studio")) {
        ctx.page_type = "agent_studio"
      } else if (path.includes("/minha-empresa") || path.includes("/company-settings")) {
        ctx.page_type = "settings_config"
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

  const sendViaRest = useCallback(async (
    content: string,
    domain: string,
    context: Record<string, unknown>,
  ) => {
    setIsThinking?.(true)
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

      // Trata erros HTTP antes de tentar interpretar o body — sem isso, um
      // 401 do middleware (dev-auto-login falhou) ou um 5xx do backend cai no
      // ramo "data.content é undefined" e a UI fica em silent drop (Task #377).
      if (!res.ok) {
        let errorMessage: string
        if (res.status === 401 || res.status === 403) {
          errorMessage = "Erro de autenticação. Faça login novamente."
        } else if (res.status >= 500) {
          errorMessage = `Erro do servidor (HTTP ${res.status}). Tente novamente.`
        } else {
          errorMessage = `Erro ao enviar mensagem (HTTP ${res.status}). Tente novamente.`
        }
        onCompleteRef.current?.(errorMessage)
        return
      }

      type ChatResponse = {
        content?: string
        conversation_id?: string
        needs_clarification?: boolean
        clarification_question?: string
        clarification_options?: Array<string | { label?: string; value?: string }>
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
      let data: ChatResponse
      try {
        data = (await res.json()) as ChatResponse
      } catch {
        onCompleteRef.current?.("Resposta inválida do servidor. Tente novamente.")
        return
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

      // Tier 8 clarification fallback from the cascaded router — render the
      // question as a LIA message with clickable option chips.
      if (data.needs_clarification && data.clarification_question) {
        const optionsArr = (data.clarification_options ?? []).map((opt) => {
          if (typeof opt === "string") return { label: opt, value: opt }
          return { label: opt.label ?? opt.value ?? "", value: opt.value ?? opt.label ?? "" }
        }).filter((o) => o.label && o.value)
        onCompleteRef.current?.(data.clarification_question, undefined, {
          options: optionsArr,
          isClarification: true,
        })
        return
      }

      if (data.content) {
        onCompleteRef.current?.(data.content)
      } else if (!pendingAction?.awaiting_confirmation) {
        // JSON 2xx mas sem `content` e sem outro caminho de UI — antes desta
        // correção (Task #377) o spinner sumia e nenhuma bolha aparecia.
        onCompleteRef.current?.("A LIA não retornou uma resposta. Tente novamente.")
      }
    } catch {
      onCompleteRef.current?.("Erro ao conectar com a LIA. Tente novamente.")
    } finally {
      // No caminho WS, o indicador é desligado pelo evento "message" do socket.
      // Aqui (REST) precisamos garantir que ele desliga ao final.
      setIsThinking?.(false)
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId, conversationId, hitlRef, setHitlPending, setIsThinking])

  // Task #383 (F2): timeout para "WS aceitou send mas nunca respondeu". O
  // backend costuma emitir `thinking` em ~200ms; se nada chegar em N segundos,
  // assumimos que o frame foi engolido (proxy/edge/buffer) e caímos pro REST.
  // Pode ser sobrescrito em testes via `window.__LIA_WS_RESPONSE_TIMEOUT_MS`.
  const getWsTimeoutMs = useCallback((): number => {
    if (typeof window !== "undefined") {
      const override = (window as unknown as { __LIA_WS_RESPONSE_TIMEOUT_MS?: number }).__LIA_WS_RESPONSE_TIMEOUT_MS
      if (typeof override === "number" && override > 0) return override
    }
    return 8000
  }, [])

  const sendMessage = useCallback(async (content: string, domain = "", scope?: string) => {
    clearTokens()
    // BUG-13: acender "LIA digitando" imediatamente — no caminho WS isso seria
    // feito pelo evento "thinking", mas em REST/SSE (e até a primeira resposta
    // do WS chegar) o indicador ficava invisível, dando sensação de chat morto.
    setIsThinking?.(true)
    const context: Record<string, unknown> = scope ? { scope } : {}
    if (conversationId) {
      context.conversation_id = conversationId
    }

    const pageContext = getPageContext()
    Object.assign(context, pageContext)

    if (isConnected && transportMode === "ws") {
      // Task #383 (F2): tira snapshot do tick ANTES do send. Se nenhum evento
      // WS chegar dentro do timeout, caímos pro REST + bolha de aviso.
      const tickAtSend = wsEventTickRef?.current ?? 0
      const accepted = wsSend(content, context, domain)
      if (!accepted) {
        // Socket entrou em CLOSING/CLOSED entre o `isConnected=true` e o send —
        // não fica preso no spinner; vai direto pro REST.
        await sendViaRest(content, domain, context)
        return
      }

      const timeoutMs = getWsTimeoutMs()
      setTimeout(() => {
        // Se algum evento (thinking/message/error/...) chegou, o tick mudou e
        // a resposta normal está no caminho — não fazemos nada.
        if (!wsEventTickRef || wsEventTickRef.current !== tickAtSend) return
        // Caso contrário: o WS engoliu o send. Avisa o usuário e reenvia REST.
        onCompleteRef.current?.(
          "Conexão instável com a LIA. Tentando novamente...",
        )
        void sendViaRest(content, domain, context)
      }, timeoutMs)
      return
    }

    if (isConnected && transportMode === "sse") {
      sendMessageViaSSE(sessionId, content, domain || "recruiter_assistant", context, conversationId)
      return
    }

    await sendViaRest(content, domain, context)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [wsSend, clearTokens, isConnected, transportMode, sessionId, conversationId, getPageContext, sendMessageViaSSE, setIsThinking, sendViaRest, wsEventTickRef, getWsTimeoutMs])

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
