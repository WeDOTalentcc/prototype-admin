"use client"

import { useState, useCallback } from "react"
import type { JdSimilarItem } from "@/components/unified-chat/wizard/panels/JdSimilarCard"

interface LookupResponse {
  items: Array<{
    id: string
    title: string
    department?: string | null
    seniority_level?: string | null
    was_filled: boolean
    time_to_fill_days?: number | null
    candidates_count: number
    similarity?: number | null
  }>
  total_company_jds: number
  threshold_met: boolean
}

interface UseJdSimilarParams {
  companyId: string
  toggleEnabled?: boolean
  minSimilarity?: number
  limit?: number
}

interface UseJdSimilarResult {
  items: JdSimilarItem[]
  loading: boolean
  totalCompanyJds: number
  thresholdMet: boolean
  lookup: (title: string, department?: string) => Promise<void>
  clear: () => void
}

/**
 * Sprint B Phase 1 — Hook para buscar JDs similares no historico.
 *
 * Fail-graceful: erros nao crasham UI, retornam items vazios.
 * Auto-debounce: caller controla quando chamar (recomendado debouncar input).
 */
export function useJdSimilar({
  companyId,
  toggleEnabled = true,
  minSimilarity = 0.7,
  limit = 3,
}: UseJdSimilarParams): UseJdSimilarResult {
  const [items, setItems] = useState<JdSimilarItem[]>([])
  const [loading, setLoading] = useState(false)
  const [totalCompanyJds, setTotal] = useState(0)
  const [thresholdMet, setThresholdMet] = useState(false)

  const clear = useCallback(() => {
    setItems([])
    setTotal(0)
    setThresholdMet(false)
  }, [])

  const lookup = useCallback(
    async (title: string, department?: string) => {
      if (!companyId || !title || !title.trim()) {
        clear()
        return
      }
      setLoading(true)
      try {
        const params = new URLSearchParams({
          company_id: companyId,
          title: title.trim(),
          toggle_enabled: String(toggleEnabled),
          min_similarity: String(minSimilarity),
          limit: String(limit),
        })
        if (department) params.set("department", department)

        const res = await fetch(`/api/backend-proxy/jd-similar/lookup?${params.toString()}`, {
          method: "GET",
          headers: { "Content-Type": "application/json" },
        })
        const data: LookupResponse = await res.json()

        // Normalize snake_case -> camelCase para o componente
        const mapped: JdSimilarItem[] = (data.items || []).map((it) => ({
          id: it.id,
          title: it.title,
          department: it.department,
          seniorityLevel: it.seniority_level,
          wasFilled: it.was_filled,
          timeToFillDays: it.time_to_fill_days,
          candidatesCount: it.candidates_count,
          similarity: it.similarity,
        }))

        setItems(mapped)
        setTotal(data.total_company_jds || 0)
        setThresholdMet(Boolean(data.threshold_met))
      } catch {
        // Fail-graceful
        clear()
      } finally {
        setLoading(false)
      }
    },
    [companyId, toggleEnabled, minSimilarity, limit, clear],
  )

  return { items, loading, totalCompanyJds, thresholdMet, lookup, clear }
}
