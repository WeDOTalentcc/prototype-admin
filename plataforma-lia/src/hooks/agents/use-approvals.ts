"use client"

import useSWR from "swr"
import type { AgentApproval } from "@/components/pages-agent-studio/custom-agents/types"

const fetcher = async (url: string) => {
  const token = typeof window !== "undefined" ? localStorage.getItem("auth_token") : null
  const res = await fetch(url, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  })
  if (!res.ok) throw new Error(`Failed: ${res.status}`)
  return res.json()
}

export function usePendingApprovals() {
  const { data, error, isLoading, mutate } = useSWR<{ approvals: AgentApproval[]; total: number }>(
    "/api/backend-proxy/agent-approvals/pending",
    fetcher,
    { revalidateOnFocus: true, dedupingInterval: 10000 }
  )
  return {
    approvals: data?.approvals ?? [],
    total: data?.total ?? 0,
    isLoading,
    isError: !!error,
    mutate,
  }
}
