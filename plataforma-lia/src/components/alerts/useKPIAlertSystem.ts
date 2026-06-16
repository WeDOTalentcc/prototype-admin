"use client"

import { useState, useEffect, useMemo, useCallback } from "react"
import { toast } from "sonner"

export interface KPIAlert {
  id: string
  type: 'critical' | 'warning' | 'info' | 'success'
  category: 'performance' | 'deadline' | 'target' | 'budget' | 'quality'
  title: string
  description: string
  recruiterName: string
  recruiterId: string
  department: string
  metric: string
  currentValue: number
  targetValue: number
  threshold: number
  variance: number
  trend: 'up' | 'down' | 'stable'
  createdAt: Date
  isRead: boolean
  isArchived: boolean
  priority: 'low' | 'medium' | 'high' | 'urgent'
  suggestedActions: string[]
  affectedJobs?: string[]
  estimatedImpact: 'low' | 'medium' | 'high'
}

interface BackendAlert {
  id: string
  alert_type: string
  severity: string
  status: string
  title: string
  message: string
  user_id?: string
  job_id?: string
  candidate_id?: string
  context?: Record<string, unknown>
  suggested_actions?: string[]
  created_at: string
}

interface AlertPreference {
  id?: string
  user_id: string
  alert_type: string
  name?: string
  description?: string
  is_enabled: boolean
  threshold?: number
  channels: {
    email: boolean
    bell: boolean
    teams: boolean
    whatsapp: boolean
  }
  cooldown_hours: number
}

export interface AlertRule {
  id: string
  name: string
  metric: string
  operator: '>' | '<' | '=' | '>=' | '<='
  threshold: number
  enabled: boolean
  severity: 'critical' | 'warning' | 'info'
  frequency: 'realtime' | 'daily' | 'weekly'
  departments: string[]
  notifications: {
    email: boolean
    push: boolean
    inApp: boolean
  }
}

const defaultAlertRules: AlertRule[] = [
  { id: 'tth-critical', name: 'Time to Hire Crítico', metric: 'avgTimeToFill', operator: '>', threshold: 45, enabled: true, severity: 'critical', frequency: 'daily', departments: ['all'], notifications: { email: true, push: true, inApp: true } },
  { id: 'conversion-low', name: 'Taxa de Conversão Baixa', metric: 'conversionRate', operator: '<', threshold: 1.5, enabled: true, severity: 'warning', frequency: 'weekly', departments: ['all'], notifications: { email: true, push: false, inApp: true } },
  { id: 'nps-declining', name: 'NPS em Declínio', metric: 'npsScore', operator: '<', threshold: 75, enabled: true, severity: 'warning', frequency: 'daily', departments: ['all'], notifications: { email: false, push: true, inApp: true } },
  { id: 'no-hires', name: 'Sem Contratações', metric: 'totalHires', operator: '=', threshold: 0, enabled: true, severity: 'critical', frequency: 'weekly', departments: ['all'], notifications: { email: true, push: true, inApp: true } },
  { id: 'quality-score-low', name: 'Score de Qualidade Baixo', metric: 'qualityOfHireScore', operator: '<', threshold: 3.5, enabled: true, severity: 'warning', frequency: 'weekly', departments: ['all'], notifications: { email: true, push: false, inApp: true } },
]

function mapAlertTypeToMetric(alertType: string): string {
  const mapping: Record<string, string> = { time_to_hire_critical: 'avgTimeToFill', conversion_rate_low: 'conversionRate', nps_declining: 'npsScore', no_hires: 'totalHires', quality_score_low: 'qualityOfHireScore' }
  return mapping[alertType] || alertType
}

function getOperatorForType(alertType: string): string {
  if (alertType.includes('low') || alertType.includes('declining')) return '<'
  if (alertType.includes('critical') || alertType.includes('high')) return '>'
  return '>'
}

function getSeverityForType(alertType: string): string {
  if (alertType.includes('critical')) return 'critical'
  if (alertType.includes('risk') || alertType.includes('pending')) return 'warning'
  return 'info'
}

