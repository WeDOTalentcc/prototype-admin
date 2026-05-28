// Onda 3 F1 (2026-05-28) — hook canonical para batch read de deployments.
//
// Consome POST /api/backend-proxy/agent-deployments/by-targets.
// Substitui N+1 da Onda 2 (cada item da lista chamava useTargetDeployments
// individual). Agora 1 fetch agregado retorna { [target_id]: Deployment[] }.
//
// staleTime 60s: deployments mudam de minuto-em-minuto na pior hipótese
// (criação manual). Sem polling — refetch só on mount/focus.
//
// Query key estável: targetIds são sorted antes de joinar pra evitar
// cache miss por ordem diferente.
//
// Multi-tenancy: backend filtra por company_id via JWT (fail-closed).
"use client"

import { useQuery } from "@tanstack/react-query"
import type {
  AgentDeployment,
  DeploymentTargetType,
} from "@/types/agents/agent-deployment"

export interface BatchTargetsResponse {
  deployments_by_target: Record<string, AgentDeployment[]>
}

export const DEPLOYMENTS_BY_TARGETS_QUERY_KEY = (
  targetType: DeploymentTargetType,
  targetIds: readonly string[],
) =>
  [
    "agent-deployments",
    "by-targets",
    targetType,
    [...targetIds].sort().join(","),
  ] as const

async function fetchDeploymentsByTargets(
  targetType: DeploymentTargetType,
  targetIds: string[],
): Promise<BatchTargetsResponse> {
  const token =
    typeof window !== "undefined" ? localStorage.getItem("auth_token") : null
  const res = await fetch("/api/backend-proxy/agent-deployments/by-targets", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({
      target_type: targetType,
      target_ids: targetIds,
    }),
  })
  if (!res.ok) {
    throw new Error(`Failed to batch-fetch deployments: ${res.status}`)
  }
  return res.json()
}

interface UseDeploymentsByTargetsOptions {
  targetType: DeploymentTargetType
  targetIds: string[]
  enabled?: boolean
}

export function useDeploymentsByTargets({
  targetType,
  targetIds,
  enabled = true,
}: UseDeploymentsByTargetsOptions) {
  return useQuery<BatchTargetsResponse, Error>({
    queryKey: DEPLOYMENTS_BY_TARGETS_QUERY_KEY(targetType, targetIds),
    queryFn: () => fetchDeploymentsByTargets(targetType, targetIds),
    enabled: enabled && targetIds.length > 0,
    staleTime: 60_000,
    refetchOnWindowFocus: false,
  })
}
