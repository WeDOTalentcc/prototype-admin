/**
 * W-Channels-A (2026-05-23) — Agent Studio channel hooks (SWR canonical)
 *
 * Hook unificado canonical para os 4 canais do mental model Paulo
 * (Opção B, decisão 2026-05-23):
 *
 *   - in_app    : chat lateral interno (default ligado)
 *   - whatsapp  : WhatsApp
 *   - voice     : ligação telefônica (PSTN, Twilio outbound)
 *   - voip      : voz no navegador (Twilio VoIP SDK + Gemini Live)
 *
 * Cada um é independente — cliente pode habilitar/desabilitar em qualquer
 * combinação. Multi-tenancy canonical: company_id NUNCA enviado no payload,
 * vem do JWT via headers do Next.js proxy.
 *
 * Endpoints backend correspondentes (lia-agent-system):
 *   PATCH /api/v1/agent-studio/agents/{id}/in_app/enabled
 *   PATCH /api/v1/agent-studio/agents/{id}/whatsapp/enabled
 *   PATCH /api/v1/agent-studio/agents/{id}/voice/enabled
 *   PATCH /api/v1/agent-studio/agents/{id}/voip/enabled
 *
 * Refs:
 *   use-agent-voice.ts (Sprint 3.7 W4-1) — pattern de origem
 *   use-agent-whatsapp.ts (T5a)
 */
'use client'

import { mutate as globalMutate } from 'swr'
import useSWRMutation from 'swr/mutation'

// ───────────────────────────── tipos canonical ─────────────────────────────

export type AgentChannel = 'in_app' | 'whatsapp' | 'voice' | 'voip'

export interface ChannelEnableResponse {
  agent_id: string
  // Backend retorna SEMPRE o flag específico do canal (voice_enabled, voip_enabled, etc).
  // O hook expõe a chave canonical e tolera as 4 formas — TS união discriminada.
  voice_enabled?: boolean
  voip_enabled?: boolean
  in_app_enabled?: boolean
  whatsapp_enabled?: boolean
}

// ───────────────────────────── fetch helper ────────────────────────────────

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
        : `Agent channel API error (HTTP ${res.status})`
    throw new Error(message)
  }
  return data as TResponse
}

// ───────────────────────────── hook canonical ──────────────────────────────

/**
 * Toggle qualquer um dos 4 canais per-agent. Invalida cache de custom-agents
 * para refletir o novo estado na UI.
 *
 * @param agentId UUID do custom agent
 * @param channel 'in_app' | 'whatsapp' | 'voice' | 'voip'
 *
 * @example
 *   const toggleInApp = useToggleAgentChannel(agent.id, 'in_app')
 *   toggleInApp.trigger(true)  // → habilita chat lateral
 */
export function useToggleAgentChannel(agentId: string, channel: AgentChannel) {
  const url = `/api/backend-proxy/agent-studio/agents/${encodeURIComponent(agentId)}/${channel}/enabled`
  const bodyKey = `${channel}_enabled` as const
  return useSWRMutation<ChannelEnableResponse, Error, string, boolean>(
    url,
    async (u: string, { arg }: { arg: boolean }) => {
      const body = { [bodyKey]: arg } as Record<string, boolean>
      const data = await mutationFetcher<typeof body, ChannelEnableResponse>(
        u,
        { arg: body, method: 'PATCH' },
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