function convertPreferencesToRules(preferences: AlertPreference[]): AlertRule[] {
  return preferences.map(pref => ({
    id: pref.alert_type,
    name: pref.name || pref.alert_type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
    metric: mapAlertTypeToMetric(pref.alert_type),
    operator: getOperatorForType(pref.alert_type) as '>' | '<' | '=' | '>=' | '<=',
    threshold: pref.threshold || 0,
    enabled: pref.is_enabled,
    severity: getSeverityForType(pref.alert_type) as 'critical' | 'warning' | 'info',
    frequency: 'daily' as const,
    departments: ['all'],
    notifications: { email: pref.channels.email, push: pref.channels.bell, inApp: pref.channels.bell }
  }))
}

function getSuggestedActions(metric: string, _currentValue: number, _threshold: number): string[] {
  switch (metric) {
    case 'avgTimeToFill': return ['Revisar processo de entrevistas para otimização', 'Implementar automação na triagem inicial', 'Reduzir número de etapas do processo', 'Agendar reunião com gestores para alinhar requisitos']
    case 'conversionRate': return ['Melhorar qualidade do sourcing', 'Revisar critérios de triagem', 'Implementar pré-qualificação mais rigorosa', 'Analisar feedback dos candidatos rejeitados']
    case 'npsScore': return ['Coletar feedback detalhado dos candidatos', 'Melhorar comunicação durante o processo', 'Revisar experiência do candidato', 'Implementar follow-up pós-entrevista']
    case 'totalHires': return ['Aumentar atividades de sourcing', 'Revisar requisitos das vagas', 'Implementar sourcing passivo', 'Buscar parcerias com universidades']
    case 'qualityOfHireScore': return ['Melhorar processo de avaliação técnica', 'Implementar entrevistas comportamentais', 'Revisar aderência cultural', 'Acompanhar onboarding dos novos contratados']
    default: return ['Analisar métrica em detalhes', 'Consultar gestor direto']
  }
}

function getCategoryFromMetric(metric: string): KPIAlert['category'] {
  switch (metric) {
    case 'avgTimeToFill': return 'deadline'
    case 'conversionRate': return 'performance'
    case 'npsScore': return 'quality'
    case 'totalHires': return 'target'
    case 'qualityOfHireScore': return 'quality'
    default: return 'performance'
  }
}

function getMetricDisplayName(metric: string): string {
  switch (metric) {
    case 'avgTimeToFill': return 'Tempo de Preenchimento'
    case 'conversionRate': return 'Taxa de Conversão'
    case 'npsScore': return 'NPS'
    case 'totalHires': return 'Total de Contratações'
    case 'qualityOfHireScore': return 'Score de Qualidade'
    default: return metric
  }
}

function getPriorityFromSeverity(severity: string, variance: number): KPIAlert['priority'] {
  if (severity === 'critical') return variance > 50 ? 'urgent' : 'high'
  if (severity === 'warning') return variance > 25 ? 'high' : 'medium'
  return 'low'
}

function getAffectedJobs(_recruiter: Record<string, unknown>): string[] {
  return [`Vaga ${Math.floor(Math.random() * 100)}`]
}

function getEstimatedImpact(_metric: string, variance: number): KPIAlert['estimatedImpact'] {
  if (variance > 50) return 'high'
  if (variance > 25) return 'medium'
  return 'low'
}

