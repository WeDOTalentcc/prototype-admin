"use client"

import { useState, useEffect, useCallback } from "react"

export interface CandidateActivity {
  id: string
  type: string
  title: string
  summary?: string
  author?: string
  author_role?: string
  date?: string
  timestamp?: string
  score?: number
  status?: string
  job_id?: string
  job_title?: string
  platform?: string
  priority?: string
  category?: string
  details?: Record<string, any>
  [key: string]: unknown
}

interface UseCandidateActivitiesResult {
  activities: CandidateActivity[]
  isLoading: boolean
  error: string | null
  total: number
  refetch: () => void
}

/**
 * Fetches real activities for a candidate from the backend.
 * Consumes GET /api/backend-proxy/activities?candidate_id={id}&limit={n}
 *
 * The backend supports filtering by candidate_id per
 * lia-agent-system/app/api/v1/activities.py (list_activities endpoint).
 *
 * Multi-tenancy: enforced on backend via Depends(require_company_id) from JWT.
 * Frontend does NOT pass company_id in the request body or query — only JWT auth header.
 */
export function useCandidateActivities(
  candidate: Record<string, unknown> | null,
  limit = 50,
): UseCandidateActivitiesResult {
  const candidateId = (
    candidate?.id ??
    candidate?.candidateId ??
    candidate?.candidate_id
  ) as string | undefined

  const [activities, setActivities] = useState<CandidateActivity[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [total, setTotal] = useState(0)

  const fetchActivities = useCallback(async () => {
    if (!candidateId) {
      setActivities([])
      setTotal(0)
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      const params = new URLSearchParams({
        candidate_id: candidateId,
        limit: String(limit),
      })
      const response = await fetch(`/api/backend-proxy/activities?${params}`)

      if (!response.ok) {
        const text = await response.text().catch(() => "")
        throw new Error(
          `Activities fetch failed: ${response.status}${text ? ` — ${text.slice(0, 120)}` : ""}`,
        )
      }

      const data = await response.json()
      // Backend returns { activities: [...], total: N }
      const items: CandidateActivity[] = Array.isArray(data?.activities)
        ? data.activities
        : Array.isArray(data)
          ? data
          : []
      setActivities(items)
      setTotal(typeof data?.total === "number" ? data.total : items.length)
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Erro ao carregar atividades"
      setError(msg)
      // Fail loud — do NOT silently show empty/fake data
      setActivities([])
      setTotal(0)
    } finally {
      setIsLoading(false)
    }
  }, [candidateId, limit])

  useEffect(() => {
    void fetchActivities()
  }, [fetchActivities])

  return { activities, isLoading, error, total, refetch: fetchActivities }
}
