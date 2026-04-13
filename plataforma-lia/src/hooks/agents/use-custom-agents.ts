"use client"

import useSWR from "swr"
import type { CustomAgent } from "@/components/pages-agent-studio/custom-agents/types"

const fetcher = async (url: string) => {
  const token = typeof window !== "undefined" ? localStorage.getItem("auth_token") : null
  const res = await fetch(url, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  })
  if (!res.ok) throw new Error(`Failed to fetch: ${res.status}`)
  return res.json()
}

export function useCustomAgents() {
  const { data, error, isLoading, mutate } = useSWR<{ agents: CustomAgent[]; total: number }>(
    "/api/backend-proxy/custom-agents",
    fetcher,
    { revalidateOnFocus: false, dedupingInterval: 5000 }
  )
  return {
    agents: data?.agents ?? [],
    total: data?.total ?? 0,
    isLoading,
    isError: !!error,
    mutate,
  }
}

export function useAgentDeployments(agentId: string | null) {
  const { data, error, isLoading, mutate } = useSWR(
    agentId ? `/api/backend-proxy/custom-agents/${agentId}/deployments` : null,
    fetcher,
    { revalidateOnFocus: false }
  )
  return {
    deployments: data?.deployments ?? [],
    total: data?.total ?? 0,
    isLoading,
    isError: !!error,
    mutate,
  }
}
