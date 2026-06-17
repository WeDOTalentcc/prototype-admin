import { useState, useCallback } from 'react'
import useSWR from 'swr'

export interface ProactiveInsight {
  id: string
  title: string
  message: string
  urgency: 'low' | 'normal' | 'high' | 'urgent'
  type: string
  action_url?: string | null
  created_at: string
}

interface UseProactiveInsightsReturn {
  insights: ProactiveInsight[]
  loading: boolean
  dismissed: Set<string>
  dismiss: (id: string) => void
  refresh: () => void
}

const REFRESH_INTERVAL_MS = 5 * 60 * 1000 // 5 minutos
const STORAGE_KEY = 'proactive_dismissed_insights'

function getDismissed(): Set<string> {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY)
    return raw ? new Set(JSON.parse(raw)) : new Set()
  } catch {
    return new Set()
  }
}

function saveDismissed(ids: Set<string>) {
  try {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify([...ids]))
  } catch (error) {
    console.error("[use-proactive-insights] Error:", error)
    // fail silently
  }
}

const jsonFetcher = (url: string) =>
  fetch(url).then(r => {
    if (!r.ok) throw new Error(`HTTP ${r.status}`)
    return r.json()
  })

export function useProactiveInsights(
  jobId: string | null | undefined,
  companyId: string | null | undefined
): UseProactiveInsightsReturn {
  const [dismissed, setDismissed] = useState<Set<string>>(getDismissed)

  const key = companyId
    ? `/api/backend-proxy/proactive-insights?company_id=${companyId}${jobId ? `&job_id=${jobId}` : ''}`
    : null

  const { data, isLoading, mutate } = useSWR<ProactiveInsight[]>(key, jsonFetcher, {
    refreshInterval: REFRESH_INTERVAL_MS,
  })

  const dismiss = useCallback((id: string) => {
    setDismissed(prev => {
      const next = new Set(prev)
      next.add(id)
      saveDismissed(next)
      return next
    })
  }, [])

  const rawData = Array.isArray(data) ? data : []
  const insights = rawData.filter(i => !dismissed.has(i.id))

  return {
    insights,
    loading: isLoading,
    dismissed,
    dismiss,
    refresh: () => mutate(),
  }
}
