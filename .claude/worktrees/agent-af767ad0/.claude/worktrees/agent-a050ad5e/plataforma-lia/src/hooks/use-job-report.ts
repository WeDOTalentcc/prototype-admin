import { useState, useCallback } from 'react'

export interface JobReportFunnelMetrics {
  total_candidates: number
  screening: number
  interview: number
  final: number
  hired: number
  conversion_rate: number
  avg_time_to_hire: number
  cost_per_hire: number
}

export interface JobReportChannelItem {
  channel: string
  candidates: number
  hired: number
}

export interface JobReportTopCandidate {
  name: string
  score: number
  status: string
}

export interface JobReportData {
  vacancy_id: string
  vacancy_title: string
  funnel_metrics: JobReportFunnelMetrics
  channel_performance: JobReportChannelItem[]
  top_candidates: JobReportTopCandidate[]
}

interface UseJobReportReturn {
  data: JobReportData | null
  loading: boolean
  error: string | null
  fetch: (jobId: string) => Promise<void>
}

export function useJobReport(): UseJobReportReturn {
  const [data, setData] = useState<JobReportData | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetch = useCallback(async (jobId: string) => {
    if (!jobId) return
    setLoading(true)
    setError(null)
    try {
      const response = await window.fetch(`/api/backend-proxy/jobs/${jobId}/report`)
      if (!response.ok) throw new Error(`HTTP ${response.status}`)
      const json = await response.json()
      setData(json)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao carregar relatório')
    } finally {
      setLoading(false)
    }
  }, [])

  return { data, loading, error, fetch }
}
