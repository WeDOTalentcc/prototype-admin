/**
 * Workstream A 2026-05-23 — Agent Studio Triagem Invite hooks (SWR canonical).
 *
 * Hooks canonical para o 4o toggle per-agent: capability "criar convite triagem
 * candidato". Quando habilitada, o agente pode gerar token unico + URL publica
 * (/triagem/{token}) e disparar delivery via email/WhatsApp.
 *
 * Para o TOGGLE on/off, use ``useToggleAgentChannel(agentId, 'triagem_invite')``
 * (canonical em use-agent-channel.ts). Este modulo expoe apenas o hook de
 * INITIATE (criar convite), separado por simetria com use-agent-whatsapp.ts +
 * use-agent-voice.ts.
 *
 * Endpoints backend correspondentes (lia-agent-system):
 *   POST  /api/v1/agent-studio/agents/{id}/triagem-invite/initiate
 *
 * Multi-tenancy canonical: company_id NUNCA enviado no payload — vem do JWT
 * via headers do Next.js proxy.
 *
 * Pattern reference:
 *   src/hooks/agent-studio/use-agent-whatsapp.ts (T5a) — initiate semantic
 *   src/hooks/agent-studio/use-agent-voice.ts (Sprint 3.7 W4-1)
 */
'use client'

import useSWRMutation from 'swr/mutation'

// ───────────────────────────── tipos canonical ─────────────────────────────

export interface TriagemInviteInitiateRequest {
  candidate_id: string
  job_id: string
  candidate_name?: string
  candidate_email?: string
  job_title?: string
  company_name?: string
  company_logo_url?: string
  invite_channel?: 'email' | 'whatsapp' | string
  expires_days?: number
  voice_mode?: boolean
}

export interface TriagemInviteInitiateResponse {
  agent_id: string
  agent_name: string | null
  status:
    | 'invite_created'
    | 'agent_triagem_invite_disabled'
    | 'error'
    | string
  token: string | null
  expires_at: string | null
  invite_url: string | null
  triagem_url: string | null
  session_id: string | null
}

// ───────────────────────────── fetch helper ────────────────────────────────

async function mutationFetcher<TBody, TResponse>(
  url: string,
  { arg, method }: { arg: TBody; method: 'POST' },
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
        : typeof (detail as { message?: unknown })?.message === 'string'
          ? (detail as { message: string }).message
          : `Triagem Invite API error (HTTP ${res.status})`
    throw new Error(message)
  }
  return data as TResponse
}

// ───────────────────────────── hook canonical ──────────────────────────────

/**
 * Inicia criacao de convite triagem candidato via agente. Backend devolve
 * ``status`` que dirige a UI (``invite_created`` | ``agent_triagem_invite_disabled``
 * | ``error``) + ``invite_url`` para compartilhar com o candidato.
 *
 * @example
 *   const initiateInvite = useInitiateAgentTriagemInvite(agent.id)
 *   const result = await initiateInvite.trigger({
 *     candidate_id: 'cand-1', job_id: 'job-1', invite_channel: 'email',
 *   })
 *   if (result.status === 'invite_created') {
 *     navigator.clipboard.writeText(result.invite_url!)
 *   }
 */
export function useInitiateAgentTriagemInvite(agentId: string) {
  return useSWRMutation<
    TriagemInviteInitiateResponse,
    Error,
    string,
    TriagemInviteInitiateRequest
  >(
    `/api/backend-proxy/agent-studio/agents/${encodeURIComponent(agentId)}/triagem-invite/initiate`,
    async (url: string, { arg }: { arg: TriagemInviteInitiateRequest }) =>
      mutationFetcher<TriagemInviteInitiateRequest, TriagemInviteInitiateResponse>(
        url,
        { arg, method: 'POST' },
      ),
  )
}
