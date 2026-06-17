"use client"

/**
 * Hook canonical para GET /api/v1/custom-agents/studio/quota/agents-total.
 *
 * Sprint 7C / 7B-3b backlog (max_agents_total alias canonical):
 *   - Backend retorna soma das 4 categorias agent (sourcing + custom +
 *     digital_twins + campaigns) como view unified.
 *   - Sidebar consome pra exibir badge "X/Y agentes" (current/total).
 *
 * PRESERVA useStudioQuota (4 categorias per resource) — esse hook é
 * APENAS pra view unified de sidebar/badge global.
 */
import { useEffect, useState, useCallback } from "react"

export interface AgentsTotalQuotaData {
  company_id: string
  max_agents_total: number       // -1 = unlimited
  current_agents_total: number
  percentage_agents_total: number  // 0-100, 0 quando unlimited
  is_unlimited: boolean
}

export type QuotaTotalTier = "green" | "amber" | "coral"

export interface UseAgentsTotalQuotaResult {
  data: AgentsTotalQuotaData | null
  /** semaphore canonical: verde<70%, amber 70-94%, coral≥95% */
  tier: QuotaTotalTier
  isLoading: boolean
  error: Error | null
  refetch: () => Promise<void>
}


function isValidQuotaData(json: unknown): json is AgentsTotalQuotaData {
  if (!json || typeof json !== "object") return false
  const d = json as Record<string, unknown>
  return (
    typeof d.company_id === "string" &&
    typeof d.max_agents_total === "number" &&
    typeof d.current_agents_total === "number" &&
    typeof d.percentage_agents_total === "number" &&
    typeof d.is_unlimited === "boolean"
  )
}

export function computeTotalTier(
  percentage: number,
  isUnlimited: boolean,
): QuotaTotalTier {
  if (isUnlimited) return "green"
  if (percentage >= 95) return "coral"
  if (percentage >= 70) return "amber"
  return "green"
}

export function useAgentsTotalQuota(): UseAgentsTotalQuotaResult {
  const [data, setData] = useState<AgentsTotalQuotaData | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  const refetch = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const res = await fetch(
        "/api/backend-proxy/custom-agents/studio/quota/agents-total",
        { method: "GET", credentials: "include" },
      )
      if (!res.ok) {
        throw new Error(`HTTP ${res.status} fetching agents-total quota`)
      }
      const json = (await res.json()) as unknown
      if (!isValidQuotaData(json)) {
        throw new Error(
          `Invalid quota response shape: ${JSON.stringify(json).slice(0, 200)}`,
        )
      }
      setData(json)
    } catch (e) {
      setError(e instanceof Error ? e : new Error(String(e)))
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    void refetch()
  }, [refetch])

  const tier: QuotaTotalTier = data
    ? computeTotalTier(data.percentage_agents_total, data.is_unlimited)
    : "green"

  return { data, tier, isLoading, error, refetch }
}
