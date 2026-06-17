// Onda 2 F1 (2026-05-27) — hook canonical para listar deployments por target.
//
// Consome GET /api/backend-proxy/agent-deployments?target_type&target_id.
// Usado por: pingo cyan no ActiveJobsCard (F4), header da Vaga (F5), header
// aba Agentes do Pool (F6), pingo pulsante no Funil (F7).
//
// staleTime 60s: deployments mudam de minuto-em-minuto na pior hipótese
// (criação manual). Sem polling — refetch só on mount/focus.
//
// N+1 awareness: chamar este hook em N items custa N requests. Use só em
// listas pequenas (e.g., top 10 vagas no Decidir, 6 stages do Funil).
// Para Kanban com 100 candidates, prefira derivar via active-summary cruzado
// com target_id, OU implementar batch endpoint backend.
"use client"

import { useQuery } from "@tanstack/react-query"
import type {
  DeploymentListResponse,
  DeploymentTargetType,
} from "@/types/agents/agent-deployment"

export const TARGET_DEPLOYMENTS_QUERY_KEY = (
  targetType: DeploymentTargetType,
  targetId: string | null,
) => ["agent-deployments", targetType, targetId] as const

async function fetchTargetDeployments(
  targetType: DeploymentTargetType,
  targetId: string,
): Promise<DeploymentListResponse> {
  const token =
    typeof window !== "undefined" ? localStorage.getItem("auth_token") : null
  const url = `/api/backend-proxy/agent-deployments?target_type=${encodeURIComponent(
    targetType,
  )}&target_id=${encodeURIComponent(targetId)}`
  const res = await fetch(url, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  })
  if (!res.ok) {
    throw new Error(`Failed to fetch deployments: ${res.status}`)
  }
  return res.json()
}

interface UseTargetDeploymentsOptions {
  targetType: DeploymentTargetType
  targetId: string | null
  enabled?: boolean
}

export function useTargetDeployments({
  targetType,
  targetId,
  enabled = true,
}: UseTargetDeploymentsOptions) {
  return useQuery<DeploymentListResponse, Error>({
    queryKey: TARGET_DEPLOYMENTS_QUERY_KEY(targetType, targetId),
    queryFn: () => fetchTargetDeployments(targetType, targetId as string),
    enabled: enabled && targetId !== null,
    staleTime: 60_000,
    refetchOnWindowFocus: false,
  })
}
