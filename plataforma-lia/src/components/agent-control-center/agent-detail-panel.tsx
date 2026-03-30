"use client"

import React, { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { 
  X, CheckCircle, Clock, XCircle, TrendingUp, TrendingDown, Minus,
  Activity, Settings, Target,
  ChevronRight, Lightbulb
} from 'lucide-react'
import { 
  agentMonitoringService, 
  AgentSummary, 
  ActivityEvent, 
  AgentHealth 
} from '@/services/agent-monitoring'
import { Sparkline } from './sparkline'

interface AgentDetailPanelProps {
  agent: AgentSummary | null
  isOpen: boolean
  onClose: () => void
}

export function AgentDetailPanel({ agent, isOpen, onClose }: AgentDetailPanelProps) {
  const [activities, setActivities] = useState<ActivityEvent[]>([])
  const [healthScore, setHealthScore] = useState<AgentHealth | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [activeTab, setActiveTab] = useState<'activity' | 'health' | 'settings'>('activity')

  useEffect(() => {
    if (agent && isOpen) {
      fetchAgentDetails()
    }
  }, [agent, isOpen])

  const fetchAgentDetails = async () => {
    if (!agent) return
    setIsLoading(true)
    try {
      const [activityData, healthData] = await Promise.all([
        agentMonitoringService.getAgentActivities(agent.id, 30),
        agentMonitoringService.getAgentHealth(agent.id)
      ])
      setActivities(activityData)
      setHealthScore(healthData)
    } catch (error) {
    } finally {
      setIsLoading(false)
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

  const getHealthTierLabel = (tier: string) => {
    switch (tier) {
      case 'excellent': return 'Excelente'
      case 'good': return 'Bom'
      case 'watch': return 'Atenção'
      case 'critical': return 'Crítico'
      default: return tier
    }
  }

  const getHealthTierColor = (tier: string) => {
    switch (tier) {
      case 'excellent': return 'var(--gray-600)'
      case 'good': return 'var(--wedo-green-bright)'
      case 'watch': return 'var(--status-warning)'
      case 'critical': return 'var(--status-error)'
      default: return 'var(--gray-400)'
    }
  }

  const getHealthTierBgColor = (tier: string) => {
    switch (tier) {
      case 'excellent': return 'var(--gray-600-bg-10)'
      case 'good': return 'var(--wedo-green-bg-10)'
      case 'watch': return 'var(--status-warning-bg)'
      case 'critical': return 'var(--status-error-bg)'
      default: return 'var(--gray-bg-10)'
    }
  }

  const getImpactColor = (impact: string) => {
    switch (impact) {
      case 'positive': return 'var(--wedo-green-bright)'
      case 'negative': return 'var(--status-error)'
      default: return 'var(--gray-400)'
    }
  }

  if (!agent) return null

  return (
    <>
      {isOpen && (
        <>
          {/* Backdrop — OPT-027: CSS fade-in replacing framer-motion */}
          <div
            className="fixed inset-0 bg-black/20 z-40 animate-in fade-in duration-200"
            onClick={onClose}
          />

          {/* Panel — OPT-027: CSS slide-in from right replacing framer-motion spring */}
          <div
            className="fixed right-0 top-0 h-full w-full max-w-md z-50 overflow-hidden flex flex-col bg-white animate-in slide-in-from-right duration-300"
          >
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-lia-border-subtle dark:border-lia-border-subtle">
              <div className="flex items-center gap-3">
                <span className="text-2xl">{agent.icon}</span>
                <div>
                  <h3 className="font-semibold text-sm text-gray-800 dark:text-lia-text-primary">
                    {agent.name}
                  </h3>
                  <div className="flex items-center gap-2">
                    <span
                      className="w-2 h-2 rounded-full"
                      style={{backgroundColor: agent.status === 'online' ? 'var(--gray-950)' : agent.status === 'idle' ? 'var(--status-warning)' : 'var(--status-error)'}}
                    />
                    <span className="text-xs text-gray-500 dark:text-lia-text-tertiary">
                      {agent.status === 'online' ? 'Online' : agent.status === 'idle' ? 'Idle' : 'Atenção'}
                    </span>
                  </div>
                </div>
              </div>
              <Button variant="ghost" size="sm" onClick={onClose}>
                <X className="w-4 h-4" />
              </Button>
            </div>

            {/* Quick Stats */}
            <div className="grid grid-cols-3 gap-3 p-4 border-b border-lia-border-subtle dark:border-lia-border-subtle">
              <div className="text-center">
                <div className="text-xl font-bold text-gray-900">{agent.actions_today}</div>
                <div className="text-xs text-gray-400">Ações Hoje</div>
              </div>
              <div className="text-center">
                <div
                  className="text-xl font-bold"
                  style={{color: agent.progress >= 80 ? 'var(--wedo-green-bright)' : agent.progress >= 50 ? 'var(--gray-950)' : 'var(--status-warning)'}}
                >
                  {agent.progress}%
                </div>
                <div className="text-xs text-gray-400">Progresso</div>
              </div>
              <div className="text-center">
                <div className="flex items-center justify-center gap-1">
                  <span className="text-xl font-bold text-gray-900">{agent.daily_goal}</span>
                </div>
                <div className="text-xs text-gray-400">Meta Diária</div>
              </div>
            </div>

            {/* Trend Chart */}
            <div className="p-4 border-b border-lia-border-subtle dark:border-lia-border-subtle">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-medium text-gray-500 dark:text-lia-text-tertiary">
                  Tendência 24h
                </span>
                <div className="flex items-center gap-1">
                  {agent.delta > 0 ? (
                    <TrendingUp className="w-3 h-3 text-status-success" />
                  ) : agent.delta < 0 ? (
                    <TrendingDown className="w-3 h-3 text-status-error" />
                  ) : (
                    <Minus className="w-3 h-3 lia-text-base" />
                  )}
                  <span
                    className="text-xs"
                    style={{color: agent.delta > 0 ? 'var(--wedo-green-bright)' : agent.delta < 0 ? 'var(--status-error)' : undefined}}
                  className={agent.delta === 0 ? 'text-gray-400' : ''}
                  >
                    {agent.delta > 0 ? '+' : ''}{agent.delta}% vs ontem
                  </span>
                </div>
              </div>
              <div className="h-16">
                <Sparkline data={agent.sparkline} color="var(--gray-600)" height={64} />
              </div>
            </div>

            {/* Tabs */}
            <div className="flex border-b border-lia-border-subtle dark:border-lia-border-subtle">
              {[
                { id: 'activity', label: 'Atividades', icon: Activity },
                { id: 'health', label: 'Saúde', icon: Target },
                { id: 'settings', label: 'Config', icon: Settings }
              ].map(tab => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as 'activity' | 'health' | 'settings')}
                  className={`flex-1 flex items-center justify-center gap-1.5 py-3 text-xs font-medium transition-colors ${activeTab !== tab.id ? 'text-gray-500 dark:text-lia-text-tertiary' : ''}`}
                  style={{color: activeTab === tab.id ? 'var(--gray-950)' : undefined,
                    backgroundColor: activeTab === tab.id ? 'var(--gray-bg-20)' : 'transparent',
                    borderBottom: activeTab === tab.id ? '2px solid var(--gray-300)' : '2px solid transparent'}}
                >
                  <tab.icon className="w-3.5 h-3.5" />
                  {tab.label}
                </button>
              ))}
            </div>

            {/* Tab Content */}
            <div className="flex-1 overflow-y-auto">
              {/* Activity Tab */}
              {activeTab === 'activity' && (
                <div className="p-4 space-y-3">
                  {isLoading ? (
                    <div className="flex items-center justify-center py-8 text-gray-400">
                      <Clock className="w-4 h-4 animate-spin mr-2" />
                      Carregando...
                    </div>
                  ) : activities.length === 0 ? (
                    <div className="text-center py-8 text-gray-400">
                      Nenhuma atividade recente
                    </div>
                  ) : (
                    activities.map(activity => (
                      <div
                        key={activity.id}
                        className="flex items-start gap-3 p-3 rounded-md bg-gray-100 dark:bg-lia-bg-secondary"
                      >
                        <div className="flex-shrink-0 mt-0.5">
                          {activity.status === 'success' && <CheckCircle className="w-4 h-4 text-status-success" />}
                          {activity.status === 'in_progress' && <Clock className="w-4 h-4 text-status-warning animate-pulse" />}
                          {activity.status === 'pending' && <Clock className="w-4 h-4 lia-text-base" />}
                          {activity.status === 'error' && <XCircle className="w-4 h-4 text-status-error" />}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-0.5">
                            <span className="text-xs font-medium text-gray-800 dark:text-lia-text-primary">
                              {activity.title}
                            </span>
                            <span className="text-xs text-gray-400">
                              {formatTimeAgo(activity.started_at)}
                            </span>
                          </div>
                          <p className="text-xs text-gray-500 dark:text-lia-text-tertiary">
                            {activity.description}
                          </p>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              )}

              {/* Health Tab */}
              {activeTab === 'health' && healthScore && (
                <div className="p-4 space-y-4">
                  {/* Health Score Circle */}
                  <div className="flex flex-col items-center py-4">
                    <div
                      className="relative w-24 h-24 rounded-full flex items-center justify-center"
                      style={{background: `conic-gradient(${getHealthTierColor(healthScore.tier)} ${healthScore.score}%, var(--gray-200) 0)`}}
                    >
                      <div
                        className="w-20 h-20 rounded-full flex flex-col items-center justify-center bg-white"
                      >
                        <span className="text-2xl font-bold" style={{color: getHealthTierColor(healthScore.tier)}}>
                          {healthScore.score}
                        </span>
                        <span className="text-xs text-gray-400">
                          de 100
                        </span>
                      </div>
                    </div>
                    <Badge 
                      className="mt-3"
                      style={{backgroundColor: getHealthTierBgColor(healthScore.tier),
                        color: getHealthTierColor(healthScore.tier),
                        border: `1px solid ${getHealthTierColor(healthScore.tier)}`}}
                    >
                      {getHealthTierLabel(healthScore.tier)}
                    </Badge>
                  </div>

                  {/* Score Drivers */}
                  <div>
                    <h4 className="text-xs font-medium mb-3 text-gray-800 dark:text-lia-text-primary">
                      Fatores de Score
                    </h4>
                    <div className="space-y-2">
                      {healthScore.drivers.map((driver, i) => (
                        <div key={i} className="flex items-center gap-3">
                          <div className="flex-1">
                            <div className="flex items-center justify-between mb-1">
                              <span className="text-xs text-gray-500 dark:text-lia-text-tertiary">
                                {driver.name}
                              </span>
                              <div className="flex items-center gap-1">
                                {driver.impact === 'positive' && <TrendingUp className="w-3 h-3 text-status-success" />}
                                {driver.impact === 'negative' && <TrendingDown className="w-3 h-3 text-status-error" />}
                                {driver.impact === 'neutral' && <Minus className="w-3 h-3 lia-text-base" />}
                                <span className="text-xs font-medium" style={{color: getImpactColor(driver.impact)}}>
                                  {driver.value}%
                                </span>
                              </div>
                            </div>
                            <div className="h-1.5 rounded-full overflow-hidden bg-gray-200 dark:bg-lia-bg-elevated">
                              <div
                                className="h-full rounded-full"
                                style={{width: `${Math.min(driver.value, 100)}%`,
                                  backgroundColor: getImpactColor(driver.impact)}}
                              />
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Recommendations */}
                  {healthScore.recommendations.length > 0 && (
                    <div>
                      <h4 className="text-xs font-medium mb-3 flex items-center gap-2 text-gray-800 dark:text-lia-text-primary">
                        <Lightbulb className="w-3.5 h-3.5 text-gray-600 dark:text-lia-text-tertiary" />
                        Recomendações
                      </h4>
                      <div className="space-y-2">
                        {healthScore.recommendations.map((rec, i) => (
                          <div
                            key={i}
                            className="p-3 rounded-md flex items-start gap-2 bg-gray-200/20"
                          >
                            <ChevronRight className="w-3 h-3 mt-0.5 text-gray-600 dark:text-lia-text-tertiary flex-shrink-0" />
                            <span className="text-xs text-gray-500 dark:text-lia-text-tertiary">
                              {rec}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Settings Tab */}
              {activeTab === 'settings' && (
                <div className="p-4 space-y-4">
                  <div className="p-4 rounded-md bg-gray-100 dark:bg-lia-bg-secondary">
                    <h4 className="text-xs font-medium mb-2 text-gray-800 dark:text-lia-text-primary">
                      Configurações do Agente
                    </h4>
                    <p className="text-xs text-gray-400">
                      Em breve: Configure prioridades, limites de ações, e preferências de automação.
                    </p>
                  </div>
                  <div className="p-4 rounded-md bg-gray-100 dark:bg-lia-bg-secondary">
                    <h4 className="text-xs font-medium mb-2 text-gray-800 dark:text-lia-text-primary">
                      Integrações
                    </h4>
                    <p className="text-xs text-gray-400">
                      Em breve: Conecte APIs externas e configure webhooks.
                    </p>
                  </div>
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="p-4 border-t border-lia-border-subtle dark:border-lia-border-subtle">
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  className="flex-1 text-xs border-lia-border-default dark:border-lia-border-default"
                >
                  Ver Logs Completos
                </Button>
                <Button 
                  size="sm" 
                  className="flex-1 text-xs bg-gray-900 hover:bg-gray-800 text-white dark:hover:bg-gray-200"
                >
                  Executar Ação
                </Button>
              </div>
            </div>
          </div>
        </>
      )}
    </>
  )
}

export default AgentDetailPanel
