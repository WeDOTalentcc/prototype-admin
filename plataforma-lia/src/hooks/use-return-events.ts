import { useState, useEffect, useCallback, useRef, useMemo } from 'react'
import { toast } from "sonner"
interface ReturnEvent {
  id: string
  event_type: string
  vacancy_candidate_id: string
  candidate_name: string
  new_sub_status: string
  new_stage: string | null
  auto_moved: boolean
  notification_type: 'success' | 'warning' | 'info'
  title: string
  description: string
  action_label: string
  action_url: string
  category: string
  timestamp: string
}

interface CandidateAlert {
  candidateId: string
  alertLevel: 'warning' | 'critical'
  message: string
  daysSinceAction: number
}

interface SLAConfig {
  screening: number
  scheduling: number
  evaluation: number
  verification: number
  offer: number
}

const DEFAULT_SLA_DAYS: SLAConfig = {
  screening: 7,
  scheduling: 3,
  evaluation: 5,
  verification: 5,
  offer: 5,
}

const WAITING_SUB_STATUSES = [
  'invite_sent', 'awaiting_response', 'test_sent', 'offer_sent',
  'request_sent', 'awaiting', 'in_progress'
]

interface UseReturnEventsOptions {
  jobId?: string
  companyId?: string
  enabled?: boolean
  pollingIntervalMs?: number
  slaConfig?: Partial<SLAConfig>
}

export function useReturnEvents({
  jobId,
  companyId,
  enabled = true,
  pollingIntervalMs = 30000,
  slaConfig: customSlaConfig
}: UseReturnEventsOptions = {}) {
  const [events, setEvents] = useState<ReturnEvent[]>([])
  const [candidateAlerts, setCandidateAlerts] = useState<Map<string, CandidateAlert>>(new Map())
  const [isPolling, setIsPolling] = useState(false)
  const [useSSE, setUseSSE] = useState(true)
  const lastPollTimestamp = useRef<string>(new Date().toISOString())
  const reconnectAttemptRef = useRef(0)
const slaConfig: SLAConfig = useMemo(() => ({ ...DEFAULT_SLA_DAYS, ...customSlaConfig }), [customSlaConfig])

  const processEvent = useCallback((event: ReturnEvent) => {
    const toastVariant = event.notification_type === 'warning' ? 'destructive' as const : 'default' as const

    toast.success(event.title, { description: event.description })
   
  }, [])

  const computeAlerts = useCallback((candidates: Array<{
    id: string
    name?: string
    subStatus?: string
    actionBehavior?: string
    lastActionDate?: string
    stage?: string
  }>) => {
    const alerts = new Map<string, CandidateAlert>()
    const now = new Date()

    candidates.forEach(candidate => {
      if (!candidate.lastActionDate || !candidate.subStatus) return
      if (!WAITING_SUB_STATUSES.includes(candidate.subStatus)) return

      const actionDate = new Date(candidate.lastActionDate)
      const daysSince = Math.floor((now.getTime() - actionDate.getTime()) / (1000 * 60 * 60 * 24))

      const behavior = candidate.actionBehavior as keyof SLAConfig | undefined
      const slaDays = behavior && slaConfig[behavior] ? slaConfig[behavior] : 5

      if (daysSince >= slaDays) {
        alerts.set(candidate.id, {
          candidateId: candidate.id,
          alertLevel: 'critical',
          message: `Sem resposta há ${daysSince} dias`,
          daysSinceAction: daysSince,
        })
      } else if (daysSince >= Math.floor(slaDays * 0.7)) {
        alerts.set(candidate.id, {
          candidateId: candidate.id,
          alertLevel: 'warning',
          message: `${slaDays - daysSince} dias restantes`,
          daysSinceAction: daysSince,
        })
      }
    })

    setCandidateAlerts(alerts)
    return alerts
  }, [slaConfig])

  const fetchEvents = useCallback(async () => {
    if (!enabled || isPolling) return

    setIsPolling(true)
    try {
      const params = new URLSearchParams({
        since: lastPollTimestamp.current,
      })
      if (jobId) params.append('job_id', jobId)
      if (companyId) params.append('company_id', companyId)

      const response = await fetch(`/api/backend-proxy/recruitment-stages/transition/return-event/recent?${params}`)

      if (response.ok) {
        const data = await response.json()
        const newEvents: ReturnEvent[] = data.events || []

        if (newEvents.length > 0) {
          setEvents(prev => [...newEvents, ...prev].slice(0, 100))
          lastPollTimestamp.current = new Date().toISOString()

          newEvents.forEach(event => processEvent(event))
        }
      }
    } catch (error) {
    } finally {
      setIsPolling(false)
    }
  }, [enabled, isPolling, jobId, companyId, processEvent])

  useEffect(() => {
    if (!enabled) return

    let eventSource: EventSource | null = null
    let fallbackInterval: ReturnType<typeof setInterval> | null = null
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null

    const startPollingFallback = () => {
      if (!fallbackInterval) {
        fallbackInterval = setInterval(fetchEvents, pollingIntervalMs)
      }
    }

    const connectSSE = () => {
      if (!useSSE) {
        startPollingFallback()
        return
      }

      try {
        const params = new URLSearchParams()
        if (jobId) params.append('job_id', jobId)
        if (companyId) params.append('company_id', companyId)

        const url = `/api/backend-proxy/recruitment-stages/transition/return-event/stream?${params}`

        eventSource = new EventSource(url)

        eventSource.onopen = () => {
          reconnectAttemptRef.current = 0
          if (fallbackInterval) {
            clearInterval(fallbackInterval)
            fallbackInterval = null
          }
        }

        eventSource.onmessage = (event) => {
          try {
            const newEvent: ReturnEvent = JSON.parse(event.data)
            setEvents(prev => [newEvent, ...prev].slice(0, 100))
            processEvent(newEvent)
          } catch (error) {
            console.error("[use-return-events] Error:", error)
          }
        }

        eventSource.onerror = () => {
          eventSource?.close()
          eventSource = null
          startPollingFallback()
          const attempt = reconnectAttemptRef.current
          const backoffMs = Math.min(500 * Math.pow(2, attempt), 30000)
          const jitterMs = Math.random() * 1000
          reconnectAttemptRef.current = attempt + 1
          reconnectTimer = setTimeout(connectSSE, backoffMs + jitterMs)
        }
      } catch {
        startPollingFallback()
      }
    }

    connectSSE()

    return () => {
      eventSource?.close()
      if (fallbackInterval) clearInterval(fallbackInterval)
      if (reconnectTimer) clearTimeout(reconnectTimer)
    }
  }, [enabled, jobId, companyId, useSSE, pollingIntervalMs, fetchEvents, processEvent])

  const getAlertForCandidate = useCallback((candidateId: string): CandidateAlert | undefined => {
    return candidateAlerts.get(candidateId)
  }, [candidateAlerts])

  const hasAlerts = candidateAlerts.size > 0

  return {
    events,
    candidateAlerts,
    getAlertForCandidate,
    hasAlerts,
    isPolling,
    fetchEvents,
    computeAlerts,
  }
}
