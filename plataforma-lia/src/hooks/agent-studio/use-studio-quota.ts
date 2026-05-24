"use client"

/**
 * Hook canonical para consumir GET /api/v1/custom-agents/studio/quota.
 *
 * Pattern feedforward (audit harness 2026-05-23 + pesquisa concorrencial):
 *   - Backend já expunha este endpoint mas frontend nunca consumia.
 *   - Sem o hook, recrutador só descobre limit quando bate parede (feedback puro).
 *   - Com o hook + QuotaMeter, recrutador vê "8/10" e sabe quando aproximar do AM.
 *
 * Shape do response (lia-agent-system/app/api/v1/custom_agents.py:832):
 *   {
 *     company_id: string,
 *     plan_code: "starter" | "pro" | "business" | "enterprise",
 *     max_custom_agents: number,       // -1 = unlimited
 *     max_sourcing_agents: number,
 *     max_digital_twins: number,
 *     max_campaigns: number,
 *     active_custom_agents: number,
 *     active_sourcing_agents: number,
 *     active_digital_twins: number,
 *     active_campaigns: number,
 *   }
 */
import { useEffect, useState, useCallback } from "react"

export interface StudioQuotaData {
  company_id: string
  plan_code: string
  max_custom_agents: number
  max_sourcing_agents: number
  max_digital_twins: number
  max_campaigns: number
  active_custom_agents: number
  active_sourcing_agents: number
  active_digital_twins: number
  active_campaigns: number
}

export type QuotaResource =
  | "custom_agents"
  | "sourcing_agents"
  | "digital_twins"
  | "campaigns"

export interface QuotaResourceStatus {
  resource: QuotaResource
  active: number
  limit: number
  /** percentage used (0-100). For unlimited (-1) returns 0. */
  percent: number
  /** true when limit === -1 (enterprise tier or override) */
  isUnlimited: boolean
  /** semaphore: green <80%, yellow 80-99%, red >=100% */
  tier: "green" | "yellow" | "red"
}

export interface UseStudioQuotaResult {
  data: StudioQuotaData | null
  resources: QuotaResourceStatus[]
  isLoading: boolean
  error: Error | null
  refetch: () => Promise<void>
}

function computeStatus(active: number, limit: number, resource: QuotaResource): QuotaResourceStatus {
  if (limit === -1) {
    return { resource, active, limit, percent: 0, isUnlimited: true, tier: "green" }
  }
  const percent = limit === 0 ? 100 : Math.min(100, Math.round((active / limit) * 100))
  const tier: QuotaResourceStatus["tier"] =
    percent >= 100 ? "red" : percent >= 80 ? "yellow" : "green"
  return { resource, active, limit, percent, isUnlimited: false, tier }
}

export function useStudioQuota(): UseStudioQuotaResult {
  const [data, setData] = useState<StudioQuotaData | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  const refetch = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const res = await fetch("/api/backend-proxy/custom-agents/studio/quota", {
        method: "GET",
        credentials: "include",
      })
      if (!res.ok) {
        throw new Error(`HTTP ${res.status} fetching studio quota`)
      }
      const json = (await res.json()) as StudioQuotaData
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

  const resources: QuotaResourceStatus[] = data
    ? [
        computeStatus(data.active_custom_agents, data.max_custom_agents, "custom_agents"),
        computeStatus(data.active_sourcing_agents, data.max_sourcing_agents, "sourcing_agents"),
        computeStatus(data.active_digital_twins, data.max_digital_twins, "digital_twins"),
        computeStatus(data.active_campaigns, data.max_campaigns, "campaigns"),
      ]
    : []

  return { data, resources, isLoading, error, refetch }
}
