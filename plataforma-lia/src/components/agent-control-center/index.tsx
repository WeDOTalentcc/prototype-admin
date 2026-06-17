"use client"

import React, { useState, useEffect, useCallback } from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Chip } from '@/components/ui/chip'
import { 
  Activity, RefreshCcw, CheckCircle, Clock, XCircle, 
  AlertTriangle, ChevronRight,
  Filter, X, Brain, Zap, Target, Users
} from 'lucide-react'
function MetricCard({ variant, icon, title, value, trend, accentColor }: {
  variant?: string; icon: React.ReactNode; title: string; value: React.ReactNode; trend?: number; accentColor?: string
}) {
  return (
    <div className="p-3 rounded-lg bg-lia-bg-secondary dark:bg-lia-bg-tertiary border border-lia-border-default">
      <div className="flex items-center gap-2 mb-1">
        <span style={{ color: accentColor }}>{icon}</span>
        <span className="text-xs text-lia-text-muted">{title}</span>
      </div>
      <div className="flex items-baseline gap-2">
        <span className="text-lg font-semibold text-lia-text-primary">{value}</span>
        {trend !== undefined && <CompactDelta value={trend} />}
      </div>
    </div>
  )
}

function CompactDelta({ value }: { value: number }) {
  if (value === 0) return null
  const isPositive = value > 0
  return (
    <span className={`text-xs font-medium ${isPositive ? 'text-green-600' : 'text-red-500'}`}>
      {isPositive ? '+' : ''}{value}%
    </span>
  )
}
import { 
  agentMonitoringService, 
  AgentSummary, 
  ActivityEvent, 
  ProactiveAlert,
  GlobalMetrics,
  ActivityFeedFilters
} from '@/services/agent-monitoring'
import { AgentDetailPanel } from './agent-detail-panel'
import { Sparkline } from './sparkline'

interface AgentControlCenterProps {
  className?: string
}

// Calibration dashboard types
interface CalibrationDomain {
  domain: string
  total_events: number
  agree_count: number
  disagree_count: number
  agreement_rate: number
  avg_lia_score: number
  needs_calibration: boolean
}
interface CalibrationDashboard {
  overall: { total_events: number; agreement_rate: number; avg_lia_score: number; agree_count: number; disagree_count: number }
  domains: CalibrationDomain[]
  weights: { dimension: string; base_weight: number; adjusted_weight: number }[]
  pending_suggestions: number
}

// ML Predictions types
interface PredictionVacancy {
  job_id: string
  title: string
  seniority: string
  days_open: number
  predicted_ttf_days: number
  confidence: number
  source: string
  factors: string[]
  is_overdue: boolean
}
interface MLPredictions {
  vacancies: PredictionVacancy[]
  company_avg_ttf: number
  market_avg_ttf: number
  total_open: number
  overdue_count: number
}

// Quality dashboard types
interface QualityAgent {
  agent_id: string
  total_executions: number
  avg_confidence: number
  error_rate: number
  human_intervention_rate: number
  calibration_events?: number
  fairness_checks?: number
  fairness_blocks?: number
  fairness_warning_rate?: number
  avg_lia_score?: number
  trend: 'improving' | 'stable' | 'degrading' | 'insufficient_data'
}
interface QualityDashboard {
  agents: QualityAgent[]
  overall: { total_executions: number; avg_confidence: number; error_rate: number; fairness_score: number }
  period: string
}

