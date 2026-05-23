/**
 * Sprint 3.7 W4-1 — Agent Studio voice hooks (SWR canonical)
 *
 * Hooks canonical para que o cliente final controle o flag de voz por
 * agente custom e inicie chamadas com candidatos.
 *
 * Endpoints backend correspondentes (lia-agent-system):
 *   PATCH /api/v1/agent-studio/agents/{id}/voice/enabled
 *   POST  /api/v1/agent-studio/agents/{id}/voice/initiate
 *   GET   /api/v1/agent-studio/agents/{id}/voice/sessions/{sid}
 *
 * Multi-tenancy canonical: company_id NUNCA enviado no payload — vem do JWT
 * via headers do Next.js proxy.
 */
'use client'

import useSWR, { mutate as globalMutate } from 'swr'
import useSWRMutation from 'swr/mutation'

// ───────────────────────────── tipos canonical ─────────────────────────────

export interface VoiceInitiateRequest {
  candidate_id: string
  candidate_phone?: string
  candidate_name?: string
  job_id?: string
  job_title?: string
  language?: string
}

export interface VoiceInitiateResponse {
  session_id: string
  call_sid: string | null
  is_voip: boolean
  status:
    | 'session_initiated'
    | 'feature_not_enabled'
    | 'agent_voice_disabled'
    | 'session_resumed'
    | 'feature_check_failed'
    | 'error'
    | string
  agent_id: string
  agent_name: string | null
  plugin_name: string | null
}

export interface VoiceSessionStatusResponse {
  session_id: string
  status: 'ringing' | 'in_progress' | 'completed' | 'failed' | 'unknown' | string
  duration_seconds: number
  transcript_segments_count: number
  summary: string | null
  has_transcript: boolean
}

export interface VoiceEnableResponse {
  agent_id: string
  voice_enabled: boolean
}

// ───────────────────────────── fetch helpers ───────────────────────────────

async function jsonFetcher<T>(url: string): Promise<T> {
  const res = await fetch(url)
  if (!res.ok) {
    throw new Error(`Voice API error (HTTP ${res.status})`)
  }
  return (await res.json()) as T
}

async function mutationFetcher<TBody, TResponse>(
  url: string,
  { arg, method }: { arg: TBody; method: 'PATCH' | 'POST' },
): Promise<TResponse> {
  const res = await fetch(url, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(arg),
  })
  const text = await res.text()
  let data: unknown
  try {
    data = text ? JSON.parse(text) : {}
  } catch {
    data = { error: text }
  }
  if (!res.ok) {
    const detail = (data as { detail?: unknown; message?: unknown })?.detail
    const message =
      typeof detail === 'string'
        ? detail
        : `Voice API error (HTTP ${res.status})`
    throw new Error(message)
  }
  return data as TResponse
}

// ───────────────────────────── hooks ────────────────────────────────────────

/**
 * Toggle `voice_enabled` per-agent. Invalida cache de custom-agents pra
 * refletir o novo estado na UI.
 */
export function useToggleAgentVoice(agentId: string) {
  return useSWRMutation<VoiceEnableResponse, Error, string, boolean>(
    `/api/backend-proxy/agent-studio/agents/${encodeURIComponent(agentId)}/voice/enabled`,
    async (url: string, { arg }: { arg: boolean }) => {
      const data = await mutationFetcher<{ voice_enabled: boolean }, VoiceEnableResponse>(
        url,
        { arg: { voice_enabled: arg }, method: 'PATCH' },
      )
      // Invalida lista de agentes (qualquer chave começando com /api/backend-proxy/custom-agents)
      await globalMutate(
        (key) => typeof key === 'string' && key.startsWith('/api/backend-proxy/custom-agents'),
        undefined,
        { revalidate: true },
      )
      return data
    },
  )
}

/**
 * Iniciar chamada de voz com candidato. Backend devolve status drives UI
 * (session_initiated | agent_voice_disabled | feature_not_enabled | error).
 */
export function useInitiateVoiceCall(agentId: string) {
  return useSWRMutation<VoiceInitiateResponse, Error, string, VoiceInitiateRequest>(
    `/api/backend-proxy/agent-studio/agents/${encodeURIComponent(agentId)}/voice/initiate`,
    async (url: string, { arg }: { arg: VoiceInitiateRequest }) =>
      mutationFetcher<VoiceInitiateRequest, VoiceInitiateResponse>(
        url,
        { arg, method: 'POST' },
      ),
  )
}

/**
 * Polling-friendly status read. Use `refreshInterval` no consumer (típico 3-5s).
 */
export function useVoiceSessionStatus(
  agentId: string,
  sessionId: string | null | undefined,
  options?: { refreshInterval?: number; enabled?: boolean },
) {
  const enabled = options?.enabled !== false && Boolean(agentId && sessionId)
  const url = enabled
    ? `/api/backend-proxy/agent-studio/agents/${encodeURIComponent(
        agentId,
      )}/voice/sessions/${encodeURIComponent(sessionId ?? '')}`
    : null
  return useSWR<VoiceSessionStatusResponse>(url, jsonFetcher, {
    refreshInterval: options?.refreshInterval,
  })
}
