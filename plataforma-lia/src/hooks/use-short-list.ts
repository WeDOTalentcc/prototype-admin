"use client"

/**
 * useShortList — gerenciamento de short lists de candidatos por vaga.
 *
 * Sprint F4 — Short List Feature.
 * Proxy: /api/backend-proxy/short-lists
 *
 * Portabilidade Vue: useShortList() → composable com reactive/ref.
 */
import { useState, useCallback, useEffect } from "react"

// ── Types ──────────────────────────────────────────────────────────────────

export interface ShortList {
  id: string
  jobId: string
  name: string
  description?: string
  createdBy: string
  createdAt: string
  candidateCount: number
}

export interface ShortListEntry {
  id: string
  candidateId: string
  addedAt: string
  notes?: string
}

export interface UseShortListReturn {
  shortLists: ShortList[]
  isLoading: boolean
  error: string | null
  createShortList: (jobId: string, name: string, description?: string) => Promise<ShortList | null>
  addCandidate: (listId: string, candidateId: string, notes?: string) => Promise<boolean>
  removeCandidate: (listId: string, candidateId: string) => Promise<boolean>
  refresh: () => void
}

// ── API helpers ────────────────────────────────────────────────────────────

async function apiFetch(url: string, options?: RequestInit) {
  const res = await fetch(url, options)
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.error || `HTTP ${res.status}`)
  }
  if (res.status === 204) return null
  return res.json()
}

function toShortList(raw: Record<string, unknown>): ShortList {
  return {
    id: raw.id,
    jobId: raw.job_id,
    name: raw.name,
    description: raw.description ?? undefined,
    createdBy: raw.created_by,
    createdAt: raw.created_at,
    candidateCount: raw.candidate_count ?? 0,
  }
}

// ── Hook ──────────────────────────────────────────────────────────────────

export function useShortList(companyId: string, jobId?: string): UseShortListReturn {
  const [shortLists, setShortLists] = useState<ShortList[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [refreshFlag, setRefreshFlag] = useState(0)

  const fetchShortLists = useCallback(async () => {
    if (!companyId) return
    setIsLoading(true)
    setError(null)
    try {
      const params = new URLSearchParams({ company_id: companyId })
      if (jobId) params.set("job_id", jobId)
      const data = await apiFetch(`/api/backend-proxy/short-lists?${params}`)
      setShortLists((data as Record<string, unknown>[]).map(toShortList))
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setIsLoading(false)
    }
  }, [companyId, jobId])

  useEffect(() => {
    fetchShortLists()
  }, [fetchShortLists, refreshFlag])

  const createShortList = useCallback(
    async (jId: string, name: string, description?: string): Promise<ShortList | null> => {
      try {
        const data = await apiFetch(
          `/api/backend-proxy/short-lists?company_id=${companyId}`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ job_id: jId, name, description }),
          }
        )
        const list = toShortList(data)
        setShortLists(prev => [list, ...prev])
        return list
      } catch (err) {
        setError((err as Error).message)
        return null
      }
    },
    [companyId]
  )

  const addCandidate = useCallback(
    async (listId: string, candidateId: string, notes?: string): Promise<boolean> => {
      try {
        await apiFetch(
          `/api/backend-proxy/short-lists/${listId}/candidates?company_id=${companyId}`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ candidate_id: candidateId, notes }),
          }
        )
        setRefreshFlag(f => f + 1)
        return true
      } catch (err) {
        setError((err as Error).message)
        return false
      }
    },
    [companyId]
  )

  const removeCandidate = useCallback(
    async (listId: string, candidateId: string): Promise<boolean> => {
      try {
        await apiFetch(
          `/api/backend-proxy/short-lists/${listId}/candidates/${candidateId}?company_id=${companyId}`,
          { method: "DELETE" }
        )
        setRefreshFlag(f => f + 1)
        return true
      } catch (err) {
        setError((err as Error).message)
        return false
      }
    },
    [companyId]
  )

  const refresh = useCallback(() => setRefreshFlag(f => f + 1), [])

  return {
    shortLists,
    isLoading,
    error,
    createShortList,
    addCandidate,
    removeCandidate,
    refresh,
  }
}
