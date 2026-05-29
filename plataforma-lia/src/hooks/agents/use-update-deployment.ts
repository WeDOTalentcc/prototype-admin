// CF-B B7 (2026-05-29) — hook canonical para PATCH de um agent-deployment.
//
//   useUpdateDeployment() → PATCH /agent-deployments/{deployment_id}
//
// Extraido do inline fetch que vivia em JobAgentsTab (patchDeploymentActive).
// Agora ha 2+ sites de pause/resume; centralizar a mutation evita drift de
// invalidacao de cache e de auth headers.
//
// Invalida ['job-agents', jobId] (quando jobId fornecido) + ['agent-deployments']
// (broader) para refletir mudanca em ActiveJobsCard / Pipeline / Studio.
"use client"

import { useMutation, useQueryClient } from "@tanstack/react-query"
import { JOB_AGENTS_QUERY_KEY } from "@/hooks/agents/use-job-agents"

function authHeaders(): Record<string, string> {
  if (typeof window === "undefined") return {}
  const token = localStorage.getItem("auth_token")
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export interface UpdateDeploymentVars {
  deploymentId: string
  isActive: boolean
}

async function patchDeployment({
  deploymentId,
  isActive,
}: UpdateDeploymentVars): Promise<void> {
  const res = await fetch(
    `/api/backend-proxy/agent-deployments/${encodeURIComponent(deploymentId)}`,
    {
      method: "PATCH",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify({ is_active: isActive }),
    },
  )
  if (!res.ok) {
    throw new Error(`Failed to update deployment: ${res.status}`)
  }
}

/**
 * @param jobId quando fornecido, invalida tambem a lista de agentes daquela vaga.
 */
export function useUpdateDeployment(jobId?: string | null) {
  const qc = useQueryClient()
  return useMutation<void, Error, UpdateDeploymentVars>({
    mutationFn: patchDeployment,
    onSuccess: () => {
      if (jobId) {
        qc.invalidateQueries({ queryKey: JOB_AGENTS_QUERY_KEY(jobId) })
      }
      qc.invalidateQueries({ queryKey: ["agent-deployments"] })
    },
  })
}
