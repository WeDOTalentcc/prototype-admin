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
  /**
   * Percentage used (0-100).  quando não há limite real configurado
   * (limit -1 = enterprise/unlimited OU limit 0/ausente = plano sem cota).
   * Consumers NÃO devem renderizar "100%" pra null — é estado neutro.
   */
  percent: number | null
  /** true when limit === -1 (enterprise tier or override) */
  isUnlimited: boolean
  /**
   * true quando limit é 0/null/undefined: plano sem cota configurada (trial,
   * plano sem limite explícito). NÃO é "100% usado" — é "sem limite definido".
   * Distinto de isUnlimited (que é o opt-in -1 do enterprise).
   */
  noLimit: boolean
  /**
   * semaphore canonical (escala por uso real, 2026-05-30):
   *   - green  : 0-74% usado, OU sem limite (unlimited / noLimit). Estado calmo.
   *   - yellow : 75-94% usado. Atenção (âmbar sutil).
   *   - red    : 95%+ usado. Crítico — único caso de vermelho.
   */
  tier: "green" | "yellow" | "red"
}

export interface UseStudioQuotaResult {
  data: StudioQuotaData | null
  resources: QuotaResourceStatus[]
  isLoading: boolean
  error: Error | null
  refetch: () => Promise<void>
}

/**
 * Pure status resolver (exported pra unit test direto — pattern
 * espelha computeTotalTier do use-agents-total-quota).
 */
export function computeStatus(
  active: number | null | undefined,
  limit: number | null | undefined,
  resource: QuotaResource,
): QuotaResourceStatus {
  // canonical defensive coalescing per backend contract
  // (lia-agent-system/app/api/v1/custom_agents.py:860-895 +
  //  libs/models/lia_models/agent_quota.py:to_dict).
  // Schema garante Integer non-null no DB, mas fallback path
  // (quota row ausente) ou drift de tipo pode entregar null/undefined.
  const safeActive = active ?? 0
  const safeLimit = limit ?? 0

  // Enterprise / override explícito: limit -1 = ilimitado.
  if (safeLimit === -1) {
    return {
      resource,
      active: safeActive,
      limit: safeLimit,
      percent: null,
      isUnlimited: true,
      noLimit: false,
      tier: "green",
    }
  }

  // Sem limite configurado (limit 0/null/undefined): plano trial ou sem cota.
  // BUG histórico (fix 2026-05-30): antes retornava percent=100 + tier=red,
  // mostrando "0/0 100%" em vermelho — falso alarme de "próximo do limite".
  // Correto: estado neutro "sem limite definido", NÃO dispara warning.
  if (safeLimit === 0) {
    return {
      resource,
      active: safeActive,
      limit: safeLimit,
      percent: null,
      isUnlimited: false,
      noLimit: true,
      tier: "green",
    }
  }

  // Limite real configurado: percent 0-100, escala de cor por uso real.
  const percent = Math.min(100, Math.round((safeActive / safeLimit) * 100))
  const tier: QuotaResourceStatus["tier"] =
    percent >= 95 ? "red" : percent >= 75 ? "yellow" : "green"
  return {
    resource,
    active: safeActive,
    limit: safeLimit,
    percent,
    isUnlimited: false,
    noLimit: false,
    tier,
  }
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
