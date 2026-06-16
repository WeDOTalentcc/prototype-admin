"use client"

import useSWR from "swr"
import type { AgentActivityItem } from "@/components/pages-agent-studio/custom-agents/AgentActivityCard"

const fetcher = async (url: string): Promise<AgentActivityItem[]> => {
  const token = typeof window !== "undefined" ? localStorage.getItem("auth_token") : null
  const res = await fetch(url, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  })
  if (!res.ok) throw new Error(`Failed to fetch activities: ${res.status}`)
  const json = await res.json()
  return Array.isArray(json) ? json : []
}

/**
 * useAgentActivities — Wave B2.2 (2026-05-27).
 *
 * Consome GET /api/backend-proxy/agent-monitoring/agents/{id}/activities
 * (ActivityResponse[] do FastAPI). Limit canonical 10 mais recentes.
 */
export function useAgentActivities(agentId: string | null, limit = 10) {
  const url = agentId
    ? `/api/backend-proxy/agent-monitoring/agents/${agentId}/activities?limit=${limit}`
    : null
  const { data, error, isLoading, mutate } = useSWR<AgentActivityItem[]>(url, fetcher, {
    revalidateOnFocus: false,
    dedupingInterval: 10_000,
  })
  return {
    activities: data ?? [],
    isLoading,
    isError: !!error,
    mutate,
  }
}
