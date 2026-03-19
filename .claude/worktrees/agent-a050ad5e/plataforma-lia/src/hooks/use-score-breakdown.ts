/**
 * E1 — Score clicável: hook para lazy-load do detalhamento de score
 *
 * Não faz fetch até ser explicitamente chamado (lazy). Ideal para Popover
 * que carrega apenas quando o usuário clica no badge de score.
 */
import { useState, useCallback } from 'react'

export interface RequirementEvaluation {
  requirement: string
  priority: string
  level: string
  points: number
  multiplier: number
  weighted_points: number
  evidence: string
  reasoning?: string
  confidence: number
}

export interface ScoreBreakdownData {
  candidate_id: string
  job_vacancy_id: string
  score: number
  evaluated_at: string | null
  model_version: string | null
  strengths: string[]
  concerns: string[]
  reasoning: string
  recommendation: string
  evaluations: RequirementEvaluation[]
  auto_excluded: boolean
}

interface UseScoreBreakdownReturn {
  data: ScoreBreakdownData | null
  loading: boolean
  error: string | null
  fetch: (jobId: string, candidateId: string) => Promise<void>
  reset: () => void
}

export function useScoreBreakdown(): UseScoreBreakdownReturn {
  const [data, setData] = useState<ScoreBreakdownData | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetch = useCallback(async (jobId: string, candidateId: string) => {
    setLoading(true)
    setError(null)
    try {
      const response = await window.fetch(
        `/api/backend-proxy/rubrics/${jobId}/candidates/${candidateId}/breakdown`
      )
      if (response.status === 404) {
        setData(null)
        setError('Avaliação não disponível para este candidato')
        return
      }
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }
      const json = await response.json()
      setData(json)
    } catch (err) {
      setError('Erro ao carregar detalhamento do score')
    } finally {
      setLoading(false)
    }
  }, [])

  const reset = useCallback(() => {
    setData(null)
    setError(null)
    setLoading(false)
  }, [])

  return { data, loading, error, fetch, reset }
}
