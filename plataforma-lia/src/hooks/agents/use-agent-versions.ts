"use client"

import useSWR from "swr"
import type { AgentVersionSummary } from "@/components/pages-agent-studio/custom-agents/types"

const fetcher = async (url: string) => {
  const token = typeof window !== "undefined" ? localStorage.getItem("auth_token") : null
  const res = await fetch(url, { headers: token ? { Authorization: `Bearer ${token}` } : {} })
  if (!res.ok) throw new Error(`Failed: ${res.status}`)
  return res.json()
}

export function useAgentVersions(agentId: string | null) {
  const { data, error, isLoading, mutate } = useSWR<{
    versions: AgentVersionSummary[]
    total: number
    limit: number
    offset: number
  }>(
    agentId ? `/api/backend-proxy/custom-agents/${agentId}/versions?limit=20` : null,
    fetcher,
    { revalidateOnFocus: false, dedupingInterval: 5000 }
  )
  return {
    versions: data?.versions ?? [],
    total: data?.total ?? 0,
    isLoading,
    isError: !!error,
    mutate,
  }
}
