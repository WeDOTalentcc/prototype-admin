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
      console.error('Error fetching agent data:', error)
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
      case 'online': return '#374151'
      case 'idle': return '#F59E0B'
      case 'warning': return '#EF4444'
      default: return '#9CA3AF'
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
        <div className="flex items-center gap-2" style={{ color: 'var(--eleven-text-secondary)' }}>
          <RefreshCcw className="w-5 h-5 animate-spin" />
          <span>Carregando Centro de Controle...</span>
        </div>
      </div>
    )
  }

  return (
    <div className={`flex-1 overflow-y-auto p-6 ${className}`} style={{ backgroundColor: 'var(--eleven-bg-main)' }}>
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold mb-1 flex items-center gap-2" style={{ color: 'var(--eleven-text-primary)' }}>
              <Brain className="w-5 h-5 text-wedo-cyan" />
              Centro de Controle IA
            </h2>
            <p className="text-sm" style={{ color: 'var(--eleven-text-secondary)' }}>
              Monitore seus agentes especializados em tempo real
            </p>
          </div>
          <div className="flex items-center gap-3">
            {lastUpdated && (
              <span className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>
                Atualizado {formatTimeAgo(lastUpdated.toISOString())}
              </span>
            )}
            <Button
              variant="outline"
              size="sm"
              onClick={fetchData}
              disabled={isLoading}
              className="text-xs"
              style={{ borderColor: 'var(--eleven-border)' }}
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
            color="#374151"
          />
          <MetricCard
            icon={<Users className="w-4 h-4" />}
            label="Agentes Ativos"
            value={`${globalMetrics.active_agents}/${globalMetrics.total_agents}`}
            color="#374151"
          />
          <MetricCard
            icon={<Target className="w-4 h-4" />}
            label="Taxa de Sucesso"
            value={`${globalMetrics.success_rate.toFixed(1)}%`}
            color="#60D186"
          />
          <MetricCard
            icon={<Clock className="w-4 h-4" />}
            label="Tempo Médio"
            value={`${globalMetrics.avg_response_time}s`}
            color="#374151"
          />
          <MetricCard
            icon={<AlertTriangle className="w-4 h-4" />}
            label="Alertas"
            value={globalMetrics.proactive_alerts}
            color={globalMetrics.proactive_alerts > 0 ? '#F59E0B' : '#60D186'}
          />
        </div>

        {/* Proactive Alerts */}
        {proactiveAlerts.length > 0 && (
          <div className="mb-6 p-4 rounded-md border" style={{ 
            backgroundColor: 'rgba(245, 158, 11, 0.05)', 
            borderColor: 'rgba(245, 158, 11, 0.3)' 
          }}>
            <div className="flex items-center gap-2 mb-3">
              <AlertTriangle className="w-4 h-4 text-amber-500" />
              <span className="text-sm font-medium" style={{ color: 'var(--eleven-text-primary)' }}>
                Atenção Necessária
              </span>
            </div>
            <div className="space-y-2">
              {proactiveAlerts.map(alert => (
                <div 
                  key={alert.id}
                  className="flex items-center justify-between p-3 rounded-md"
                  style={{ backgroundColor: 'var(--eleven-bg-card)' }}
                >
                  <div className="flex items-center gap-3">
                    <Badge 
                      variant="outline" 
                      className="text-xs"
                      style={{ 
                        borderColor: alert.severity === 'high' ? '#EF4444' : 
                                    alert.severity === 'medium' ? '#F59E0B' : '#374151',
                        color: alert.severity === 'high' ? '#EF4444' : 
                               alert.severity === 'medium' ? '#F59E0B' : '#374151'
                      }}
                    >
                      {alert.severity}
                    </Badge>
                    <div>
                      <p className="text-sm font-medium" style={{ color: 'var(--eleven-text-primary)' }}>
                        {alert.title}
                      </p>
                      <p className="text-xs" style={{ color: 'var(--eleven-text-secondary)' }}>
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
              className="border transition-all duration-200 hover:scale-[1.02] hover:cursor-pointer group"
              style={{ 
                backgroundColor: 'var(--eleven-bg-card)',
                borderColor: selectedAgent?.id === agent.id ? '#111827' : 'var(--eleven-border-subtle)'
              }}
            >
              <CardContent className="p-4">
                {/* Header */}
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-2.5">
                    <span className="text-xl">{agent.icon}</span>
                    <div>
                      <h3 className="font-medium text-sm leading-tight font-sans" style={{ color: 'var(--eleven-text-primary)' }}>
                        {agent.name}
                      </h3>
                    </div>
                  </div>
                  <div className="flex items-center gap-1">
                    <span 
                      className="w-2 h-2 rounded-full"
                      style={{ backgroundColor: getStatusColor(agent.status) }}
                    />
                    <ChevronRight 
                      className="w-4 h-4 opacity-0 group-hover:opacity-100 transition-opacity" 
                      style={{ color: 'var(--eleven-text-tertiary)' }}
                    />
                  </div>
                </div>

                {/* Sparkline */}
                <div className="mb-3 h-8">
                  <Sparkline data={agent.sparkline} color="#374151" />
                </div>

                {/* Metrics Row */}
                <div className="grid grid-cols-2 gap-2 mb-3">
                  <div className="p-2 rounded-md" style={{ backgroundColor: 'var(--eleven-bg-message)' }}>
                    <div className="flex items-center justify-between">
                      <span className="text-[11px]" style={{ color: 'var(--eleven-text-tertiary)' }}>
                        Ações 24h
                      </span>
                      <DeltaIndicator value={agent.delta} />
                    </div>
                    <div className="flex items-baseline gap-1">
                      <span className="text-lg font-bold text-gray-900 dark:text-gray-50">{agent.actions_today}</span>
                      <span className="text-[11px]" style={{ color: 'var(--eleven-text-tertiary)' }}>
                        /{agent.daily_goal}
                      </span>
                    </div>
                    {/* Progress bar */}
                    <div className="mt-1 h-1 rounded-full overflow-hidden" style={{ backgroundColor: 'var(--eleven-border-subtle)' }}>
                      <div 
                        className="h-full rounded-full transition-all bg-gray-900" style={{ width: `${Math.min(agent.progress, 100)}%` }}
                      />
                    </div>
                  </div>
                  <div className="p-2 rounded-md" style={{ backgroundColor: 'var(--eleven-bg-message)' }}>
                    <span className="text-[11px] block" style={{ color: 'var(--eleven-text-tertiary)' }}>
                      Progresso
                    </span>
                    <span 
                      className="text-lg font-bold"
                      style={{ color: agent.progress >= 80 ? '#60D186' : agent.progress >= 50 ? '#111827' : '#F59E0B' }}
                    >
                      {agent.progress}%
                    </span>
                  </div>
                </div>

                {/* Last Activity */}
                <div className="pt-2 border-t" style={{ borderColor: 'var(--eleven-border-subtle)' }}>
                  <p className="text-[11px] truncate" style={{ color: 'var(--eleven-text-secondary)' }}>
                    {agent.last_action || 'Sem atividade recente'}
                  </p>
                  <p className="text-[11px]" style={{ color: 'var(--eleven-text-tertiary)' }}>
                    {formatTimeAgo(agent.last_action_time)}
                  </p>
                </div>

                {/* Warning for warning status */}
                {agent.status === 'warning' && (
                  <div 
                    className="mt-2 p-2 rounded-md flex items-center gap-2"
                    style={{ backgroundColor: 'rgba(239, 68, 68, 0.1)' }}
                  >
                    <AlertTriangle className="w-3 h-3 flex-shrink-0" style={{ color: '#EF4444' }} />
                    <span className="text-[11px] line-clamp-1" style={{ color: 'var(--eleven-text-secondary)' }}>
                      Requer atenção
                    </span>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Activity Feed Section */}
        <div className="rounded-md border" style={{ backgroundColor: 'var(--eleven-bg-card)', borderColor: 'var(--eleven-border-subtle)' }}>
          {/* Feed Header with Filters */}
          <div className="p-4 border-b" style={{ borderColor: 'var(--eleven-border-subtle)' }}>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Activity className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                <h3 className="font-medium font-sans" style={{ color: 'var(--eleven-text-primary)' }}>
                  Atividade Recente
                </h3>
                <Badge variant="outline" className="text-xs" style={{ borderColor: 'var(--eleven-border)' }}>
                  {activities.length} eventos
                </Badge>
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-xs"
                  onClick={() => setFilterPeriod('today')}
                  style={{ 
                    color: filterPeriod === 'today' ? '#111827' : 'var(--eleven-text-secondary)',
                    backgroundColor: filterPeriod === 'today' ? 'rgba(229, 231, 235, 0.3)' : 'transparent'
                  }}
                >
                  Hoje
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-xs"
                  onClick={() => setFilterPeriod('week')}
                  style={{ 
                    color: filterPeriod === 'week' ? '#111827' : 'var(--eleven-text-secondary)',
                    backgroundColor: filterPeriod === 'week' ? 'rgba(229, 231, 235, 0.3)' : 'transparent'
                  }}
                >
                  Semana
                </Button>
              </div>
            </div>

            {/* Filter Pills */}
            <div className="flex flex-wrap items-center gap-2">
              <Filter className="w-3.5 h-3.5" style={{ color: 'var(--eleven-text-tertiary)' }} />
              
              {/* Agent Filters */}
              <div className="flex flex-wrap gap-1">
                {agents.slice(0, 4).map(agent => (
                  <button
                    key={agent.id}
                    onClick={() => toggleAgentFilter(agent.id)}
                    className="px-2 py-1 rounded-full text-[11px] transition-all"
                    style={{
                      backgroundColor: selectedAgentFilter.includes(agent.id) ? 'rgba(96, 190, 209, 0.15)' : 'var(--eleven-bg-message)',
                      color: selectedAgentFilter.includes(agent.id) ? '#111827' : 'var(--eleven-text-secondary)',
                      border: `1px solid ${selectedAgentFilter.includes(agent.id) ? '#111827' : 'transparent'}`
                    }}
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
                    className="px-2 py-1 rounded-full text-[11px] transition-all flex items-center gap-1"
                    style={{
                      backgroundColor: selectedStatusFilter.includes(status) ? 
                        (status === 'success' ? 'rgba(96, 209, 134, 0.15)' : status === 'error' ? 'rgba(239, 68, 68, 0.15)' : 'rgba(245, 158, 11, 0.15)') : 
                        'var(--eleven-bg-message)',
                      color: selectedStatusFilter.includes(status) ? 
                        (status === 'success' ? '#60D186' : status === 'error' ? '#EF4444' : '#F59E0B') : 
                        'var(--eleven-text-secondary)',
                      border: `1px solid ${selectedStatusFilter.includes(status) ? 
                        (status === 'success' ? '#60D186' : status === 'error' ? '#EF4444' : '#F59E0B') : 'transparent'}`
                    }}
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
                  className="px-2 py-1 rounded-full text-[11px] flex items-center gap-1"
                  style={{ color: 'var(--eleven-text-tertiary)' }}
                >
                  <X className="w-3 h-3" />
                  Limpar
                </button>
              )}
            </div>
          </div>

          {/* Activity List */}
          <div className="max-h-[400px] overflow-y-auto">
            {activities.length === 0 ? (
              <div className="p-8 text-center" style={{ color: 'var(--eleven-text-tertiary)' }}>
                Nenhuma atividade encontrada com os filtros selecionados
              </div>
            ) : (
              <div className="divide-y" style={{ borderColor: 'var(--eleven-border-subtle)' }}>
                {activities.map((activity) => (
                  <div 
                    key={activity.id}
                    className="flex items-start gap-3 p-4 transition-colors hover:bg-opacity-50"
                    style={{ backgroundColor: 'transparent' }}
                  >
                    <div className="flex-shrink-0 mt-0.5">
                      <span className="text-lg">{activity.agent_icon}</span>
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-xs font-medium text-gray-600 dark:text-gray-400">
                          {activity.agent_name}
                        </span>
                        <span className="text-[11px]" style={{ color: 'var(--eleven-text-tertiary)' }}>
                          {formatTimeAgo(activity.started_at)}
                        </span>
                        {activity.sla_breach && (
                          <Badge variant="outline" className="text-[11px] px-1 py-0" style={{ borderColor: '#EF4444', color: '#EF4444' }}>
                            SLA
                          </Badge>
                        )}
                      </div>
                      <p className="text-sm font-medium" style={{ color: 'var(--eleven-text-primary)' }}>
                        {activity.title}
                      </p>
                      <p className="text-xs" style={{ color: 'var(--eleven-text-secondary)' }}>
                        {activity.description}
                      </p>
                    </div>
                    <div className="flex-shrink-0">
                      {activity.status === 'success' && (
                        <CheckCircle className="w-4 h-4 text-wedo-green-bright" />
                      )}
                      {activity.status === 'in_progress' && (
                        <Clock className="w-4 h-4" style={{ color: '#F59E0B' }} />
                      )}
                      {activity.status === 'error' && (
                        <XCircle className="w-4 h-4" style={{ color: '#EF4444' }} />
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
      <div className="flex items-center gap-0.5 text-[11px]" style={{ color: 'var(--eleven-text-tertiary)' }}>
        <Minus className="w-2.5 h-2.5" />
        <span>0%</span>
      </div>
    )
  }
  
  if (value > 0) {
    return (
      <div className="flex items-center gap-0.5 text-[11px] text-wedo-green-bright">
        <TrendingUp className="w-2.5 h-2.5" />
        <span>+{value}%</span>
      </div>
    )
  }
  
  return (
    <div className="flex items-center gap-0.5 text-[11px]" style={{ color: '#EF4444' }}>
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
      className="p-3 rounded-md border"
      style={{ backgroundColor: 'var(--eleven-bg-card)', borderColor: 'var(--eleven-border-subtle)' }}
    >
      <div className="flex items-center gap-2 mb-1.5">
        <div style={{ color }}>{icon}</div>
        <span className="text-[11px]" style={{ color: 'var(--eleven-text-tertiary)' }}>{label}</span>
      </div>
      <div className="flex items-baseline gap-2">
        <span className="text-xl font-bold" style={{ color }}>{value}</span>
        {delta !== undefined && (
          <DeltaIndicator value={delta} />
        )}
      </div>
    </div>
  )
}
