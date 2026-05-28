// Onda 2 F1 (2026-05-27) — hook canonical Studio surface presence.
//
// Consome GET /api/backend-proxy/agent-monitoring/active-summary (Onda 2 B1).
// Usado por: AgentsCard no Decidir (F2), banner global (F3), pingo pulsante
// no Funil (F7), pingo no header da aba Agentes do Pool (F6).
//
// React Query canonical (mesma stack do DecisionTreeDrawer Onda 1).
// Polling 10s (menos agressivo que Sala de Controle 5s — Decidir é background).
// staleTime 5s impede dedup ruido entre surfaces que compartilham query key.
"use client"

import { useQuery } from "@tanstack/react-query"
import type {
  ActiveAgentSurface,
  ActiveSummaryResponse,
} from "@/types/agents/active-summary"

export const ACTIVE_AGENTS_SUMMARY_QUERY_KEY = (
  surface: ActiveAgentSurface,
  limit: number,
) => ["agent-monitoring", "active-summary", surface, limit] as const

interface UseActiveAgentsSummaryOptions {
  surface?: ActiveAgentSurface
  limit?: number
  enabled?: boolean
  /** Override polling em ms. Default 10_000 (10s). */
  refetchInterval?: number | false
}

async function fetchActiveSummary(
  surface: ActiveAgentSurface,
  limit: number,
): Promise<ActiveSummaryResponse> {
  const token =
    typeof window !== "undefined" ? localStorage.getItem("auth_token") : null
  const url = `/api/backend-proxy/agent-monitoring/active-summary?surface=${encodeURIComponent(
    surface,
  )}&limit=${limit}`
  const res = await fetch(url, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  })
  if (!res.ok) {
    throw new Error(`Failed to fetch active agents summary: ${res.status}`)
  }
  return res.json()
}

export function useActiveAgentsSummary(
  opts: UseActiveAgentsSummaryOptions = {},
) {
  const surface = opts.surface ?? "decidir"
  const limit = opts.limit ?? 5
  return useQuery<ActiveSummaryResponse, Error>({
    queryKey: ACTIVE_AGENTS_SUMMARY_QUERY_KEY(surface, limit),
    queryFn: () => fetchActiveSummary(surface, limit),
    refetchInterval: opts.refetchInterval ?? 10_000,
    staleTime: 5_000,
    enabled: opts.enabled ?? true,
  })
}
