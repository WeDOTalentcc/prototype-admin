"use client"

import React, { useState, useEffect, useCallback } from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { 
  Activity, RefreshCcw, CheckCircle, Clock, XCircle, 
  TrendingUp, TrendingDown, Minus, AlertTriangle, ChevronRight,
  Filter, X, Brain, Zap, Target, Users
} from 'lucide-react'
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
      case 'online': return 'var(--gray-600)'
      case 'idle': return 'var(--status-warning)'
      case 'warning': return 'var(--status-error)'
      default: return 'var(--gray-400)'
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
        <div className="flex items-center gap-2 text-gray-500 dark:text-gray-400">
          <RefreshCcw className="w-5 h-5 animate-spin" />
          <span>Carregando Centro de Controle...</span>
        </div>
      </div>
    )
  }

  return (
    <div className={`flex-1 overflow-y-auto p-6 bg-gray-50 dark:bg-gray-900 ${className}`}>
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold mb-1 flex items-center gap-2 text-gray-800 dark:text-gray-100">
              <Brain className="w-5 h-5 text-wedo-cyan" />
              Centro de Controle IA
            </h2>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Monitore seus agentes especializados em tempo real
            </p>
          </div>
          <div className="flex items-center gap-3">
            {lastUpdated && (
              <span className="text-xs text-gray-400 dark:text-gray-500">
                Atualizado {formatTimeAgo(lastUpdated.toISOString())}
              </span>
            )}
            <Button
              variant="outline"
              size="sm"
              onClick={fetchData}
              disabled={isLoading}
              className="text-xs border-gray-300 dark:border-gray-600"
            >
              <RefreshCcw className={`w-3 h-3 mr-1 ${isLoading ? 'animate-spin' : ''}`} />
              Atualizar
            </Button>
          </div>
        </div>

        {/* Global Metrics Bar */}
        <div className="grid grid-cols-5 gap-3 mb-6">
          <MetricCard
            icon={<Zap className="w-4 h-4" />}
            label="Ações Hoje"
            value={globalMetrics.actions_today}
            delta={globalMetrics.actions_delta}
            color="var(--gray-600)"
          />
          <MetricCard
            icon={<Users className="w-4 h-4" />}
            label="Agentes Ativos"
            value={`${globalMetrics.active_agents}/${globalMetrics.total_agents}`}
            color="var(--gray-600)"
          />
          <MetricCard
            icon={<Target className="w-4 h-4" />}
            label="Taxa de Sucesso"
            value={`${globalMetrics.success_rate.toFixed(1)}%`}
            color="var(--wedo-green-bright)"
          />
          <MetricCard
            icon={<Clock className="w-4 h-4" />}
            label="Tempo Médio"
            value={`${globalMetrics.avg_response_time}s`}
            color="var(--gray-600)"
          />
          <MetricCard
            icon={<AlertTriangle className="w-4 h-4" />}
            label="Alertas"
            value={globalMetrics.proactive_alerts}
            color={globalMetrics.proactive_alerts > 0 ? 'var(--status-warning)' : 'var(--wedo-green-bright)'}
          />
        </div>

        {/* Proactive Alerts */}
        {proactiveAlerts.length > 0 && (
          <div className="mb-6 p-4 rounded-md border bg-status-warning/5 border-status-warning/30">
            <div className="flex items-center gap-2 mb-3">
              <AlertTriangle className="w-4 h-4 text-status-warning" />
              <span className="text-sm font-medium text-gray-800 dark:text-gray-100">
                Atenção Necessária
              </span>
            </div>
            <div className="space-y-2">
              {proactiveAlerts.map(alert => (
                <div
                  key={alert.id}
                  className="flex items-center justify-between p-3 rounded-md bg-white dark:bg-gray-950"
                >
                  <div className="flex items-center gap-3">
                    <Badge
                      variant="outline"
                      className="text-xs"
                      style={{borderColor: alert.severity === 'high' ? 'var(--status-error)' :
                                    alert.severity === 'medium' ? 'var(--status-warning)' : 'var(--gray-600)',
                        color: alert.severity === 'high' ? 'var(--status-error)' :
                               alert.severity === 'medium' ? 'var(--status-warning)' : 'var(--gray-600)'}}
                    >
                      {alert.severity}
                    </Badge>
                    <div>
                      <p className="text-sm font-medium text-gray-800 dark:text-gray-100">
                        {alert.title}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
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
              className={`border transition-all duration-200 hover:scale-[1.02] hover:cursor-pointer group bg-white dark:bg-gray-950 ${selectedAgent?.id === agent.id ? 'border-gray-900 dark:border-gray-100' : 'border-gray-200 dark:border-gray-700'}`}
            >
              <CardContent className="p-4">
                {/* Header */}
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-2.5">
                    <span className="text-xl">{agent.icon}</span>
                    <div>
                      <h3 className="font-medium text-sm leading-tight font-sans text-gray-800 dark:text-gray-100">
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
                      className="w-4 h-4 opacity-0 group-hover:opacity-100 transition-opacity text-gray-400 dark:text-gray-500"
                    />
                  </div>
                </div>

                {/* Sparkline */}
                <div className="mb-3 h-8">
                  <Sparkline data={agent.sparkline} color="var(--gray-600)" />
                </div>

                {/* Metrics Row */}
                <div className="grid grid-cols-2 gap-2 mb-3">
                  <div className="p-2 rounded-md bg-gray-100 dark:bg-gray-800">
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-gray-400 dark:text-gray-500">
                        Ações 24h
                      </span>
                      <DeltaIndicator value={agent.delta} />
                    </div>
                    <div className="flex items-baseline gap-1">
                      <span className="text-lg font-bold text-gray-900 dark:text-gray-50">{agent.actions_today}</span>
                      <span className="text-xs text-gray-400 dark:text-gray-500">
                        /{agent.daily_goal}
                      </span>
                    </div>
                    {/* Progress bar */}
                    <div className="mt-1 h-1 rounded-full overflow-hidden bg-gray-200 dark:bg-gray-700">
                      <div 
                        className="h-full rounded-full transition-all bg-gray-900" style={{width: `${Math.min(agent.progress, 100)}%`}}
                      />
                    </div>
                  </div>
                  <div className="p-2 rounded-md bg-gray-100 dark:bg-gray-800">
                    <span className="text-xs block text-gray-400 dark:text-gray-500">
                      Progresso
                    </span>
                    <span 
                      className="text-lg font-bold"
                      style={{color: agent.progress >= 80 ? 'var(--wedo-green-bright)' : agent.progress >= 50 ? 'var(--gray-950)' : 'var(--status-warning)'}}
                    >
                      {agent.progress}%
                    </span>
                  </div>
                </div>

                {/* Last Activity */}
                <div className="pt-2 border-t border-gray-200 dark:border-gray-700">
                  <p className="text-xs truncate text-gray-500 dark:text-gray-400">
                    {agent.last_action || 'Sem atividade recente'}
                  </p>
                  <p className="text-xs text-gray-400 dark:text-gray-500">
                    {formatTimeAgo(agent.last_action_time)}
                  </p>
                </div>

                {/* Warning for warning status */}
                {agent.status === 'warning' && (
                  <div 
                    className="mt-2 p-2 rounded-md flex items-center gap-2 bg-status-error/10"
                  >
                    <AlertTriangle className="w-3 h-3 flex-shrink-0" style={{color: 'var(--status-error)'}} />
                    <span className="text-xs line-clamp-1 text-gray-500 dark:text-gray-400">
                      Requer atenção
                    </span>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Activity Feed Section */}
        <div className="rounded-md border bg-white dark:bg-gray-950 border-gray-200 dark:border-gray-700">
          {/* Feed Header with Filters */}
          <div className="p-4 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Activity className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                <h3 className="font-medium font-sans text-gray-800 dark:text-gray-100">
                  Atividade Recente
                </h3>
                <Badge variant="outline" className="text-xs border-gray-300 dark:border-gray-600">
                  {activities.length} eventos
                </Badge>
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  className={`text-xs ${filterPeriod === 'today' ? '' : 'text-gray-500 dark:text-gray-400'}`}
                  onClick={() => setFilterPeriod('today')}
                  style={{backgroundColor: filterPeriod === 'today' ? 'var(--gray-bg-30)' : 'transparent'}}
                >
                  Hoje
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className={`text-xs ${filterPeriod === 'week' ? '' : 'text-gray-500 dark:text-gray-400'}`}
                  onClick={() => setFilterPeriod('week')}
                  style={{backgroundColor: filterPeriod === 'week' ? 'var(--gray-bg-30)' : 'transparent'}}
                >
                  Semana
                </Button>
              </div>
            </div>

            {/* Filter Pills */}
            <div className="flex flex-wrap items-center gap-2">
              <Filter className="w-3.5 h-3.5 text-gray-400 dark:text-gray-500" />
              
              {/* Agent Filters */}
              <div className="flex flex-wrap gap-1">
                {agents.slice(0, 4).map(agent => (
                  <button
                    key={agent.id}
                    onClick={() => toggleAgentFilter(agent.id)}
                    className={`px-2 py-1 rounded-full text-xs transition-all ${selectedAgentFilter.includes(agent.id) ? '' : 'bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400'}`}
                    style={{backgroundColor: selectedAgentFilter.includes(agent.id) ? 'var(--wedo-cyan-bg-15)' : undefined,
                      border: `1px solid ${selectedAgentFilter.includes(agent.id) ? 'var(--gray-950)' : 'transparent'}`}}
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
                    className={`px-2 py-1 rounded-full text-xs transition-all flex items-center gap-1 ${!selectedStatusFilter.includes(status) ? 'bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400' : ''}`}
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
                  className="px-2 py-1 rounded-full text-xs flex items-center gap-1 text-gray-400 dark:text-gray-500"
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
              <div className="p-8 text-center text-gray-400 dark:text-gray-500">
                Nenhuma atividade encontrada com os filtros selecionados
              </div>
            ) : (
              <div className="divide-y divide-gray-200 dark:divide-gray-700">
                {activities.map((activity) => (
                  <div 
                    key={activity.id}
                    className="flex items-start gap-3 p-4 transition-colors hover:bg-opacity-50"
                    style={{backgroundColor: 'transparent'}}
                  >
                    <div className="flex-shrink-0 mt-0.5">
                      <span className="text-lg">{activity.agent_icon}</span>
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-xs font-medium text-gray-600 dark:text-gray-400">
                          {activity.agent_name}
                        </span>
                        <span className="text-xs text-gray-400 dark:text-gray-500">
                          {formatTimeAgo(activity.started_at)}
                        </span>
                        {activity.sla_breach && (
                          <Badge variant="outline" className="text-xs px-1 py-0" style={{borderColor: 'var(--status-error)', color: 'var(--status-error)'}}>
                            SLA
                          </Badge>
                        )}
                      </div>
                      <p className="text-sm font-medium text-gray-800 dark:text-gray-100">
                        {activity.title}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        {activity.description}
                      </p>
                    </div>
                    <div className="flex-shrink-0">
                      {activity.status === 'success' && (
                        <CheckCircle className="w-4 h-4 text-wedo-green-bright" />
                      )}
                      {activity.status === 'in_progress' && (
                        <Clock className="w-4 h-4" style={{color: 'var(--status-warning)'}} />
                      )}
                      {activity.status === 'error' && (
                        <XCircle className="w-4 h-4" style={{color: 'var(--status-error)'}} />
                      )}
                      {activity.status === 'pending' && (
                        <Clock className="w-4 h-4 text-gray-400" />
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

function DeltaIndicator({ value }: { value: number }) {
  if (value === 0) {
    return (
      <div className="flex items-center gap-0.5 text-xs text-gray-400 dark:text-gray-500">
        <Minus className="w-2.5 h-2.5" />
        <span>0%</span>
      </div>
    )
  }
  
  if (value > 0) {
    return (
      <div className="flex items-center gap-0.5 text-xs text-wedo-green-bright">
        <TrendingUp className="w-2.5 h-2.5" />
        <span>+{value}%</span>
      </div>
    )
  }
  
  return (
    <div className="flex items-center gap-0.5 text-xs" style={{color: 'var(--status-error)'}}>
      <TrendingDown className="w-2.5 h-2.5" />
      <span>{value}%</span>
    </div>
  )
}

function MetricCard({ 
  icon, 
  label, 
  value, 
  delta, 
  color 
}: { 
  icon: React.ReactNode
  label: string
  value: number | string
  delta?: number
  color: string
}) {
  return (
    <div
      className="p-3 rounded-md border bg-white dark:bg-gray-950 border-gray-200 dark:border-gray-700"
    >
      <div className="flex items-center gap-2 mb-1.5">
        <div style={{color}}>{icon}</div>
        <span className="text-xs text-gray-400 dark:text-gray-500">{label}</span>
      </div>
      <div className="flex items-baseline gap-2">
        <span className="text-xl font-bold" style={{color}}>{value}</span>
        {delta !== undefined && (
          <DeltaIndicator value={delta} />
        )}
      </div>
    </div>
  )
}