export function AgentControlCenter({ className }: AgentControlCenterProps) {
  const [globalMetrics, setGlobalMetrics] = useState<GlobalMetrics | null>(null)
  const [agents, setAgents] = useState<AgentSummary[]>([])
  const [activities, setActivities] = useState<ActivityEvent[]>([])
  const [proactiveAlerts, setProactiveAlerts] = useState<ProactiveAlert[]>([])
  const [qualityData, setQualityData] = useState<QualityDashboard | null>(null)
  const [qualityPeriod, setQualityPeriod] = useState<'7d' | '30d' | '90d'>('7d')
  const [predictions, setPredictions] = useState<MLPredictions | null>(null)
  const [calibration, setCalibration] = useState<CalibrationDashboard | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)
  const [selectedAgent, setSelectedAgent] = useState<AgentSummary | null>(null)
  const [isDetailPanelOpen, setIsDetailPanelOpen] = useState(false)
  const [activityFilters, setActivityFilters] = useState<ActivityFeedFilters>({
    limit: 15
  })
  const [selectedAgentFilter, setSelectedAgentFilter] = useState<string[]>([])
  const [selectedStatusFilter, setSelectedStatusFilter] = useState<string[]>([])
  const [filterPeriod, setFilterPeriod] = useState<'today' | 'week'>('today')

  const fetchQualityData = useCallback(async () => {
    try {
      const res = await fetch(`/api/backend-proxy/analytics/agent-quality-dashboard?period=${qualityPeriod}`)
      if (res.ok) {
        setQualityData(await res.json())
      }
    } catch {
      // non-blocking
    }
  }, [qualityPeriod])

  const fetchPredictions = useCallback(async () => {
    try {
      const res = await fetch('/api/backend-proxy/analytics/ml-predictions')
      if (res.ok) {
        setPredictions(await res.json())
      }
    } catch {
      // non-blocking
    }
  }, [])

  const fetchCalibration = useCallback(async () => {
    try {
      const res = await fetch('/api/backend-proxy/analytics/calibration-dashboard?days=30')
      if (res.ok) {
        setCalibration(await res.json())
      }
    } catch {
      // non-blocking
    }
  }, [])

  const fetchData = useCallback(async () => {
    setIsLoading(true)
    try {
      const [metricsData, agentsData, feedData, alertsData] = await Promise.all([
        agentMonitoringService.getGlobalMetrics(),
        agentMonitoringService.getAllAgentsSummary(),
        agentMonitoringService.getActivityFeed({
          ...activityFilters,
          agentId: selectedAgentFilter.length === 1 ? selectedAgentFilter[0] : undefined,
          status: selectedStatusFilter.length === 1 ? selectedStatusFilter[0] : undefined
        }),
        agentMonitoringService.getProactiveAlerts()
      ])

      setGlobalMetrics(metricsData)
      setAgents(agentsData)
      setActivities(feedData)
      setProactiveAlerts(alertsData)
      setLastUpdated(new Date())
    } catch (error) {
    } finally {
      setIsLoading(false)
    }
  }, [activityFilters, selectedAgentFilter, selectedStatusFilter])

  useEffect(() => {
    fetchData()
    fetchQualityData()
    fetchPredictions()
    fetchCalibration()
    const interval = setInterval(fetchData, 30000)
    return () => clearInterval(interval)
  }, [fetchData, fetchQualityData])

  const handleAgentClick = (agent: AgentSummary) => {
    setSelectedAgent(agent)
    setIsDetailPanelOpen(true)
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online': return 'var(--lia-text-secondary)'
      case 'idle': return 'var(--status-warning)'
      case 'warning': return 'var(--status-error)'
      default: return 'var(--lia-text-tertiary)'
    }
  }

  const formatTimeAgo = (timestamp: string | null) => {
    if (!timestamp) return 'N/A'
    const now = new Date()
    const time = new Date(timestamp)
    const diffMs = now.getTime() - time.getTime()
    const diffMin = Math.floor(diffMs / 60000)
    
    if (diffMin < 1) return 'agora'
    if (diffMin < 60) return `há ${diffMin} min`
    const diffHours = Math.floor(diffMin / 60)
    if (diffHours < 24) return `há ${diffHours}h`
    return `há ${Math.floor(diffHours / 24)}d`
  }

  const toggleAgentFilter = (agentId: string) => {
    setSelectedAgentFilter(prev => 
      prev.includes(agentId) 
        ? prev.filter(id => id !== agentId) 
        : [...prev, agentId]
    )
  }

  const toggleStatusFilter = (status: string) => {
    setSelectedStatusFilter(prev => 
      prev.includes(status) 
        ? prev.filter(s => s !== status) 
        : [...prev, status]
    )
  }

  const clearFilters = () => {
    setSelectedAgentFilter([])
    setSelectedStatusFilter([])
  }

  if (!globalMetrics || agents.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex items-center gap-2 text-lia-text-tertiary">
          <RefreshCcw className="w-5 h-5 animate-spin motion-reduce:animate-none" />
          <span>Carregando Centro de Controle...</span>
        </div>
      </div>
    )
  }

  return (
    <div className={`flex-1 overflow-y-auto p-6 bg-white dark:bg-lia-bg-primary ${className}`}>
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold mb-1 flex items-center gap-2 text-lia-text-primary">
              <Brain className="w-5 h-5 text-wedo-cyan" />
              Centro de Controle IA
            </h2>
            <p className="text-sm text-lia-text-tertiary">
              Monitore seus agentes especializados em tempo real
            </p>
          </div>
          <div className="flex items-center gap-3">
            {lastUpdated && (
              <span className="text-xs text-lia-text-muted">
                Atualizado {formatTimeAgo(lastUpdated.toISOString())}
              </span>
            )}
            <Button
              variant="outline"
              size="sm"
              onClick={fetchData}
              disabled={isLoading}
              className="text-xs border-lia-border-default dark:border-lia-border-default"
            >
              <RefreshCcw className={`w-3 h-3 mr-1 ${isLoading ? 'animate-spin motion-reduce:animate-none' : ''}`} />
              Atualizar
            </Button>
          </div>
        </div>

        {/* Global Metrics Bar */}
        <div className="grid grid-cols-5 gap-3 mb-6">
          <MetricCard
            variant="compact"
            icon={<Zap className="w-4 h-4" />}
            title="Ações Hoje"
            value={globalMetrics.actions_today}
            trend={globalMetrics.actions_delta}
            accentColor="var(--lia-text-secondary)"
          />
          <MetricCard
            variant="compact"
            icon={<Users className="w-4 h-4" />}
            title="Agentes Ativos"
            value={`${globalMetrics.active_agents}/${globalMetrics.total_agents}`}
            accentColor="var(--lia-text-secondary)"
          />
          <MetricCard
            variant="compact"
            icon={<Target className="w-4 h-4" />}
            title="Taxa de Sucesso"
            value={`${globalMetrics.success_rate.toFixed(1)}%`}
            accentColor="var(--wedo-green-bright)"
          />
          <MetricCard
            variant="compact"
            icon={<Clock className="w-4 h-4" />}
            title="Tempo Médio"
            value={`${globalMetrics.avg_response_time}s`}
            accentColor="var(--lia-text-secondary)"
          />
          <MetricCard
            variant="compact"
            icon={<AlertTriangle className="w-4 h-4" />}
            title="Alertas"
            value={globalMetrics.proactive_alerts}
            accentColor={globalMetrics.proactive_alerts > 0 ? 'var(--status-warning)' : 'var(--wedo-green-bright)'}
          />
        </div>

        {/* Quality Metrics Section */}
        {qualityData?.overall && (
          <div className="mb-6">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-medium text-lia-text-secondary flex items-center gap-2">
                <Target className="w-4 h-4" />
                Qualidade dos Agentes
              </h3>
              <div className="flex items-center gap-1">
                {(['7d', '30d', '90d'] as const).map(p => (
                  <Button
                    key={p}
                    variant="ghost"
                    size="sm"
                    className={`text-xs px-2 py-1 ${qualityPeriod === p ? 'bg-lia-interactive-active' : 'text-lia-text-tertiary'}`}
                    onClick={() => setQualityPeriod(p)}
                  >
                    {p}
                  </Button>
                ))}
              </div>
            </div>
            <div className="grid grid-cols-4 gap-3 mb-4">
              <MetricCard
                icon={<Brain className="w-4 h-4" />}
                title="Confiança Média"
                value={`${(qualityData.overall.avg_confidence * 100).toFixed(0)}%`}
                accentColor="var(--wedo-cyan)"
              />
              <MetricCard
                icon={<CheckCircle className="w-4 h-4" />}
                title="Taxa de Erro"
                value={`${(qualityData.overall.error_rate * 100).toFixed(1)}%`}
                accentColor={qualityData.overall.error_rate < 0.05 ? 'var(--wedo-green-bright)' : 'var(--status-error)'}
              />
              <MetricCard
                icon={<Activity className="w-4 h-4" />}
                title="Fairness Score"
                value={`${(qualityData.overall.fairness_score * 100).toFixed(0)}%`}
                accentColor={qualityData.overall.fairness_score >= 0.95 ? 'var(--wedo-green-bright)' : 'var(--status-warning)'}
              />
              <MetricCard
                icon={<Zap className="w-4 h-4" />}
                title="Execuções"
                value={qualityData.overall.total_executions.toLocaleString()}
                accentColor="var(--lia-text-secondary)"
              />
            </div>
            {/* Per-agent quality table */}
            {(qualityData.agents?.length ?? 0) > 0 && (
              <div className="rounded-lg border border-lia-border-subtle overflow-hidden">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="bg-lia-bg-secondary dark:bg-lia-bg-tertiary">
                      <th className="text-left p-2 font-medium text-lia-text-tertiary">Agente</th>
                      <th className="text-right p-2 font-medium text-lia-text-tertiary">Execuções</th>
                      <th className="text-right p-2 font-medium text-lia-text-tertiary">Confiança</th>
                      <th className="text-right p-2 font-medium text-lia-text-tertiary">Erros</th>
                      <th className="text-right p-2 font-medium text-lia-text-tertiary">Fairness</th>
                      <th className="text-center p-2 font-medium text-lia-text-tertiary">Trend</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-lia-border-subtle">
                    {qualityData.agents!.slice(0, 8).map(a => (
                      <tr key={a.agent_id} className="hover:bg-lia-bg-secondary/50">
                        <td className="p-2 font-medium text-lia-text-primary">{a.agent_id}</td>
                        <td className="p-2 text-right text-lia-text-secondary">{a.total_executions}</td>
                        <td className="p-2 text-right text-lia-text-secondary">{(a.avg_confidence * 100).toFixed(0)}%</td>
                        <td className="p-2 text-right">
                          <span className={a.error_rate > 0.05 ? 'text-status-error' : 'text-lia-text-secondary'}>
                            {(a.error_rate * 100).toFixed(1)}%
                          </span>
                        </td>
                        <td className="p-2 text-right text-lia-text-secondary">
                          {a.fairness_checks ? `${a.fairness_checks} checks` : '—'}
                        </td>
                        <td className="p-2 text-center">
                          {a.trend === 'improving' && <span className="text-wedo-green-text-bright">▲</span>}
                          {a.trend === 'stable' && <span className="text-lia-text-disabled">━</span>}
                          {a.trend === 'degrading' && <span className="text-status-error">▼</span>}
                          {a.trend === 'insufficient_data' && <span className="text-lia-text-disabled">?</span>}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* ML Predictions Section */}
        {predictions && (predictions.vacancies?.length ?? 0) > 0 && (
          <div className="mb-6">
            <h3 className="text-sm font-medium text-lia-text-secondary flex items-center gap-2 mb-3">
              <Clock className="w-4 h-4" />
              Previsão Time-to-Fill
            </h3>
            <div className="grid grid-cols-3 gap-3 mb-4">
              <MetricCard
                icon={<Target className="w-4 h-4" />}
                title="Média da Empresa"
                value={`${predictions.company_avg_ttf}d`}
                accentColor="var(--wedo-cyan)"
              />
              <MetricCard
                icon={<Users className="w-4 h-4" />}
                title="Média de Mercado"
                value={`${predictions.market_avg_ttf}d`}
                accentColor="var(--lia-text-secondary)"
              />
              <MetricCard
                icon={<AlertTriangle className="w-4 h-4" />}
                title="Vagas Atrasadas"
                value={predictions.overdue_count}
                accentColor={predictions.overdue_count > 0 ? 'var(--status-error)' : 'var(--wedo-green-bright)'}
              />
            </div>
            <div className="rounded-lg border border-lia-border-subtle overflow-hidden">
              <table className="w-full text-xs">
                <thead>
                  <tr className="bg-lia-bg-secondary dark:bg-lia-bg-tertiary">
                    <th className="text-left p-2 font-medium text-lia-text-tertiary">Vaga</th>
                    <th className="text-right p-2 font-medium text-lia-text-tertiary">Dias Abertos</th>
                    <th className="text-right p-2 font-medium text-lia-text-tertiary">Previsão</th>
                    <th className="text-right p-2 font-medium text-lia-text-tertiary">Confiança</th>
                    <th className="text-center p-2 font-medium text-lia-text-tertiary">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-lia-border-subtle">
                  {predictions.vacancies.slice(0, 10).map(v => (
                    <tr key={v.job_id} className={`hover:bg-lia-bg-secondary/50 ${v.is_overdue ? 'bg-status-error/5' : ''}`}>
                      <td className="p-2">
                        <div className="font-medium text-lia-text-primary truncate max-w-[200px]">{v.title}</div>
                        <div className="text-lia-text-disabled">{v.seniority}</div>
                      </td>
                      <td className="p-2 text-right text-lia-text-secondary">{v.days_open}d</td>
                      <td className="p-2 text-right text-lia-text-secondary">{v.predicted_ttf_days}d</td>
                      <td className="p-2 text-right text-lia-text-secondary">{(v.confidence * 100).toFixed(0)}%</td>
                      <td className="p-2 text-center">
                        {v.is_overdue
                          ? <span className="text-status-error font-medium">Atrasada</span>
                          : <span className="text-lia-text-secondary-bright">No prazo</span>
                        }
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Calibration Dashboard Section */}
        {calibration?.overall && calibration.overall.total_events > 0 && (
          <div className="mb-6">
            <h3 className="text-sm font-medium text-lia-text-secondary flex items-center gap-2 mb-3">
              <Activity className="w-4 h-4" />
              Calibração IA vs. Recrutador
            </h3>
            <div className="grid grid-cols-4 gap-3 mb-4">
              <MetricCard
                icon={<CheckCircle className="w-4 h-4" />}
                title="Taxa de Concordância"
                value={`${(calibration.overall.agreement_rate * 100).toFixed(0)}%`}
                accentColor={calibration.overall.agreement_rate >= 0.75 ? 'var(--wedo-green-bright)' : 'var(--status-warning)'}
              />
              <MetricCard
                icon={<Zap className="w-4 h-4" />}
                title="Total Eventos"
                value={calibration.overall.total_events}
                accentColor="var(--lia-text-secondary)"
              />
              <MetricCard
                icon={<Brain className="w-4 h-4" />}
                title="Score Médio IA"
                value={`${calibration.overall.avg_lia_score}`}
                accentColor="var(--wedo-cyan)"
              />
              <MetricCard
                icon={<AlertTriangle className="w-4 h-4" />}
                title="Sugestões Pendentes"
                value={calibration.pending_suggestions}
                accentColor={calibration.pending_suggestions > 0 ? 'var(--status-warning)' : 'var(--wedo-green-bright)'}
              />
            </div>
            {calibration.domains.length > 0 && (
              <div className="rounded-lg border border-lia-border-subtle overflow-hidden">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="bg-lia-bg-secondary dark:bg-lia-bg-tertiary">
                      <th className="text-left p-2 font-medium text-lia-text-tertiary">Domínio</th>
                      <th className="text-right p-2 font-medium text-lia-text-tertiary">Eventos</th>
                      <th className="text-right p-2 font-medium text-lia-text-tertiary">Concordam</th>
                      <th className="text-right p-2 font-medium text-lia-text-tertiary">Divergem</th>
                      <th className="text-right p-2 font-medium text-lia-text-tertiary">Taxa</th>
                      <th className="text-center p-2 font-medium text-lia-text-tertiary">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-lia-border-subtle">
                    {calibration.domains.map(d => (
                      <tr key={d.domain} className={`hover:bg-lia-bg-secondary/50 ${d.needs_calibration ? 'bg-status-warning/5' : ''}`}>
                        <td className="p-2 font-medium text-lia-text-primary">{d.domain}</td>
                        <td className="p-2 text-right text-lia-text-secondary">{d.total_events}</td>
                        <td className="p-2 text-right text-lia-text-secondary-bright">{d.agree_count}</td>
                        <td className="p-2 text-right text-status-error">{d.disagree_count}</td>
                        <td className="p-2 text-right text-lia-text-secondary">{(d.agreement_rate * 100).toFixed(0)}%</td>
                        <td className="p-2 text-center">
                          {d.needs_calibration
                            ? <span className="text-status-warning font-medium">Calibrar</span>
                            : <span className="text-lia-text-secondary-bright">OK</span>
                          }
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* Proactive Alerts */}
        {proactiveAlerts.length > 0 && (
          <div className="mb-6 p-4 rounded-xl border bg-status-warning/5 border-status-warning/30">
            <div className="flex items-center gap-2 mb-3">
              <AlertTriangle className="w-4 h-4 text-status-warning" />
              <span className="text-sm font-medium text-lia-text-primary">
                Atenção Necessária
              </span>
            </div>
            <div className="space-y-2">
              {proactiveAlerts.map(alert => (
                <div
                  key={alert.id}
                  className="flex items-center justify-between p-3 rounded-xl bg-lia-bg-primary"
                >
                  <div className="flex items-center gap-3">
                    <Chip
                      variant={alert.severity === 'high' ? 'danger' : alert.severity === 'medium' ? 'warning' : 'neutral'}
                      className="text-xs"
                    >
                      {alert.severity}
                    </Chip>
                    <div>
                      <p className="text-sm font-medium text-lia-text-primary">
                        {alert.title}
                      </p>
                      <p className="text-xs text-lia-text-tertiary">
                        {alert.description}
                      </p>
                    </div>
                  </div>
                  <Button variant="ghost" size="sm" className="text-xs">
                    Resolver
                  </Button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Agent Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 mb-8">
          {agents.map((agent) => (
            <Card
              key={agent.id}
              onClick={() => handleAgentClick(agent)}
              className={`border transition-transform motion-reduce:transition-none duration-200 hover:scale-[1.02] hover:cursor-pointer group bg-lia-bg-primary ${selectedAgent?.id === agent.id ? 'border-lia-btn-primary-bg dark:border-lia-border-subtle' : 'border-lia-border-subtle dark:border-lia-border-subtle'}`}
            >
              <CardContent className="p-4">
                {/* Header */}
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-2.5">
                    <span className="text-xl">{agent.icon}</span>
                    <div>
                      <h3 className="font-medium text-sm leading-tight font-sans text-lia-text-primary">
                        {agent.name}
                      </h3>
                    </div>
                  </div>
                  <div className="flex items-center gap-1">
                    <span 
                      className="w-2 h-2 rounded-full"
                      style={{backgroundColor: getStatusColor(agent.status)}}
                    />
                    <ChevronRight
                      className="w-4 h-4 opacity-0 group-hover:opacity-100 transition-opacity motion-reduce:transition-none text-lia-text-muted"
                    />
                  </div>
                </div>

                {/* Sparkline */}
                <div className="mb-3 h-8">
                  <Sparkline data={agent.sparkline} color="var(--lia-text-secondary)" />
                </div>

                {/* Metrics Row */}
                <div className="grid grid-cols-2 gap-2 mb-3">
                  <div className="p-2 rounded-xl bg-lia-bg-tertiary dark:bg-lia-bg-secondary">
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-lia-text-muted">
                        Ações 24h
                      </span>
                      <CompactDelta value={agent.delta} />
                    </div>
                    <div className="flex items-baseline gap-1">
                      <span className="text-lg font-semibold text-lia-text-primary">{agent.actions_today}</span>
                      <span className="text-xs text-lia-text-muted">
                        /{agent.daily_goal}
                      </span>
                    </div>
                    {/* Progress bar */}
                    <div className="mt-1 h-1 rounded-full overflow-hidden bg-lia-interactive-active dark:bg-lia-bg-elevated">
                      <div 
                        className="h-full rounded-full transition-[width,height] bg-lia-btn-primary-bg" style={{width: `${Math.min(agent.progress, 100)}%`}}
                      />
                    </div>
                  </div>
                  <div className="p-2 rounded-xl bg-lia-bg-tertiary dark:bg-lia-bg-secondary">
                    <span className="text-xs block text-lia-text-muted">
                      Progresso
                    </span>
                    <span 
                      className={`text-lg font-semibold ${agent.progress >= 80 ? 'text-wedo-green-text-bright' : agent.progress >= 50 ? 'text-lia-btn-primary-bg' : 'text-status-warning'}`}
                    >
                      {agent.progress}%
                    </span>
                  </div>
                </div>

                {/* Last Activity */}
                <div className="pt-2 border-t border-lia-border-subtle dark:border-lia-border-subtle">
                  <p className="text-xs truncate text-lia-text-tertiary">
                    {agent.last_action || 'Sem atividade recente'}
                  </p>
                  <p className="text-xs text-lia-text-muted">
                    {formatTimeAgo(agent.last_action_time)}
                  </p>
                </div>

                {/* Warning for warning status */}
                {agent.status === 'warning' && (
                  <div 
                    className="mt-2 p-2 rounded-md flex items-center gap-2 bg-status-error/10"
                  >
                    <AlertTriangle className="w-3 h-3 flex-shrink-0" />
                    <span className="text-xs line-clamp-1 text-lia-text-tertiary">
                      Requer atenção
                    </span>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Activity Feed Section */}
        <div className="rounded-xl border bg-lia-bg-primary border-lia-border-subtle dark:border-lia-border-subtle">
          {/* Feed Header with Filters */}
          <div className="p-4 dark:border-lia-border-subtle">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Activity className="w-5 h-5 text-lia-text-secondary" />
                <h3 className="font-medium font-sans text-lia-text-primary">
                  Atividade Recente
                </h3>
                <Chip density="relaxed" variant="neutral" className="border-lia-border-default dark:border-lia-border-default">
                  {activities.length} eventos
                </Chip>
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  className={`text-xs ${filterPeriod === 'today' ? 'bg-lia-interactive-active' : 'text-lia-text-tertiary'}`}
                  onClick={() => setFilterPeriod('today')}
                >
                  Hoje
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className={`text-xs ${filterPeriod === 'week' ? 'bg-lia-interactive-active' : 'text-lia-text-tertiary'}`}
                  onClick={() => setFilterPeriod('week')}
                >
                  Semana
                </Button>
              </div>
            </div>

            {/* Filter Pills */}
            <div className="flex flex-wrap items-center gap-2">
              <Filter className="w-3.5 h-3.5 text-lia-text-muted" />
              
              {/* Agent Filters */}
              <div className="flex flex-wrap gap-1">
                {agents.slice(0, 4).map(agent => (
                  <button
                    key={agent.id}
                    onClick={() => toggleAgentFilter(agent.id)}
                    className={`px-2 py-1 rounded-full text-xs transition-[width,height] ${selectedAgentFilter.includes(agent.id) ? 'bg-wedo-cyan-bg-15 border border-lia-btn-primary-bg' : 'bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-tertiary border border-transparent'}`}
                  >
                    {agent.icon} {agent.name.split(' ')[0]}
                  </button>
                ))}
              </div>

              {/* Status Filters */}
              <div className="flex gap-1 ml-2">
                {['success', 'in_progress', 'error'].map(status => (
                  <button
                    key={status}
                    onClick={() => toggleStatusFilter(status)}
                    className={`px-2 py-1 rounded-full text-xs transition-[width,height] flex items-center gap-1 ${!selectedStatusFilter.includes(status) ? 'bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-tertiary' : ''}`}
                    style={{backgroundColor: selectedStatusFilter.includes(status) ?
                        (status === 'success' ? 'var(--wedo-green-active-15)' : status === 'error' ? 'var(--status-error-bg-15)' : 'var(--status-warning-bg-15)') :
                        undefined,
                      color: selectedStatusFilter.includes(status) ?
                        (status === 'success' ? 'var(--wedo-green-bright)' : status === 'error' ? 'var(--status-error)' : 'var(--status-warning)') :
                        undefined,
                      border: `1px solid ${selectedStatusFilter.includes(status) ?
                        (status === 'success' ? 'var(--wedo-green-bright)' : status === 'error' ? 'var(--status-error)' : 'var(--status-warning)') : 'transparent'}`}}
                  >
                    {status === 'success' && <CheckCircle className="w-2.5 h-2.5" />}
                    {status === 'in_progress' && <Clock className="w-2.5 h-2.5" />}
                    {status === 'error' && <XCircle className="w-2.5 h-2.5" />}
                    {status === 'success' ? 'Sucesso' : status === 'in_progress' ? 'Em andamento' : 'Erro'}
                  </button>
                ))}
              </div>

              {/* Clear Filters */}
              {(selectedAgentFilter.length > 0 || selectedStatusFilter.length > 0) && (
                <button
                  onClick={clearFilters}
                  className="px-2 py-1 rounded-full text-xs flex items-center gap-1 text-lia-text-muted"
                >
                  <X className="w-3 h-3" />
                  Limpar
                </button>
              )}
            </div>
          </div>

          {/* Activity List */}
          <div className="max-h-content-lg overflow-y-auto">
            {activities.length === 0 ? (
              <div className="p-8 text-center text-lia-text-disabled">
                Nenhuma atividade encontrada com os filtros selecionados
              </div>
            ) : (
              <div className="divide-y divide-lia-border-subtle dark:divide-lia-border-strong">
                {activities.map((activity) => (
                  <div 
                    key={activity.id}
                    className="flex items-start gap-3 p-4 transition-colors motion-reduce:transition-none hover:bg-opacity-50"
                   
                  >
                    <div className="flex-shrink-0 mt-0.5">
                      <span className="text-lg">{activity.agent_icon}</span>
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-xs font-medium text-lia-text-secondary">
                          {activity.agent_name}
                        </span>
                        <span className="text-xs text-lia-text-muted">
                          {formatTimeAgo(activity.started_at)}
                        </span>
                        {activity.sla_breach && (
                          <Chip density="relaxed" variant="neutral" className="px-1 py-0">
                            SLA
                          </Chip>
                        )}
                      </div>
                      <p className="text-sm font-medium text-lia-text-primary">
                        {activity.title}
                      </p>
                      <p className="text-xs text-lia-text-tertiary">
                        {activity.description}
                      </p>
                    </div>
                    <div className="flex-shrink-0">
                      {activity.status === 'success' && (
                        <CheckCircle className="w-4 h-4 text-wedo-green-bright" />
                      )}
                      {activity.status === 'in_progress' && (
                        <Clock className="w-4 h-4" />
                      )}
                      {activity.status === 'error' && (
                        <XCircle className="w-4 h-4" />
                      )}
                      {activity.status === 'pending' && (
                        <Clock className="w-4 h-4 text-lia-text-secondary" />
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Agent Detail Panel */}
      <AgentDetailPanel
        agent={selectedAgent}
        isOpen={isDetailPanelOpen}
        onClose={() => {
          setIsDetailPanelOpen(false)
          setSelectedAgent(null)
        }}
      />
    </div>
  )
}

