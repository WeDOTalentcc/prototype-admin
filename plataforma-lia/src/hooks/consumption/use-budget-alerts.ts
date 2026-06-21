// Onda 4 F2 (2026-05-28) — hook canonical para alertas de orçamento.
//
// Consome GET /api/backend-proxy/ai-consumption/budget-alerts (Onda 4 B3).
// Usado por: BudgetAlertsList (F5) no hub Consumo > Créditos IA.
//
// Polling 60s — alerts evoluem com consumo agregado; não precisa ser tão
// agressivo quanto active-summary (10s).
"use client"

import { useQuery } from "@tanstack/react-query"
import type { BudgetAlertsResponse } from "@/types/consumption/budget-alerts"

export const BUDGET_ALERTS_QUERY_KEY = ["consumption", "budget-alerts"] as const

interface UseBudgetAlertsOptions {
  enabled?: boolean
  refetchInterval?: number | false
}

async function fetchBudgetAlerts(): Promise<BudgetAlertsResponse> {
  const token =
    typeof window !== "undefined" ? localStorage.getItem("auth_token") : null
  const res = await fetch("/api/backend-proxy/ai-consumption/budget-alerts", {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  })
  if (res.status === 404) {
    return { alerts: [] } as BudgetAlertsResponse
  }
  if (!res.ok) {
    throw new Error(`Failed to fetch budget alerts: ${res.status}`)
  }
  return res.json()
}

export function useBudgetAlerts(opts: UseBudgetAlertsOptions = {}) {
  return useQuery<BudgetAlertsResponse, Error>({
    queryKey: BUDGET_ALERTS_QUERY_KEY,
    queryFn: fetchBudgetAlerts,
    enabled: opts.enabled ?? true,
    staleTime: 60_000,
    refetchInterval: opts.refetchInterval ?? 60_000,
  })
}
