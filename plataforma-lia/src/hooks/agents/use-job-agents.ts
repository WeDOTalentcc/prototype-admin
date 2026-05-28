// Onda 3 F3/F4 (2026-05-28) — hooks canonical para CRUD de agentes acoplados
// a uma vaga.
//
//   useJobAgents(jobId)         → GET   /jobs/{job_id}/agents
//   useAttachJobAgent(jobId)    → POST  /jobs/{job_id}/agents
//   useDetachJobAgent(jobId)    → DELETE /jobs/{job_id}/agents/{deployment_id}
//
// React Query v5 padrão. Mutations invalidam queryKey ['job-agents', jobId]
// + ['agent-deployments'] (broader) para refletir mudança em outras surfaces
// (ActiveJobsCard, Pipeline).
"use client"

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import type {
  AttachJobAgentRequest,
  JobAgentListResponse,
  JobAgentDeployment,
} from "@/types/agents/job-agent"

export const JOB_AGENTS_QUERY_KEY = (jobId: string | null) =>
  ["job-agents", jobId] as const

function authHeaders(): Record<string, string> {
  if (typeof window === "undefined") return {}
  const token = localStorage.getItem("auth_token")
  return token ? { Authorization: `Bearer ${token}` } : {}
}

async function fetchJobAgents(jobId: string): Promise<JobAgentListResponse> {
  const res = await fetch(
    `/api/backend-proxy/jobs/${encodeURIComponent(jobId)}/agents`,
    { headers: { ...authHeaders() } },
  )
  if (!res.ok) {
    throw new Error(`Failed to fetch job agents: ${res.status}`)
  }
  return res.json()
}

export function useJobAgents(jobId: string | null) {
  return useQuery<JobAgentListResponse, Error>({
    queryKey: JOB_AGENTS_QUERY_KEY(jobId),
    queryFn: () => fetchJobAgents(jobId as string),
    enabled: !!jobId,
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  })
}

async function postAttachJobAgent(
  jobId: string,
  body: AttachJobAgentRequest,
): Promise<JobAgentDeployment> {
  const res = await fetch(
    `/api/backend-proxy/jobs/${encodeURIComponent(jobId)}/agents`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify(body),
    },
  )
  if (!res.ok) {
    let detail = ""
    try {
      const data = await res.json()
      detail = data?.detail || data?.message || ""
    } catch {
      /* ignore */
    }
    throw new Error(detail || `Failed to attach agent: ${res.status}`)
  }
  return res.json()
}

export function useAttachJobAgent(jobId: string) {
  const qc = useQueryClient()
  return useMutation<JobAgentDeployment, Error, AttachJobAgentRequest>({
    mutationFn: (body) => postAttachJobAgent(jobId, body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: JOB_AGENTS_QUERY_KEY(jobId) })
      // Broadcasta para batch/per-target hooks (ActiveJobsCard, etc.)
      qc.invalidateQueries({ queryKey: ["agent-deployments"] })
    },
  })
}

async function deleteJobAgent(
  jobId: string,
  deploymentId: string,
): Promise<void> {
  const res = await fetch(
    `/api/backend-proxy/jobs/${encodeURIComponent(jobId)}/agents/${encodeURIComponent(
      deploymentId,
    )}`,
    { method: "DELETE", headers: { ...authHeaders() } },
  )
  if (!res.ok && res.status !== 204) {
    throw new Error(`Failed to detach agent: ${res.status}`)
  }
}

export function useDetachJobAgent(jobId: string) {
  const qc = useQueryClient()
  return useMutation<void, Error, string>({
    mutationFn: (deploymentId) => deleteJobAgent(jobId, deploymentId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: JOB_AGENTS_QUERY_KEY(jobId) })
      qc.invalidateQueries({ queryKey: ["agent-deployments"] })
    },
  })
}
