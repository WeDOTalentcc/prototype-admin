"use client"

import { useState, useCallback } from "react"

interface DecisionFactor {
  factor: string
  weight: number | null
  match: string | null
  contribution: string | null
}

interface DecisionExplanation {
  reasoning: string[]
  factors: DecisionFactor[]
  confidence: number | null
  confidence_level: string | null
  fairness_check: string
  criteria_evaluated: string[]
  criteria_ignored: string[]
  calibration_weights_used: Record<string, number>
  transparency_note: string
}

interface DecisionItem {
  decision_id: string
  type: string
  timestamp: string | null
  agent: string
  result: {
    decision: string
    score: number | null
    action: string
  }
  explanation: DecisionExplanation
  human_reviewed: boolean
  human_override: string | null
}

export interface DecisionExplanationResponse {
  candidate_id: string
  job_id: string
  decisions: DecisionItem[]
  total_decisions: number
}

export function useDecisionExplanation() {
  const [data, setData] = useState<DecisionExplanationResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchExplanation = useCallback(
    async (candidateId: string, jobId: string) => {
      setLoading(true)
      setError(null)
      try {
        const res = await fetch(
          `/api/backend-proxy/decisions/candidates/${candidateId}/explain?job_id=${jobId}`
        )
        if (!res.ok) {
          const body = await res.json().catch(() => ({}))
          throw new Error(body.detail || `Erro ${res.status}`)
        }
        const json: DecisionExplanationResponse = await res.json()
        setData(json)
        return json
      } catch (err) {
        const msg = err instanceof Error ? err.message : "Erro ao carregar explicação"
        setError(msg)
        return null
      } finally {
        setLoading(false)
      }
    },
    []
  )

  return { data, loading, error, fetchExplanation }
}

export type { DecisionItem, DecisionExplanation, DecisionFactor }
