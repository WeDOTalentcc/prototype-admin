// Onda 4 F2 (2026-05-28) — hook canonical para KPIs de agente individual.
//
// Consome GET /api/backend-proxy/custom-agents/{id}/kpis (Onda 4 B1 backend).
// Usado por: /agent-studio/{id}/kpis page (F3), AgentDetailsPanel KPI link.
//
// React Query canonical (mesma stack do useActiveAgentsSummary Onda 2).
// staleTime 30s — KPIs não mudam tão rápido quanto active-summary; usuário
// trocando de period dispara fetch novo via queryKey.
"use client"

import { useQuery } from "@tanstack/react-query"
import type { AgentKpiPeriod, AgentKpiResponse } from "@/types/agents/kpi"

export const AGENT_KPIS_QUERY_KEY = (agentId: string, period: AgentKpiPeriod) =>
  ["agents", "kpis", agentId, period] as const

interface UseAgentKpisOptions {
  enabled?: boolean
  refetchInterval?: number | false
}

async function fetchAgentKpis(
  agentId: string,
  period: AgentKpiPeriod,
): Promise<AgentKpiResponse> {
  const token =
    typeof window !== "undefined" ? localStorage.getItem("auth_token") : null
  const url = `/api/backend-proxy/custom-agents/${encodeURIComponent(
    agentId,
  )}/kpis?period=${encodeURIComponent(period)}`
  const res = await fetch(url, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  })
  if (!res.ok) {
    throw new Error(`Failed to fetch agent KPIs: ${res.status}`)
  }
  return res.json()
}

export function useAgentKpis(
  agentId: string,
  period: AgentKpiPeriod = "30d",
  opts: UseAgentKpisOptions = {},
) {
  return useQuery<AgentKpiResponse, Error>({
    queryKey: AGENT_KPIS_QUERY_KEY(agentId, period),
    queryFn: () => fetchAgentKpis(agentId, period),
    enabled: (opts.enabled ?? true) && Boolean(agentId),
    staleTime: 30_000,
    refetchInterval: opts.refetchInterval ?? false,
  })
}
