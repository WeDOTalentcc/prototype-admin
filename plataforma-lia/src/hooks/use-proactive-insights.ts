import { useState, useEffect, useCallback, useRef } from 'react'

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
  } catch {
    // fail silently
  }
}

export function useProactiveInsights(
  jobId: string | null | undefined,
  companyId: string | null | undefined
): UseProactiveInsightsReturn {
  const [insights, setInsights] = useState<ProactiveInsight[]>([])
  const [loading, setLoading] = useState(false)
  const [dismissed, setDismissed] = useState<Set<string>>(getDismissed)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const fetch = useCallback(async () => {
    if (!companyId) return
    setLoading(true)
    try {
      const params = new URLSearchParams({ company_id: companyId })
      if (jobId) params.set('job_id', jobId)
      const res = await window.fetch(`/api/backend-proxy/proactive-insights?${params.toString()}`)
      if (res.ok) {
        const data: ProactiveInsight[] = await res.json()
        setInsights(data)
      }
    } catch {
      // fail silently — insights are non-critical
    } finally {
      setLoading(false)
    }
  }, [jobId, companyId])

  useEffect(() => {
    fetch()
    intervalRef.current = setInterval(fetch, REFRESH_INTERVAL_MS)
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current)
    }
  }, [fetch])

  const dismiss = useCallback((id: string) => {
    setDismissed(prev => {
      const next = new Set(prev)
      next.add(id)
      saveDismissed(next)
      return next
    })
  }, [])

  const visibleInsights = insights.filter(i => !dismissed.has(i.id))

  return { insights: visibleInsights, loading, dismissed, dismiss, refresh: fetch }
}
