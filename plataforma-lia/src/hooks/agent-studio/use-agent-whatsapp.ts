/**
 * T5a UX Transformação 5 — Agent Studio WhatsApp hooks (SWR canonical)
 *
 * Hooks canonical para que o cliente final controle o flag de WhatsApp por
 * agente custom e inicie conversas com candidatos via WhatsApp.
 *
 * Endpoints backend correspondentes (lia-agent-system):
 *   PATCH /api/v1/agent-studio/agents/{id}/whatsapp/enabled
 *   POST  /api/v1/agent-studio/agents/{id}/whatsapp/initiate
 *
 * Multi-tenancy canonical: company_id NUNCA enviado no payload — vem do JWT
 * via headers do Next.js proxy.
 *
 * Pattern reference: src/hooks/agent-studio/use-agent-voice.ts (Sprint 3.7 W4-1)
 */
'use client'

import { mutate as globalMutate } from 'swr'
import useSWRMutation from 'swr/mutation'

// ───────────────────────────── tipos canonical ─────────────────────────────

export interface WhatsAppInitiateRequest {
  candidate_id: string
  candidate_phone: string
  candidate_name?: string
  message: string
  job_id?: string
  job_title?: string
  session_id?: string
}

export interface WhatsAppInitiateResponse {
  agent_id: string
  agent_name: string | null
  plugin_name: string | null
  status:
    | 'message_sent'
    | 'send_failed'
    | 'agent_whatsapp_disabled'
    | 'whatsapp_missing_company_id'
    | 'whatsapp_missing_sender_phone'
    | 'whatsapp_empty_message'
    | 'error'
    | string
  response_text: string | null
  delivery_status: string | null
  delivery_message_id: string | null
  delivery_error: string | null
  session_id: string | null
}

export interface WhatsAppEnableResponse {
  agent_id: string
  whatsapp_enabled: boolean
}

// ───────────────────────────── fetch helpers ───────────────────────────────

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
        : `WhatsApp API error (HTTP ${res.status})`
    throw new Error(message)
  }
  return data as TResponse
}

// ───────────────────────────── hooks ────────────────────────────────────────

/**
 * Toggle `whatsapp_enabled` per-agent. Invalida cache de custom-agents pra
 * refletir o novo estado na UI.
 */
export function useToggleAgentWhatsApp(agentId: string) {
  return useSWRMutation<WhatsAppEnableResponse, Error, string, boolean>(
    `/api/backend-proxy/agent-studio/agents/${encodeURIComponent(agentId)}/whatsapp/enabled`,
    async (url: string, { arg }: { arg: boolean }) => {
      const data = await mutationFetcher<{ whatsapp_enabled: boolean }, WhatsAppEnableResponse>(
        url,
        { arg: { whatsapp_enabled: arg }, method: 'PATCH' },
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
 * Iniciar conversa WhatsApp com candidato. Backend devolve status drives UI
 * (message_sent | send_failed | agent_whatsapp_disabled | error).
 */
export function useInitiateWhatsAppConversation(agentId: string) {
  return useSWRMutation<WhatsAppInitiateResponse, Error, string, WhatsAppInitiateRequest>(
    `/api/backend-proxy/agent-studio/agents/${encodeURIComponent(agentId)}/whatsapp/initiate`,
    async (url: string, { arg }: { arg: WhatsAppInitiateRequest }) =>
      mutationFetcher<WhatsAppInitiateRequest, WhatsAppInitiateResponse>(
        url,
        { arg, method: 'POST' },
      ),
  )
}
