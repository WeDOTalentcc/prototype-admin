"use client"

import useSWR from "swr"
import type { Webhook } from "@/components/pages-agent-studio/custom-agents/webhook-types"

const fetcher = async (url: string) => {
  const token = typeof window !== "undefined" ? localStorage.getItem("auth_token") : null
  const res = await fetch(url, { headers: token ? { Authorization: `Bearer ${token}` } : {} })
  if (!res.ok) throw new Error(`Failed: ${res.status}`)
  return res.json()
}

export function useWebhooks() {
  const { data, error, isLoading, mutate } = useSWR<{ webhooks: Webhook[]; total: number }>(
    "/api/backend-proxy/webhooks",
    fetcher,
    { revalidateOnFocus: false, dedupingInterval: 5000 }
  )
  return {
    webhooks: data?.webhooks ?? [],
    total: data?.total ?? 0,
    isLoading,
    isError: !!error,
    mutate,
  }
}
