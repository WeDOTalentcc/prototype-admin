// Onda C4.2 (2026-05-29) — hook canonical Daily Digest / Morning Brief.
//
// Consome GET /api/backend-proxy/agent-monitoring/daily-digest (Onda C4.2).
// Usado por: MorningDigest no topo da Sala de Controle do Studio.
//
// React Query canonical. staleTime 5min — o digest é um resumo de "o que
// aconteceu enquanto você não estava", não precisa de polling agressivo.
"use client"

import { useQuery } from "@tanstack/react-query"

import type { DailyDigestResponse } from "@/types/agents/daily-digest"

export const DAILY_DIGEST_QUERY_KEY = (sinceHours: number, limit: number) =>
  ["agent-monitoring", "daily-digest", sinceHours, limit] as const

interface UseDailyDigestOptions {
  /** Janela de tempo em horas (default 24). */
  sinceHours?: number
  /** Máximo de items curados (default 8). */
  limit?: number
  enabled?: boolean
}

async function fetchDailyDigest(
  sinceHours: number,
  limit: number,
): Promise<DailyDigestResponse> {
  const token =
    typeof window !== "undefined" ? localStorage.getItem("auth_token") : null
  const url = `/api/backend-proxy/agent-monitoring/daily-digest?since_hours=${sinceHours}&limit=${limit}`
  const res = await fetch(url, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    signal: AbortSignal.timeout(8_000),
  })
  if (!res.ok) {
    throw new Error(`Failed to fetch daily digest: ${res.status}`)
  }
  return res.json()
}

export function useDailyDigest(opts: UseDailyDigestOptions = {}) {
  const sinceHours = opts.sinceHours ?? 24
  const limit = opts.limit ?? 8
  return useQuery<DailyDigestResponse, Error>({
    queryKey: DAILY_DIGEST_QUERY_KEY(sinceHours, limit),
    queryFn: () => fetchDailyDigest(sinceHours, limit),
    staleTime: 5 * 60_000,
    enabled: opts.enabled ?? true,
  })
}
