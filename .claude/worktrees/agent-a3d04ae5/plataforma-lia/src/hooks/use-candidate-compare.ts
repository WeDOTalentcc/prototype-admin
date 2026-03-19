/**
 * D9 — Análise Comparativa Visual
 *
 * Hook para comparar 2-4 candidatos lado a lado.
 * Lazy: não faz fetch até `compare()` ser chamado.
 */
import { useState, useCallback } from 'react'

export interface DimensionScore {
  [candidateId: string]: number | null
}

export interface CandidateCompareResult {
  comparison_id: string
  winner: string | null
  winner_name: string | null
  confidence: number
  scenario: string
  scenario_description: string
  candidate_scores: Record<string, number>
  dimension_comparison: Record<string, DimensionScore>
  analysis: string
  generated_at: string
}

interface UseCandidateCompareReturn {
  data: CandidateCompareResult | null
  loading: boolean
  error: string | null
  compare: (
    candidateIds: string[],
    jobId?: string,
    companyId?: string
  ) => Promise<void>
  reset: () => void
}

export function useCandidateCompare(): UseCandidateCompareReturn {
  const [data, setData] = useState<CandidateCompareResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const compare = useCallback(
    async (candidateIds: string[], jobId?: string, companyId?: string) => {
      if (candidateIds.length < 2) {
        setError('Selecione pelo menos 2 candidatos para comparar')
        return
      }
      setLoading(true)
      setError(null)
      try {
        const headers: Record<string, string> = {
          'Content-Type': 'application/json',
        }
        if (companyId) headers['X-Company-ID'] = companyId

        const response = await window.fetch('/api/backend-proxy/candidates/compare', {
          method: 'POST',
          headers,
          body: JSON.stringify({
            candidate_ids: candidateIds,
            job_id: jobId || null,
          }),
        })
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`)
        }
        const json = await response.json()
        setData(json)
      } catch {
        setError('Erro ao comparar candidatos')
      } finally {
        setLoading(false)
      }
    },
    []
  )

  const reset = useCallback(() => {
    setData(null)
    setError(null)
    setLoading(false)
  }, [])

  return { data, loading, error, compare, reset }
}
