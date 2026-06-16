"use client"

/**
 * F-B: Unified transition chat hook — REST (default) or SSE (flag-gated).
 *
 * Always calls both underlying hooks (Rules of Hooks compliance).
 * Activates the SSE path when NEXT_PUBLIC_LIA_TRANSITION_VIA_SSE=true.
 *
 * SSE path advantages over REST:
 *   - HITL per-session (not global useLiaChatContext)
 *   - Streaming tokens + AgentActivityTimeline
 *   - RRP (reasoning/tool events)
 *   - PipelineTransitionAgent full 20-tool stack
 */

import { useState, useCallback, useRef } from 'react'
import {
  useInterpretContext,
  type InterpretChatMessage as ChatMessage,
  type TaskItem,
  type LearnedSuggestion,
} from './use-interpret-context'
import { useChatTransport, type TransportEvent } from '@/hooks/chat/useChatTransport'

export type { ChatMessage, TaskItem, LearnedSuggestion }

export interface TransitionParams {
  candidate_id: string
  candidate_name?: string
  job_title?: string
  job_id?: string
  from_stage: string
  to_stage: string
  action_behavior: string
  company_id?: string
}

export interface HitlPendingState {
  pending_id: string
  action: string
  description: string
}

function makeSessionId(): string {
  return `tc-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 6)}`
}

const SSE_ENABLED =
  typeof process !== 'undefined' &&
  process.env.NEXT_PUBLIC_LIA_TRANSITION_VIA_SSE === 'true'

export function useTransitionChat() {
  // ─── SSE path state ────────────────────────────────────────────────────
  const sessionIdRef = useRef<string>(makeSessionId())
  const [sseMessages, setSseMessages] = useState<ChatMessage[]>([])
  const [sseLoading, setSseLoading] = useState(false)
  const [hitlPending, setHitlPending] = useState<HitlPendingState | null>(null)
  const sseConvIdRef = useRef<string | null>(null)
  const currentTokensRef = useRef('')
  const lastParamsRef = useRef<TransitionParams | null>(null)

  const handleSseEvent = useCallback((event: TransportEvent) => {
    switch (event.type) {
      case 'thinking':
        setSseLoading(true)
        currentTokensRef.current = ''
        break
      case 'token':
        if (typeof event.content === 'string') {
          currentTokensRef.current += event.content
        }
        break
      case 'token_done':
        setSseLoading(false)
        break
      case 'message': {
        setSseLoading(false)
        const text =
          (typeof event.content === 'string' && event.content) ||
          currentTokensRef.current
        currentTokensRef.current = ''
        if (!text) break
        const meta: ChatMessage['metadata'] = {}
        if (typeof event.confidence === 'number') meta.confidence = event.confidence
        if (Array.isArray(event.fairness_warnings) && event.fairness_warnings.length) {
          meta.fairness_result = {
            is_fair: false,
            warnings: event.fairness_warnings as string[],
          }
        }
        const evData = event.data as Record<string, unknown> | undefined
        if (evData?.out_of_scope) meta.out_of_scope = true
        setSseMessages(prev => [
          ...prev,
          { role: 'lia', content: text, timestamp: Date.now(), metadata: meta },
        ])
        break
      }
      case 'approval_required':
        setHitlPending({
          pending_id: (event.pending_id as string) || '',
          action: (event.action as string) || 'pipeline_transition',
          description: (event.description as string) || 'Confirmar ação',
        })
        setSseLoading(false)
        break
      case 'approval_result':
        setHitlPending(null)
        break
      case 'error': {
        setSseLoading(false)
        const errText =
          (typeof event.message === 'string' && event.message) ||
          'Erro ao processar mensagem.'
        setSseMessages(prev => [
          ...prev,
          { role: 'lia', content: errText, timestamp: Date.now() },
        ])
        break
      }
    }
  }, [])

  const { sendMessageViaSSE } = useChatTransport(
    sessionIdRef.current,
    {},
    handleSseEvent,
  )

  const sseSendMessage = useCallback(
    (userMsg: string, params: Omit<TransitionParams, 'prompt' | 'message_history'>) => {
      lastParamsRef.current = params
      setSseMessages(prev => [
        ...prev,
        { role: 'user', content: userMsg, timestamp: Date.now() },
      ])
      setSseLoading(true)
      sendMessageViaSSE(
        sessionIdRef.current,
        userMsg,
        'pipeline_transition',
        {
          action_behavior: params.action_behavior,
          candidate_id: params.candidate_id,
          candidate_name: params.candidate_name ?? '',
          job_id: params.job_id ?? '',
          job_title: params.job_title ?? '',
          from_stage: params.from_stage,
          to_stage: params.to_stage,
          company_id: params.company_id ?? '',
        },
        sseConvIdRef.current,
      )
    },
    [sendMessageViaSSE],
  )

  const sseSendApproval = useCallback(
    (approved: boolean) => {
      const pending = hitlPending
      const p = lastParamsRef.current
      setHitlPending(null)
      if (!approved || !pending || !p) return
      sendMessageViaSSE(
        sessionIdRef.current,
        '[HITL_APPROVED]',
        'pipeline_transition',
        {
          action_behavior: p.action_behavior,
          candidate_id: p.candidate_id,
          candidate_name: p.candidate_name ?? '',
          job_id: p.job_id ?? '',
          job_title: p.job_title ?? '',
          from_stage: p.from_stage,
          to_stage: p.to_stage,
          company_id: p.company_id ?? '',
          approve_pending_id: pending.pending_id,
          hitl_approved: true,
        },
        sseConvIdRef.current,
      )
    },
    [hitlPending, sendMessageViaSSE],
  )

  const sseReset = useCallback(() => {
    setSseMessages([])
    setSseLoading(false)
    setHitlPending(null)
    currentTokensRef.current = ''
    lastParamsRef.current = null
    sseConvIdRef.current = null
    sessionIdRef.current = makeSessionId()
  }, [])

  // ─── REST path (always called — Rules of Hooks) ─────────────────────────
  const {
    sendMessage: restSendMessage,
    messages: restMessages,
    result: restResult,
    isLoading: restLoading,
    reset: restReset,
  } = useInterpretContext()

  // ─── Return active transport ─────────────────────────────────────────────
  if (SSE_ENABLED) {
    return {
      sendMessage: sseSendMessage,
      messages: sseMessages,
      result: null,
      isLoading: sseLoading,
      reset: sseReset,
      hitlPending,
      sendApproval: sseSendApproval,
    }
  }

  return {
    sendMessage: restSendMessage,
    messages: restMessages,
    result: restResult,
    isLoading: restLoading,
    reset: restReset,
    hitlPending: null as HitlPendingState | null,
    sendApproval: (_approved: boolean) => { /* REST has no per-session HITL */ },
  }
}
