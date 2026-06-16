"use client"

/**
 * useMLPredictions — acesso às previsões ML (P3-4).
 *
 * Cobre três modelos:
 *  - Insights de hiring (por empresa/role)
 *  - Previsão de tempo de preenchimento (time-to-fill)
 *  - Previsão de faixa salarial ótima
 *
 * Proxies:
 *  POST /api/backend-proxy/ml/insights
 *  POST /api/backend-proxy/ml/predict/time-to-fill
 *  POST /api/backend-proxy/ml/predict/salary
 */
import { useState, useCallback } from "react"

export interface HiringInsights {
  summary: {
    total_hires: number
    avg_time_to_fill: number
    top_sources: string[]
    success_rate: number
  }
  recommendations: { action: string; impact: string; priority: string }[]
  top_successful_skills: { skill: string; success_rate: number; count: number }[]
  confidence: number
}

export interface TimeToFillPrediction {
  predicted_days: number
  range_min: number
  range_max: number
  confidence: number
  confidence_level: string
  comparison_to_market: string
  explanation: string
  factors: { name: string; impact: string; value: string }[]
  model_version: string
}

export interface SalaryPrediction {
  suggested_min: number
  suggested_max: number
  market_percentile: number
  competitive_analysis: string
  confidence: number
  confidence_level: string
  explanation: string
  factors: { name: string; impact: string; value: string }[]
}

export interface UseMLPredictionsResult {
  insights: HiringInsights | null
  timeToFill: TimeToFillPrediction | null
  salary: SalaryPrediction | null
  loading: boolean
  error: string | null
  fetchInsights: (companyId: string, role?: string) => Promise<void>
  fetchTimeToFill: (companyId: string, jobData: Record<string, unknown>) => Promise<void>
  fetchSalary: (companyId: string, jobData: Record<string, unknown>) => Promise<void>
}

export function useMLPredictions(): UseMLPredictionsResult {
  const [insights, setInsights] = useState<HiringInsights | null>(null)
  const [timeToFill, setTimeToFill] = useState<TimeToFillPrediction | null>(null)
  const [salary, setSalary] = useState<SalaryPrediction | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchInsights = useCallback(async (companyId: string, role?: string) => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch("/api/backend-proxy/ml/insights", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ company_id: companyId, role }),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      setInsights(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar insights")
    } finally {
      setLoading(false)
    }
  }, [])

  const fetchTimeToFill = useCallback(
    async (companyId: string, jobData: Record<string, unknown>) => {
      setLoading(true)
      setError(null)
      try {
        const res = await fetch("/api/backend-proxy/ml/predict/time-to-fill", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ company_id: companyId, job_data: jobData }),
        })
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        const data = await res.json()
        setTimeToFill(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : "Erro ao prever tempo de preenchimento")
      } finally {
        setLoading(false)
      }
    },
    [],
  )

  const fetchSalary = useCallback(
    async (companyId: string, jobData: Record<string, unknown>) => {
      setLoading(true)
      setError(null)
      try {
        const res = await fetch("/api/backend-proxy/ml/predict/salary", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ company_id: companyId, job_data: jobData }),
        })
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        const data = await res.json()
        setSalary(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : "Erro ao prever faixa salarial")
      } finally {
        setLoading(false)
      }
    },
    [],
  )

  return {
    insights,
    timeToFill,
    salary,
    loading,
    error,
    fetchInsights,
    fetchTimeToFill,
    fetchSalary,
  }
}
