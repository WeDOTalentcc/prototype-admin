"use client"

import React, { useState, useEffect, useCallback } from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
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
        <span className="text-xs text-lia-text-disabled">{title}</span>
      </div>
      <div className="flex items-baseline gap-2">
        <span className="text-lg font-bold text-lia-text-primary">{value}</span>
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

export function AgentControlCenter({ className }: AgentControlCenterProps) {
  const [globalMetrics, setGlobalMetrics] = useState<GlobalMetrics | null>(null)
  const [agents, setAgents] = useState<AgentSummary[]>([])
  const [activities, setActivities] = useState<ActivityEvent[]>([])
  const [proactiveAlerts, setProactiveAlerts] = useState<ProactiveAlert[]>([])
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
    const interval = setInterval(fetchData, 30000)
    return () => clearInterval(interval)
  }, [fetchData])

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
              <span className="text-xs text-lia-text-disabled">
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
                    <Badge
                      variant="outline"
                      className={`text-xs ${alert.severity === 'high' ? 'border-status-error text-status-error' : alert.severity === 'medium' ? 'border-status-warning text-status-warning' : 'border-lia-text-secondary text-lia-text-secondary'}`}
                    >
                      {alert.severity}
                    </Badge>
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
                      className="w-4 h-4 opacity-0 group-hover:opacity-100 transition-opacity motion-reduce:transition-none text-lia-text-disabled"
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
                      <span className="text-xs text-lia-text-disabled">
                        Ações 24h
                      </span>
                      <CompactDelta value={agent.delta} />
                    </div>
                    <div className="flex items-baseline gap-1">
                      <span className="text-lg font-bold text-lia-text-primary">{agent.actions_today}</span>
                      <span className="text-xs text-lia-text-disabled">
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
                    <span className="text-xs block text-lia-text-disabled">
                      Progresso
                    </span>
                    <span 
                      className={`text-lg font-bold ${agent.progress >= 80 ? 'text-wedo-green-bright' : agent.progress >= 50 ? 'text-lia-btn-primary-bg' : 'text-status-warning'}`}
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
                  <p className="text-xs text-lia-text-disabled">
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
                <Badge variant="outline" className="text-xs border-lia-border-default dark:border-lia-border-default">
                  {activities.length} eventos
                </Badge>
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
              <Filter className="w-3.5 h-3.5 text-lia-text-disabled" />
              
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
                  className="px-2 py-1 rounded-full text-xs flex items-center gap-1 text-lia-text-disabled"
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
                        <span className="text-xs text-lia-text-disabled">
                          {formatTimeAgo(activity.started_at)}
                        </span>
                        {activity.sla_breach && (
                          <Badge variant="outline" className="text-xs px-1 py-0">
                            SLA
                          </Badge>
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