export function useKPIAlertSystem(recruiterData: Record<string, unknown>[], onAlertAction: (alertId: string, action: string) => void) {
  const [alerts, setAlerts] = useState<KPIAlert[]>([])
  const [backendAlerts, setBackendAlerts] = useState<BackendAlert[]>([])
  const [alertPreferences, setAlertPreferences] = useState<AlertPreference[]>([])
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
      if (response.ok) { const data = await response.json(); setBackendAlerts(data) }
    } catch (error) {}
  }, [])

  const fetchPreferences = useCallback(async () => {
    try {
      const response = await fetch('/api/backend-proxy/alerts/preferences?user_id=default')
      if (response.ok) {
        const data = await response.json()
        setAlertPreferences(data.preferences || [])
        setAlertRules(convertPreferencesToRules(data.preferences || []))
      }
    } catch (error) { setAlertRules(defaultAlertRules) }
  }, [])

  useEffect(() => {
    const loadData = async () => { setIsLoading(true); await Promise.all([fetchAlertsFromBackend(), fetchPreferences()]); setIsLoading(false) }
    loadData()
  }, [fetchAlertsFromBackend, fetchPreferences])

  useEffect(() => { if (alertRules.length === 0) setAlertRules(defaultAlertRules) }, [alertRules.length])

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
          newAlerts.push({
            id: `alert-${recruiter.name}-${rule.id}-${Date.now()}`,
            type: rule.severity === 'critical' ? 'critical' : rule.severity === 'warning' ? 'warning' : 'info',
            category: getCategoryFromMetric(rule.metric),
            title: `${rule.name} - ${recruiter.name}`,
            description: `${getMetricDisplayName(rule.metric)} está ${rule.operator === '<' ? 'abaixo' : 'acima'} do limite (${metricValue} vs ${rule.threshold})`,
            recruiterName: String(recruiter.name), recruiterId: String(recruiter.name).toLowerCase().replace(' ', '_'),
            department: String(recruiter.department), metric: rule.metric, currentValue: metricValue, targetValue: rule.threshold,
            threshold: rule.threshold, variance: Math.abs(variance), trend: variance > 0 ? 'up' : 'down',
            createdAt: new Date(), isRead: false, isArchived: false,
            priority: getPriorityFromSeverity(rule.severity, Math.abs(variance)),
            suggestedActions: getSuggestedActions(rule.metric, metricValue, rule.threshold),
            affectedJobs: getAffectedJobs(recruiter), estimatedImpact: getEstimatedImpact(rule.metric, Math.abs(variance))
          })
        }
      })
    })
    return newAlerts
  }, [recruiterData, alertRules])

  useEffect(() => {
    setAlerts(prevAlerts => {
      const existingAlerts = prevAlerts.filter(alert => !alert.isArchived)
      const newAlertsFiltered = generateAlerts.filter(newAlert => !existingAlerts.some(existing => existing.recruiterId === newAlert.recruiterId && existing.metric === newAlert.metric))
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
        case 'priority': { const po = { urgent: 4, high: 3, medium: 2, low: 1 }; return po[b.priority] - po[a.priority] }
        case 'severity': { const so = { critical: 3, warning: 2, info: 1, success: 0 }; return so[b.type] - so[a.type] }
        default: return b.createdAt.getTime() - a.createdAt.getTime()
      }
    })
  }, [alerts, showArchived, filterType, filterCategory, sortBy])

  const handleMarkAsRead = (alertId: string) => { setAlerts(prev => prev.map(a => a.id === alertId ? { ...a, isRead: true } : a)); onAlertAction(alertId, 'mark_read') }
  const handleArchiveAlert = (alertId: string) => { setAlerts(prev => prev.map(a => a.id === alertId ? { ...a, isArchived: true } : a)); onAlertAction(alertId, 'archive') }
  const handleDeleteAlert = (alertId: string) => { setAlerts(prev => prev.filter(a => a.id !== alertId)); onAlertAction(alertId, 'delete') }
  const handleSendNotification = (alertId: string) => { onAlertAction(alertId, 'send_notification') }

  const handleRefreshAlerts = async () => {
    setIsRefreshing(true)
    try { await Promise.all([fetchAlertsFromBackend(), fetchPreferences()]); toast.success('Alertas atualizados com sucesso') }
    catch (error) { toast.error('Erro ao atualizar alertas', { description: "Verifique sua conexão e tente novamente." }) }
    finally { setIsRefreshing(false) }
  }

  const handleUpdateRules = async (newRules: AlertRule[]) => {
    setAlertRules(newRules); setShowSettingsModal(false); await fetchPreferences(); toast.success('Configurações salvas com sucesso')
  }

  const alertStats = useMemo(() => {
    const unreadAlerts = alerts.filter(a => !a.isRead && !a.isArchived)
    return {
      total: unreadAlerts.length,
      critical: unreadAlerts.filter(a => a.type === 'critical').length,
      warning: unreadAlerts.filter(a => a.type === 'warning').length,
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
    alerts, filteredAlerts, alertRules, alertStats,
    filterType, setFilterType, filterCategory, setFilterCategory,
    sortBy, setSortBy, showArchived, setShowArchived,
    selectedAlert, setSelectedAlert, isRefreshing, isLoading,
    showSettingsModal, setShowSettingsModal,
    handleMarkAsRead, handleArchiveAlert, handleDeleteAlert,
    handleSendNotification, handleRefreshAlerts, handleUpdateRules,
  }
}
