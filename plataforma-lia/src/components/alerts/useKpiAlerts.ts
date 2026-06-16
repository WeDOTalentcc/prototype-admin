"use client"

import { useState, useEffect, useMemo, useCallback } from "react"
import { toast } from "sonner"
import type { KPIAlert, AlertRule, BackendAlert, AlertPreference } from "./kpi-alert-utils"
import {
  convertPreferencesToRules,
  getSuggestedActions,
  getCategoryFromMetric,
  getMetricDisplayName,
  getPriorityFromSeverity,
  getAffectedJobs,
  getEstimatedImpact,
  defaultAlertRules,
} from "./kpi-alert-utils"

export type { KPIAlert, AlertRule } from "./kpi-alert-utils"

export function useKpiAlerts(
  recruiterData: Record<string, unknown>[],
  onAlertAction: (alertId: string, action: string) => void
) {
  const [alerts, setAlerts] = useState<KPIAlert[]>([])
  const [_backendAlerts, setBackendAlerts] = useState<BackendAlert[]>([])
  const [_alertPreferences, setAlertPreferences] = useState<AlertPreference[]>([])
  const [alertRules, setAlertRules] = useState<AlertRule[]>([])
  const [filterType, setFilterType] = useState<string>('all')
  const [filterCategory, setFilterCategory] = useState<string>('all')
  const [sortBy, setSortBy] = useState<'date' | 'priority' | 'severity'>('date')
  const [showArchived, setShowArchived] = useState(false)
  const [selectedAlert, setSelectedAlert] = useState<KPIAlert | null>(null)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [showSettingsModal, setShowSettingsModal] = useState(false)

  const fetchAlertsFromBackend = useCallback(async () => {
    try {
      const response = await fetch('/api/backend-proxy/alerts?limit=50')
      if (response.ok) {
        const data = await response.json()
        setBackendAlerts(data)
      }
    } catch (error) {
    }
  }, [])

  const fetchPreferences = useCallback(async () => {
    try {
      const response = await fetch('/api/backend-proxy/alerts/preferences?user_id=default')
      if (response.ok) {
        const data = await response.json()
        setAlertPreferences(data.preferences || [])
        const rules = convertPreferencesToRules(data.preferences || [])
        setAlertRules(rules)
      }
    } catch (error) {
      setAlertRules(defaultAlertRules)
    }
  }, [])

  useEffect(() => {
    const loadData = async () => {
      setIsLoading(true)
      await Promise.all([fetchAlertsFromBackend(), fetchPreferences()])
      setIsLoading(false)
    }
    loadData()
  }, [fetchAlertsFromBackend, fetchPreferences])

  const generateAlerts = useMemo(() => {
    const newAlerts: KPIAlert[] = []

    recruiterData.forEach(recruiter => {
      alertRules.forEach(rule => {
        if (!rule.enabled) return
        const metricValue = recruiter[rule.metric as keyof typeof recruiter]
        if (typeof metricValue !== 'number') return

        let shouldAlert = false
        switch (rule.operator) {
          case '>': shouldAlert = metricValue > rule.threshold; break
          case '<': shouldAlert = metricValue < rule.threshold; break
          case '>=': shouldAlert = metricValue >= rule.threshold; break
          case '<=': shouldAlert = metricValue <= rule.threshold; break
          case '=': shouldAlert = metricValue === rule.threshold; break
        }

        if (shouldAlert) {
          const variance = ((metricValue - rule.threshold) / rule.threshold) * 100
          const suggestedActions = getSuggestedActions(rule.metric, metricValue, rule.threshold)

          newAlerts.push({
            id: `alert-${recruiter.name}-${rule.id}-${Date.now()}`,
            type: rule.severity === 'critical' ? 'critical' : rule.severity === 'warning' ? 'warning' : 'info',
            category: getCategoryFromMetric(rule.metric),
            title: `${rule.name} - ${recruiter.name}`,
            description: `${getMetricDisplayName(rule.metric)} está ${rule.operator === '<' ? 'abaixo' : 'acima'} do limite (${metricValue} vs ${rule.threshold})`,
            recruiterName: String(recruiter.name),
            recruiterId: String(recruiter.name).toLowerCase().replace(' ', '_'),
            department: String(recruiter.department),
            metric: rule.metric,
            currentValue: metricValue,
            targetValue: rule.threshold,
            threshold: rule.threshold,
            variance: Math.abs(variance),
            trend: variance > 0 ? 'up' : 'down',
            createdAt: new Date(),
            isRead: false,
            isArchived: false,
            priority: getPriorityFromSeverity(rule.severity, Math.abs(variance)),
            suggestedActions,
            affectedJobs: getAffectedJobs(recruiter),
            estimatedImpact: getEstimatedImpact(rule.metric, Math.abs(variance))
          })
        }
      })
    })
    return newAlerts
  }, [recruiterData, alertRules])

  useEffect(() => {
    if (alertRules.length === 0) {
      setAlertRules(defaultAlertRules)
    }
  }, [alertRules.length])

  useEffect(() => {
    setAlerts(prevAlerts => {
      const existingAlerts = prevAlerts.filter(alert => !alert.isArchived)
      const newAlertsFiltered = generateAlerts.filter(newAlert =>
        !existingAlerts.some(existing =>
          existing.recruiterId === newAlert.recruiterId &&
          existing.metric === newAlert.metric
        )
      )
      return [...existingAlerts, ...newAlertsFiltered]
    })
  }, [generateAlerts])

  const filteredAlerts = useMemo(() => {
    const filtered = alerts.filter(alert => {
      if (!showArchived && alert.isArchived) return false
      if (filterType !== 'all' && alert.type !== filterType) return false
      if (filterCategory !== 'all' && alert.category !== filterCategory) return false
      return true
    })

    return [...filtered].sort((a, b) => {
      switch (sortBy) {
        case 'priority':
          const priorityOrder = { urgent: 4, high: 3, medium: 2, low: 1 }
          return priorityOrder[b.priority] - priorityOrder[a.priority]
        case 'severity':
          const severityOrder = { critical: 3, warning: 2, info: 1, success: 0 }
          return severityOrder[b.type] - severityOrder[a.type]
        case 'date':
        default:
          return b.createdAt.getTime() - a.createdAt.getTime()
      }
    })
  }, [alerts, showArchived, filterType, filterCategory, sortBy])

  const handleMarkAsRead = (alertId: string) => {
    setAlerts(prev => prev.map(alert =>
      alert.id === alertId ? { ...alert, isRead: true } : alert
    ))
    onAlertAction(alertId, 'mark_read')
  }

  const handleArchiveAlert = (alertId: string) => {
    setAlerts(prev => prev.map(alert =>
      alert.id === alertId ? { ...alert, isArchived: true } : alert
    ))
    onAlertAction(alertId, 'archive')
  }

  const handleSendNotification = (alertId: string) => {
    onAlertAction(alertId, 'send_notification')
  }

  const handleRefreshAlerts = async () => {
    setIsRefreshing(true)
    try {
      await Promise.all([fetchAlertsFromBackend(), fetchPreferences()])
      toast.success('Alertas atualizados com sucesso')
    } catch (error) {
      toast.error('Erro ao atualizar alertas', { description: "Verifique sua conexão e tente novamente." })
    } finally {
      setIsRefreshing(false)
    }
  }

  const handleUpdateRules = async (newRules: AlertRule[]) => {
    setAlertRules(newRules)
    setShowSettingsModal(false)
    await fetchPreferences()
    toast.success('Configurações salvas com sucesso')
  }

  const alertStats = useMemo(() => {
    const unreadAlerts = alerts.filter(alert => !alert.isRead && !alert.isArchived)
    const criticalAlerts = unreadAlerts.filter(alert => alert.type === 'critical')
    const warningAlerts = unreadAlerts.filter(alert => alert.type === 'warning')

    return {
      total: unreadAlerts.length,
      critical: criticalAlerts.length,
      warning: warningAlerts.length,
      byCategory: {
        performance: unreadAlerts.filter(a => a.category === 'performance').length,
        deadline: unreadAlerts.filter(a => a.category === 'deadline').length,
        target: unreadAlerts.filter(a => a.category === 'target').length,
        budget: unreadAlerts.filter(a => a.category === 'budget').length,
        quality: unreadAlerts.filter(a => a.category === 'quality').length
      }
    }
  }, [alerts])

  return {
    alerts,
    alertRules,
    filteredAlerts,
    alertStats,
    filterType,
    setFilterType,
    filterCategory,
    setFilterCategory,
    sortBy,
    setSortBy,
    showArchived,
    setShowArchived,
    selectedAlert,
    setSelectedAlert,
    isRefreshing,
    isLoading,
    showSettingsModal,
    setShowSettingsModal,
    handleMarkAsRead,
    handleArchiveAlert,
    handleSendNotification,
    handleRefreshAlerts,
    handleUpdateRules,
  }
}
