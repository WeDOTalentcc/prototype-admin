'use client'

import { useState, useEffect, useCallback } from 'react'

export interface ProactiveAlert {
  id: string
  condition: string
  category: string
  title: string
  message: string
  severity: 'info' | 'warning' | 'urgent' | 'success' | 'action_required'
  suggestedAction?: string
  actionLabel?: string
  data?: Record<string, unknown>
  timestamp: Date
  autoDismiss: boolean
  duration: number
}


interface UseProactiveAlertsOptions {
  userId?: string
  companyId?: string
  pollingInterval?: number
  enabled?: boolean
}

interface UseProactiveAlertsReturn {
  alerts: ProactiveAlert[]
  isLoading: boolean
  error: string | null
  dismissAlert: (id: string) => void
  clearAllAlerts: () => void
  triggerCheck: () => Promise<void>
  lastCheck: Date | null
}

export function useProactiveAlerts({
  userId = 'default_user',
  companyId = '',
  pollingInterval = 60000,
  enabled = true
}: UseProactiveAlertsOptions = {}): UseProactiveAlertsReturn {
  const [alerts, setAlerts] = useState<ProactiveAlert[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [lastCheck, setLastCheck] = useState<Date | null>(null)

  const triggerCheck = useCallback(async () => {
    if (!enabled) return
    
    setIsLoading(true)
    setError(null)
    
    try {
      // [Task #801 C4] usar fetchWithRetry para herdar retry/timeout
      const { fetchWithRetry } = await import("@/services/lia-api/base")
      const res = await fetchWithRetry(`/api/backend-proxy/notifications/proactive/check`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, company_id: companyId })
      })
      const response = await res.json()
      
      if (response.success && response.data?.alerts) {
        const newAlerts: ProactiveAlert[] = response.data.alerts.map((alert: Record<string, unknown>, index: number) => ({
          id: `alert_${Date.now()}_${index}`,
          condition: alert.condition,
          category: alert.category || 'system',
          title: alert.title,
          message: alert.message || '',
          severity: mapSeverity(String(alert.severity || '')),
          suggestedAction: alert.suggested_action,
          actionLabel: alert.action_label,
          data: alert.data,
          timestamp: new Date(),
          autoDismiss: String(alert.severity || '') !== 'urgent',
          duration: getSeverityDuration(String(alert.severity || ''))
        }))
        
        if (newAlerts.length > 0) {
          setAlerts(prev => [...newAlerts, ...prev].slice(0, 10))
        }
      }
      
      setLastCheck(new Date())
    } catch (err: unknown) {
      setError(err instanceof Error ? err instanceof Error ? err.message : String(err) : 'Erro ao verificar alertas')
    } finally {
      setIsLoading(false)
    }
  }, [userId, companyId, enabled])

  const dismissAlert = useCallback((id: string) => {
    setAlerts(prev => prev.filter(alert => alert.id !== id))
  }, [])

  const clearAllAlerts = useCallback(() => {
    setAlerts([])
  }, [])

  useEffect(() => {
    if (!enabled) return
    
    triggerCheck()
    
    const interval = setInterval(triggerCheck, pollingInterval)
    
    return () => clearInterval(interval)
  }, [enabled, pollingInterval, triggerCheck])

  return {
    alerts,
    isLoading,
    error,
    dismissAlert,
    clearAllAlerts,
    triggerCheck,
    lastCheck
  }
}

function mapSeverity(severity: string): ProactiveAlert['severity'] {
  const map: Record<string, ProactiveAlert['severity']> = {
    'info': 'info',
    'warning': 'warning',
    'urgent': 'urgent',
    'success': 'success',
    'action_required': 'action_required',
    'critical': 'urgent',
    'high': 'warning',
    'medium': 'info',
    'low': 'info'
  }
  return map[severity?.toLowerCase()] || 'info'
}

function getSeverityDuration(severity: string): number {
  switch (severity?.toLowerCase()) {
    case 'urgent':
    case 'critical':
      return 0
    case 'warning':
    case 'high':
      return 15000
    case 'success':
      return 8000
    default:
      return 10000
  }
}
