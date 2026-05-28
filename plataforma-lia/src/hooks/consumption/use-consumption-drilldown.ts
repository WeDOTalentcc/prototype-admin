// Onda 4 F2 (2026-05-28) — hook canonical para drilldown de execuções de consumo.
//
// Consome GET /api/backend-proxy/ai-consumption/by-agent/drilldown (Onda 4 B2).
// Usado por: ConsumptionDrilldownModal (F4) ao clicar segmento do BarChart.
"use client"

import { useQuery } from "@tanstack/react-query"
import type {
  ConsumptionDrilldownParams,
  ConsumptionDrilldownResponse,
} from "@/types/consumption/drilldown"

export const CONSUMPTION_DRILLDOWN_QUERY_KEY = (
  params: ConsumptionDrilldownParams,
) =>
  [
    "consumption",
    "drilldown",
    params.agent_type ?? null,
    params.studio_agent_id ?? null,
    params.since_days ?? 30,
    params.limit ?? 100,
    params.offset ?? 0,
  ] as const

interface UseConsumptionDrilldownOptions {
  enabled?: boolean
}

async function fetchDrilldown(
  params: ConsumptionDrilldownParams,
): Promise<ConsumptionDrilldownResponse> {
  const token =
    typeof window !== "undefined" ? localStorage.getItem("auth_token") : null
  const qs = new URLSearchParams()
  if (params.agent_type) qs.set("agent_type", params.agent_type)
  if (params.studio_agent_id) qs.set("studio_agent_id", params.studio_agent_id)
  qs.set("since_days", String(params.since_days ?? 30))
  qs.set("limit", String(params.limit ?? 100))
  qs.set("offset", String(params.offset ?? 0))
  const url = `/api/backend-proxy/ai-consumption/by-agent/drilldown?${qs.toString()}`
  const res = await fetch(url, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  })
  if (!res.ok) {
    throw new Error(`Failed to fetch consumption drilldown: ${res.status}`)
  }
  return res.json()
}

export function useConsumptionDrilldown(
  params: ConsumptionDrilldownParams,
  opts: UseConsumptionDrilldownOptions = {},
) {
  return useQuery<ConsumptionDrilldownResponse, Error>({
    queryKey: CONSUMPTION_DRILLDOWN_QUERY_KEY(params),
    queryFn: () => fetchDrilldown(params),
    enabled:
      (opts.enabled ?? true) &&
      Boolean(params.agent_type || params.studio_agent_id),
    staleTime: 60_000,
  })
}
