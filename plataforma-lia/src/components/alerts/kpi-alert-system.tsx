"use client"

import { useState, useEffect, useMemo, useCallback } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import {
  AlertTriangle, CheckCircle, Clock, TrendingDown, TrendingUp,
  Bell, BellOff, Settings, Eye, EyeOff, Users, Target,
  Timer, Percent, DollarSign, Star, Calendar, RefreshCw,
  X, Send, Mail, Zap, AlertCircle, Info, ChevronDown,
  ChevronUp, Filter, MoreVertical, Archive, Trash2, Loader2
} from "lucide-react"
import { AlertSettingsModal } from "./alert-settings-modal"
import { toast } from "sonner"

interface KPIAlert {
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

interface AlertRule {
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

interface KPIAlertSystemProps {
  recruiterData: Record<string, unknown>[]
  onAlertAction: (alertId: string, action: string) => void
}

export function KPIAlertSystem({ recruiterData, onAlertAction }: KPIAlertSystemProps) {
  const [alerts, setAlerts] = useState<KPIAlert[]>([])
  const [backendAlerts, setBackendAlerts] = useState<BackendAlert[]>([])
  const [alertPreferences, setAlertPreferences] = useState<AlertPreference[]>([])
  const [alertRules, setAlertRules] = useState<AlertRule[]>([])
  const [showSettings, setShowSettings] = useState(false)
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

  const convertPreferencesToRules = (preferences: AlertPreference[]): AlertRule[] => {
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
      notifications: {
        email: pref.channels.email,
        push: pref.channels.bell,
        inApp: pref.channels.bell
      }
    }))
  }

  const mapAlertTypeToMetric = (alertType: string): string => {
    const mapping: Record<string, string> = {
      time_to_hire_critical: 'avgTimeToFill',
      conversion_rate_low: 'conversionRate',
      nps_declining: 'npsScore',
      no_hires: 'totalHires',
      quality_score_low: 'qualityOfHireScore'
    }
    return mapping[alertType] || alertType
  }

  const getOperatorForType = (alertType: string): string => {
    if (alertType.includes('low') || alertType.includes('declining')) return '<'
    if (alertType.includes('critical') || alertType.includes('high')) return '>'
    return '>'
  }

  const getSeverityForType = (alertType: string): string => {
    if (alertType.includes('critical')) return 'critical'
    if (alertType.includes('risk') || alertType.includes('pending')) return 'warning'
    return 'info'
  }

  useEffect(() => {
    const loadData = async () => {
      setIsLoading(true)
      await Promise.all([fetchAlertsFromBackend(), fetchPreferences()])
      setIsLoading(false)
    }
    loadData()
  }, [fetchAlertsFromBackend, fetchPreferences])

  const defaultAlertRules: AlertRule[] = [
    {
      id: 'tth-critical',
      name: 'Time to Hire Crítico',
      metric: 'avgTimeToFill',
      operator: '>',
      threshold: 45,
      enabled: true,
      severity: 'critical',
      frequency: 'daily',
      departments: ['all'],
      notifications: { email: true, push: true, inApp: true }
    },
    {
      id: 'conversion-low',
      name: 'Taxa de Conversão Baixa',
      metric: 'conversionRate',
      operator: '<',
      threshold: 1.5,
      enabled: true,
      severity: 'warning',
      frequency: 'weekly',
      departments: ['all'],
      notifications: { email: true, push: false, inApp: true }
    },
    {
      id: 'nps-declining',
      name: 'NPS em Declínio',
      metric: 'npsScore',
      operator: '<',
      threshold: 75,
      enabled: true,
      severity: 'warning',
      frequency: 'daily',
      departments: ['all'],
      notifications: { email: false, push: true, inApp: true }
    },
    {
      id: 'no-hires',
      name: 'Sem Contratações',
      metric: 'totalHires',
      operator: '=',
      threshold: 0,
      enabled: true,
      severity: 'critical',
      frequency: 'weekly',
      departments: ['all'],
      notifications: { email: true, push: true, inApp: true }
    },
    {
      id: 'quality-score-low',
      name: 'Score de Qualidade Baixo',
      metric: 'qualityOfHireScore',
      operator: '<',
      threshold: 3.5,
      enabled: true,
      severity: 'warning',
      frequency: 'weekly',
      departments: ['all'],
      notifications: { email: true, push: false, inApp: true }
    }
  ]

  // Gerar alertas baseados nas regras e dados dos recrutadores
  const generateAlerts = useMemo(() => {
    const newAlerts: KPIAlert[] = []

    recruiterData.forEach(recruiter => {
      alertRules.forEach(rule => {
        if (!rule.enabled) return

        const metricValue = recruiter[rule.metric as keyof typeof recruiter]
        if (typeof metricValue !== 'number') return

        let shouldAlert = false
        switch (rule.operator) {
          case '>':
            shouldAlert = metricValue > rule.threshold
            break
          case '<':
            shouldAlert = metricValue < rule.threshold
            break
          case '>=':
            shouldAlert = metricValue >= rule.threshold
            break
          case '<=':
            shouldAlert = metricValue <= rule.threshold
            break
          case '=':
            shouldAlert = metricValue === rule.threshold
            break
        }

        if (shouldAlert) {
          const variance = ((metricValue - rule.threshold) / rule.threshold) * 100

          // Determinar ações sugeridas baseadas no tipo de alerta
          const suggestedActions = getSuggestedActions(rule.metric, metricValue, rule.threshold)

          const alert: KPIAlert = {
            id: `alert-${recruiter.name}-${rule.id}-${Date.now()}`,
            type: rule.severity === 'critical' ? 'critical' : rule.severity === 'warning' ? 'warning' : 'info',
            category: getCategoryFromMetric(rule.metric),
            title: `${rule.name} - ${recruiter.name}`,
            description: `${getMetricDisplayName(rule.metric)} está ${rule.operator === '<' ? 'abaixo' : 'acima'} do limite (${metricValue} vs ${rule.threshold})`,
            recruiterName: recruiter.name,
            recruiterId: recruiter.name.toLowerCase().replace(' ', '_'),
            department: recruiter.department,
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
          }

          newAlerts.push(alert)
        }
      })
    })

    return newAlerts
  }, [recruiterData, alertRules])

  // Inicializar regras padrão
  useEffect(() => {
    if (alertRules.length === 0) {
      setAlertRules(defaultAlertRules)
    }
  }, [])

  // Atualizar alertas quando os dados mudarem
  useEffect(() => {
    setAlerts(prevAlerts => {
      // Manter alertas existentes não lidos e adicionar novos
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

  // Funções auxiliares
  const getSuggestedActions = (metric: string, currentValue: number, threshold: number): string[] => {
    switch (metric) {
      case 'avgTimeToFill':
        return [
          'Revisar processo de entrevistas para otimização',
          'Implementar automação na triagem inicial',
          'Reduzir número de etapas do processo',
          'Agendar reunião com gestores para alinhar requisitos'
        ]
      case 'conversionRate':
        return [
          'Melhorar qualidade do sourcing',
          'Revisar critérios de triagem',
          'Implementar pré-qualificação mais rigorosa',
          'Analisar feedback dos candidatos rejeitados'
        ]
      case 'npsScore':
        return [
          'Coletar feedback detalhado dos candidatos',
          'Melhorar comunicação durante o processo',
          'Revisar experiência do candidato',
          'Implementar follow-up pós-entrevista'
        ]
      case 'totalHires':
        return [
          'Aumentar atividades de sourcing',
          'Revisar requisitos das vagas',
          'Implementar sourcing passivo',
          'Buscar parcerias com universidades'
        ]
      case 'qualityOfHireScore':
        return [
          'Melhorar processo de avaliação técnica',
          'Implementar entrevistas comportamentais',
          'Revisar fit cultural',
          'Acompanhar onboarding dos novos contratados'
        ]
      default:
        return ['Analisar métrica em detalhes', 'Consultar gestor direto']
    }
  }

  const getCategoryFromMetric = (metric: string): KPIAlert['category'] => {
    switch (metric) {
      case 'avgTimeToFill': return 'deadline'
      case 'conversionRate': return 'performance'
      case 'npsScore': return 'quality'
      case 'totalHires': return 'target'
      case 'qualityOfHireScore': return 'quality'
      default: return 'performance'
    }
  }

  const getMetricDisplayName = (metric: string): string => {
    switch (metric) {
      case 'avgTimeToFill': return 'Time to Fill'
      case 'conversionRate': return 'Taxa de Conversão'
      case 'npsScore': return 'NPS Score'
      case 'totalHires': return 'Total de Contratações'
      case 'qualityOfHireScore': return 'Score de Qualidade'
      default: return metric
    }
  }

  const getPriorityFromSeverity = (severity: string, variance: number): KPIAlert['priority'] => {
    if (severity === 'critical') return variance > 50 ? 'urgent' : 'high'
    if (severity === 'warning') return variance > 25 ? 'high' : 'medium'
    return 'low'
  }

  const getAffectedJobs = (_recruiter: Record<string, unknown>): string[] => {
    // Mock de vagas afetadas
    return [`Vaga ${Math.floor(Math.random() * 100)}`]
  }

  const getEstimatedImpact = (metric: string, variance: number): KPIAlert['estimatedImpact'] => {
    if (variance > 50) return 'high'
    if (variance > 25) return 'medium'
    return 'low'
  }

  // Filtrar alertas
  const filteredAlerts = useMemo(() => {
    const filtered = alerts.filter(alert => {
      if (!showArchived && alert.isArchived) return false
      if (filterType !== 'all' && alert.type !== filterType) return false
      if (filterCategory !== 'all' && alert.category !== filterCategory) return false
      return true
    })

    // Ordenar (criar cópia para não mutar)
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

  // Ações dos alertas
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

  const handleDeleteAlert = (alertId: string) => {
    setAlerts(prev => prev.filter(alert => alert.id !== alertId))
    onAlertAction(alertId, 'delete')
  }

  const handleSendNotification = (alertId: string) => {
    // Implementar envio de notificação
    onAlertAction(alertId, 'send_notification')
  }

  const handleRefreshAlerts = async () => {
    setIsRefreshing(true)
    try {
      await Promise.all([fetchAlertsFromBackend(), fetchPreferences()])
      toast.success('Alertas atualizados com sucesso')
    } catch (error) {
      toast.error('Erro ao atualizar alertas')
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

  // Estatísticas dos alertas
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

  const getAlertIcon = (type: KPIAlert['type']) => {
    switch (type) {
      case 'critical': return <AlertTriangle className="w-5 h-5 text-status-error" />
      case 'warning': return <AlertCircle className="w-5 h-5 text-status-warning" />
      case 'info': return <Info className="w-5 h-5 text-lia-text-secondary dark:text-lia-text-tertiary" />
      case 'success': return <CheckCircle className="w-5 h-5 text-status-success" />
    }
  }

  const getAlertBadgeColor = (type: KPIAlert['type']) => {
    switch (type) {
      case 'critical': return 'bg-status-error/10 text-status-error border-status-error/30'
      case 'warning': return 'bg-status-warning/10 text-status-warning border-status-warning/30'
      case 'info': return 'bg-gray-100 dark:bg-lia-bg-secondary text-lia-text-secondary dark:text-lia-text-tertiary border-lia-border-default dark:border-lia-border-default'
      case 'success': return 'bg-status-success/10 text-status-success border-status-success/30'
    }
  }

  const getPriorityBadgeColor = (priority: KPIAlert['priority']) => {
    switch (priority) {
      case 'urgent': return 'bg-status-error text-white'
      case 'high': return 'bg-wedo-orange text-white'
      case 'medium': return 'bg-status-warning text-white'
      case 'low': return 'bg-gray-600 text-white'
    }
  }

  return (
    <div className="space-y-6">
      {/* Header com Estatísticas */}
      <Card className="border-l-4 border-l-gray-400 dark:border-l-gray-500">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2 font-sans">
                <Bell className="w-5 h-5 text-lia-text-secondary dark:text-lia-text-tertiary" />
                Sistema de Alertas KPI
              </CardTitle>
              <p className="text-sm lia-text-base mt-1">
                Monitoramento automático da performance dos recrutadores
              </p>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleRefreshAlerts}
                disabled={isRefreshing}
                className="gap-2"
              >
                <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin motion-reduce:animate-none' : ''}`} />
                Atualizar
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowSettingsModal(true)}
                className="gap-2"
              >
                <Settings className="w-4 h-4" />
                Configurar
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-lia-text-primary">{alertStats.total}</div>
              <div className="text-sm lia-text-base">Total de Alertas</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-status-error">{alertStats.critical}</div>
              <div className="text-sm lia-text-base">Críticos</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-status-warning">{alertStats.warning}</div>
              <div className="text-sm lia-text-base">Avisos</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-wedo-purple">{alertStats.byCategory.performance}</div>
              <div className="text-sm lia-text-base">Performance</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-wedo-orange">{alertStats.byCategory.deadline}</div>
              <div className="text-sm lia-text-base">Prazos</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Filtros e Controles */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Filtros e Controles</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="text-sm font-medium text-lia-text-primary dark:text-lia-text-primary mb-2 block">Tipo</label>
              <select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
                className="w-full p-2 border border-lia-border-default rounded-md text-sm"
              >
                <option value="all">Todos</option>
                <option value="critical">Crítico</option>
                <option value="warning">Aviso</option>
                <option value="info">Informação</option>
                <option value="success">Sucesso</option>
              </select>
            </div>

            <div>
              <label className="text-sm font-medium text-lia-text-primary dark:text-lia-text-primary mb-2 block">Categoria</label>
              <select
                value={filterCategory}
                onChange={(e) => setFilterCategory(e.target.value)}
                className="w-full p-2 border border-lia-border-default rounded-md text-sm"
              >
                <option value="all">Todas</option>
                <option value="performance">Performance</option>
                <option value="deadline">Prazos</option>
                <option value="target">Metas</option>
                <option value="budget">Orçamento</option>
                <option value="quality">Qualidade</option>
              </select>
            </div>

            <div>
              <label className="text-sm font-medium text-lia-text-primary dark:text-lia-text-primary mb-2 block">Ordenar por</label>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as typeof sortBy)}
                className="w-full p-2 border border-lia-border-default rounded-md text-sm"
              >
                <option value="date">Data</option>
                <option value="priority">Prioridade</option>
                <option value="severity">Severidade</option>
              </select>
            </div>

            <div>
              <label className="text-sm font-medium text-lia-text-primary dark:text-lia-text-primary mb-2 block">Ações</label>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowArchived(!showArchived)}
                  className="gap-2 flex-1"
                >
                  {showArchived ? <EyeOff className="w-3 h-3" /> : <Eye className="w-3 h-3" />}
                  {showArchived ? 'Ocultar' : 'Mostrar'} Arquivados
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Lista de Alertas */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">
            Alertas Ativos ({filteredAlerts.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {filteredAlerts.length === 0 ? (
              <div className="text-center py-8 lia-text-base">
                <Bell className="w-12 h-12 mx-auto mb-4 lia-text-base" />
                <p aria-live="polite" aria-atomic="true">Nenhum alerta encontrado</p>
                <p className="text-sm">Todos os KPIs estão dentro dos parâmetros esperados</p>
              </div>
            ) : (
              filteredAlerts.map((alert) => (
                <div
                  key={alert.id}
                  className={`p-4 border rounded-md transition-colors motion-reduce:transition-none ${
 alert.isRead ? 'bg-gray-50' : 'bg-lia-bg-primary border-l-4'
                  } ${
                    alert.type === 'critical' ? 'border-l-red-500' :
                    alert.type === 'warning' ? 'border-l-yellow-500' :
                    alert.type === 'info' ? 'border-l-gray-400 dark:border-l-gray-500' :
                    'border-l-green-500'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-3 flex-1">
                      {/* Alert Icon */}
                      <div className="mt-1">
                        {getAlertIcon(alert.type)}
                      </div>

                      {/* Alert Content */}
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
 <h4 className={`font-medium ${alert.isRead ? 'text-lia-text-primary' : 'text-lia-text-primary'}`}>
                            {alert.title}
                          </h4>
                          <Badge className={`text-xs ${getAlertBadgeColor(alert.type)}`}>
                            {alert.type}
                          </Badge>
                          <Badge className={`text-xs ${getPriorityBadgeColor(alert.priority)}`}>
                            {alert.priority}
                          </Badge>
                        </div>

                        <p className="text-sm lia-text-base mb-3">{alert.description}</p>

                        {/* Métricas */}
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-3 p-3 bg-gray-50 rounded-md">
                          <div className="text-center">
                            <div className="text-lg font-bold text-lia-text-primary">{alert.currentValue}</div>
                            <div className="text-xs lia-text-base">Atual</div>
                          </div>
                          <div className="text-center">
                            <div className="text-lg font-bold lia-text-base">{alert.targetValue}</div>
                            <div className="text-xs lia-text-base">Meta</div>
                          </div>
                          <div className="text-center">
                            <div className={`text-lg font-bold ${alert.variance > 25 ? 'text-status-error' : 'text-status-warning'}`}>
                              {alert.variance.toFixed(1)}%
                            </div>
                            <div className="text-xs lia-text-base">Variação</div>
                          </div>
                          <div className="text-center">
                            <div className="flex items-center justify-center">
                              {alert.trend === 'up' ? (
                                <TrendingUp className="w-5 h-5 text-status-error" />
                              ) : (
                                <TrendingDown className="w-5 h-5 text-status-success" />
                              )}
                            </div>
                            <div className="text-xs lia-text-base">Tendência</div>
                          </div>
                        </div>

                        {/* Informações Adicionais */}
                        <div className="flex items-center gap-4 text-xs lia-text-base mb-3">
                          <span className="flex items-center gap-1">
                            <Users className="w-3 h-3" />
                            {alert.department}
                          </span>
                          <span className="flex items-center gap-1">
                            <Calendar className="w-3 h-3" />
                            {alert.createdAt.toLocaleDateString('pt-BR')}
                          </span>
                          {alert.affectedJobs && (
                            <span className="flex items-center gap-1">
                              <Target className="w-3 h-3" />
                              {alert.affectedJobs.length} vagas afetadas
                            </span>
                          )}
                        </div>

                        {/* Ações Sugeridas */}
                        {alert.suggestedActions.length > 0 && (
                          <div className="border-t pt-3">
                            <h5 className="text-sm font-medium text-lia-text-primary mb-2">Ações Sugeridas:</h5>
                            <ul className="space-y-1">
                              {alert.suggestedActions.slice(0, 2).map((action, index) => (
                                <li key={`action-${index}`} className="text-sm lia-text-base flex items-start gap-2">
                                  <span className="text-lia-text-secondary dark:text-lia-text-tertiary mt-1">•</span>
                                  {action}
                                </li>
                              ))}
                            </ul>
                            {alert.suggestedActions.length > 2 && (
                              <Button
                                variant="ghost"
                                size="sm"
                                className="mt-2 text-lia-text-secondary dark:text-lia-text-tertiary h-auto p-0"
                                onClick={() => setSelectedAlert(alert)}
                              >
                                Ver todas as {alert.suggestedActions.length} sugestões
                              </Button>
                            )}
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center gap-2 ml-4">
                      {!alert.isRead && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleMarkAsRead(alert.id)}
                          className="gap-2"
                        >
                          <Eye className="w-3 h-3" />
                          Marcar Lido
                        </Button>
                      )}
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleSendNotification(alert.id)}
                        className="gap-2"
                      >
                        <Send className="w-3 h-3" />
                        Notificar
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleArchiveAlert(alert.id)}
                        className="gap-2"
                      >
                        <Archive className="w-3 h-3" />
                        Arquivar
                      </Button>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>

      {/* Modal de Detalhes do Alerta */}
      {selectedAlert && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
          <div className="bg-lia-bg-primary rounded-md w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold">Detalhes do Alerta</h3>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setSelectedAlert(null)}
                >
                  <X className="w-4 h-4" />
                </Button>
              </div>

              <div className="space-y-4">
                <div>
                  <h4 className="font-medium mb-2">Todas as Ações Sugeridas:</h4>
                  <ul className="space-y-2">
                    {selectedAlert.suggestedActions.map((action, index) => (
                      <li key={`sel-action-${index}`} className="text-sm lia-text-base flex items-start gap-2 p-2 bg-gray-50 rounded-md">
                        <span className="text-lia-text-secondary dark:text-lia-text-tertiary mt-1">•</span>
                        {action}
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="flex gap-2 pt-4 border-t">
                  <Button
                    onClick={() => {
                      handleMarkAsRead(selectedAlert.id)
                      setSelectedAlert(null)
                    }}
                    className="gap-2"
                  >
                    <CheckCircle className="w-4 h-4" />
                    Implementar Ações
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => setSelectedAlert(null)}
                  >
                    Fechar
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Modal de Configurações */}
      <AlertSettingsModal
        isOpen={showSettingsModal}
        onClose={() => setShowSettingsModal(false)}
        alertRules={alertRules}
        onUpdateRules={handleUpdateRules}
      />
    </div>
  )
}
