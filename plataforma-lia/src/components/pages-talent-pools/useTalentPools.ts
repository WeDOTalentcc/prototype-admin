import { useState, useEffect, useCallback } from "react"

export interface TalentPoolSummary {
  id: string
  name: string
  status: "active" | "paused" | "archived"
  candidates_count: number
  screened_count: number
  ready_count: number
  ideal_profile_name: string | null
  agent_sourcing_enabled: boolean
  assignments_count?: number
}

export function useTalentPools() {
  const [pools, setPools] = useState<TalentPoolSummary[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadPools = useCallback(async () => {
    try {
      setIsLoading(true)
      setError(null)
      const res = await fetch("/api/backend-proxy/talent-pools")
      if (!res.ok) throw new Error("Failed to load talent pools")
      const data = await res.json()
      const mapped = (data?.data || []).map(
        (d: { id: string; attributes: TalentPoolSummary }) => ({
          ...d.attributes,
          id: d.id,
        })
      )
      setPools(mapped)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar bancos")
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => { loadPools() }, [loadPools])

  const createPool = async (params: {
    name: string
    description?: string
    ideal_profile_id?: string
  }) => {
    const res = await fetch("/api/backend-proxy/talent-pools", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ talent_pool: params }),
    })
    if (!res.ok) throw new Error("Failed to create pool")
    await loadPools()
    return res.json()
  }

  const activePools = pools.filter(p => p.status === "active")

  return { pools, activePools, isLoading, error, loadPools, createPool }
}
