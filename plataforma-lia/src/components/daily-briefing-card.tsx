"use client"

import React, { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import {
  Sun, Moon, Cloud, AlertTriangle, CheckCircle, TrendingUp, 
  Calendar, Users, Briefcase, Lightbulb, BarChart3, RefreshCw,
  ChevronDown, ChevronUp, Clock, ArrowRight, Brain, Bell,
  AlertCircle, Target, Zap
} from "lucide-react"
import { useAuth } from "@/contexts/auth-context"
import { useJWTAuth } from "@/contexts/auth-context"

interface UrgentAction {
  id: string
  type: string
  title: string
  description: string
  priority: 'critical' | 'high' | 'medium'
  action_label: string
  action_type: string
  related_job_id?: string
  related_candidate_id?: string
}

interface PipelineSummary {
  active_jobs: number
  total_candidates: number
  candidates_to_contact: number
  awaiting_feedback: number
  offers_pending: number
  stages_summary: { stage: string; count: number; label: string }[]
}

interface ScheduleItem {
  id: string
  type: string
  title: string
  time: string
  duration_minutes?: number
  location?: string
  status?: string
}

interface Insight {
  type: 'attention' | 'opportunity' | 'suggestion' | 'info' | 'success'
  icon: string
  title: string
  description: string
  priority: string
  action?: string
  action_type?: string
}

interface PipelinePredictionVacancy {
  job_id: string
  title: string
  closure_probability: number
  predicted_days_to_close: number
  risk_level: string
}

interface PipelinePrediction {
  available: boolean
  vacancies: PipelinePredictionVacancy[]
  at_risk_count?: number
  near_closure_count?: number
}

interface RecruiterBenchmark {
  benchmark_available: boolean
  overall_performance?: string
  comparison?: {
    response_time?: { recruiter?: number; company_avg?: number; diff_pct?: number }
    advanced_per_week?: { recruiter?: number; company_avg?: number; diff_pct?: number }
  }
}

interface BriefingData {
  id: string
  generated_at: string
  greeting: string
  summary: {
    urgent_count: number
    tasks_today: number
    interviews_today: number
    alerts_active: number
  }
  urgent_actions: UrgentAction[]
  pipeline: PipelineSummary
  schedule: ScheduleItem[]
  insights: Insight[]
  pipeline_prediction?: PipelinePrediction
  recruiter_benchmark?: RecruiterBenchmark
}

interface DailyBriefingCardProps {
  userName?: string
  onNavigate?: (page: string) => void
  onActionClick?: (action: string, context?: Record<string, unknown>) => void
  onBriefingLoaded?: (briefing: BriefingData) => void
}

const API_BASE = '/api/backend-proxy'



export function DailyBriefingCard({
  userName,
  onNavigate,
  onActionClick,
  onBriefingLoaded,
}: DailyBriefingCardProps) {
  const { user } = useAuth()
  const { user: jwtUser } = useJWTAuth()
  // BUG-08: null enquanto auth não carrega — fetch é gated via useEffect abaixo
  const userId: string | null = jwtUser?.id || null
  const [briefing, setBriefing] = useState<BriefingData | null>(null)
  const [loading, setLoading] = useState(true)
  const [expanded, setExpanded] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [mounted, setMounted] = useState(false)
  const [fetchError, setFetchError] = useState(false)

  const displayName = userName || user?.name?.split(' ')[0] || "Recrutador"

  const getGreeting = () => {
    const hour = new Date().getHours()
    if (hour < 12) return "Bom dia"
    if (hour < 18) return "Boa tarde"
    return "Boa noite"
  }

  const getGreetingIcon = () => {
    const hour = new Date().getHours()
    if (hour < 12) return <Sun className="w-5 h-5 text-status-warning" />
    if (hour < 18) return <Cloud className="w-5 h-5 text-lia-text-secondary" />
    return <Moon className="w-5 h-5 text-wedo-purple" />
  }

  useEffect(() => {
    setMounted(true)
    if (!userId) return // BUG-08: só busca briefing quando auth hidratar
    fetchBriefing()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId])

  const fetchBriefing = async () => {
    if (!userId) return
    setLoading(true)
    setFetchError(false)
    try {
      const response = await fetch(`${API_BASE}/briefing?user_id=${encodeURIComponent(userId)}`)
      if (response.ok) {
        const result = await response.json()
        if (result.success && result.data) {
          setBriefing(result.data)
          onBriefingLoaded?.(result.data)
        } else {
          setFetchError(true)
        }
      } else {
        setFetchError(true)
      }
    } catch {
      setFetchError(true)
    } finally {
      setLoading(false)
    }
  }

  const handleRefresh = async () => {
    setRefreshing(true)
    try {
      if (!userId) { setRefreshing(false); return }
      const response = await fetch(`${API_BASE}/briefing?user_id=${encodeURIComponent(userId)}&refresh=true`, {
        method: 'POST',
      })
      if (response.ok) {
        const result = await response.json()
        if (result.data) {
          setBriefing(result.data)
          onBriefingLoaded?.(result.data)
        }
      }
    } catch (error) {
    } finally {
      setRefreshing(false)
    }
  }

  const getInsightIcon = (iconName: string) => {
    switch (iconName) {
      case 'AlertTriangle': return <AlertTriangle className="w-4 h-4" />
      case 'TrendingUp': return <TrendingUp className="w-4 h-4" />
      case 'Lightbulb': return <Lightbulb className="w-4 h-4" />
      case 'BarChart3': return <BarChart3 className="w-4 h-4" />
      case 'CheckCircle': return <CheckCircle className="w-4 h-4" />
      default: return <Brain className="w-4 h-4 text-wedo-cyan" />
    }
  }

  const getInsightStyle = (type: string) => {
    switch (type) {
      case 'attention':
        return 'bg-status-warning/10 border-status-warning/30 text-status-warning'
      case 'opportunity':
        return 'bg-status-success/10 border-status-success/30 text-status-success'
      case 'suggestion':
        return 'bg-lia-bg-secondary dark:bg-lia-bg-primary border-lia-border-default dark:border-lia-border-default text-wedo-cyan-dark'
      case 'success':
        return 'bg-status-success/10 border-status-success/30 text-status-success'
      default:
        return 'bg-lia-bg-secondary border-lia-border-subtle text-lia-text-primary'
    }
  }

  const handleActionClick = (actionType: string, context?: Record<string, unknown>) => {
    if (onActionClick) {
      onActionClick(actionType, context)
    }
    if (onNavigate) {
      switch (actionType) {
        case 'provide_feedback':
        case 'view_awaiting_feedback':
          onNavigate('Funil de Talentos')
          break
        case 'view_job':
        case 'view_jobs':
          onNavigate('Vagas')
          break
        case 'view_offers':
          onNavigate('Funil de Talentos')
          break
        case 'view_interview':
          onNavigate('Vagas')
          break
        default:
          onNavigate('Chat')
      }
    }
  }

  if (loading) {
    return (
      <Card className="border-0 overflow-hidden bg-lia-bg-tertiary dark:bg-lia-bg-secondary">
        <CardContent className="p-5">
          <div className="animate-pulse space-y-3">
            <div className="flex items-center gap-3">
              <div className="w-5 h-5 bg-lia-bg-secondary rounded" />
              <div className="space-y-1.5 flex-1">
                <div className="h-4 bg-lia-bg-secondary rounded w-48" />
                <div className="h-3 bg-lia-bg-secondary rounded w-64" />
              </div>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
              {[1, 2, 3, 4].map(i => (
                <div key={i} className="p-2 rounded-xl bg-lia-bg-secondary h-14" />
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (!briefing) {
    return (
      <Card className="border-0 overflow-hidden bg-lia-bg-tertiary dark:bg-lia-bg-secondary">
        <CardContent className="p-5">
          <div className="flex flex-col items-center gap-3 py-4">
            <AlertCircle className="w-8 h-8 text-status-warning" />
            <p className="text-sm text-lia-text-secondary text-center">
              Não foi possível carregar o briefing diário.
            </p>
            <Button
              size="sm"
              variant="outline"
              onClick={handleRefresh}
              disabled={refreshing}
            >
              <RefreshCw className={`w-4 h-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
              Tentar novamente
            </Button>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card
      className="border-0 overflow-hidden bg-lia-bg-tertiary dark:bg-lia-bg-secondary"
    >
      <CardHeader className="pb-3 pt-4 px-5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {getGreetingIcon()}
            <div>
              <CardTitle className="text-base font-semibold text-lia-text-primary">
                {getGreeting()}, {displayName}!
              </CardTitle>
              <p className="text-sm mt-0.5 text-lia-text-tertiary">
                {fetchError
                  ? 'Não foi possível carregar o briefing. Tente atualizar.'
                  : `Seu resumo do dia - ${new Date().toLocaleDateString('pt-BR', { weekday: 'long', day: 'numeric', month: 'long' })}`}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={handleRefresh}
              disabled={refreshing}
              className="h-8 w-8 p-0"
            >
              <RefreshCw className={`w-4 h-4 text-lia-text-tertiary ${refreshing ? 'animate-spin motion-reduce:animate-none' : ''}`} />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setExpanded(!expanded)}
              className="h-8 w-8 p-0"
            >
              {expanded ? (
                <ChevronUp className="w-4 h-4 text-lia-text-tertiary" />
              ) : (
                <ChevronDown className="w-4 h-4 text-lia-text-tertiary" />
              )}
            </Button>
          </div>
        </div>
      </CardHeader>

      {expanded && (
        <CardContent className="px-5 pb-5 pt-0 space-y-4">
          {fetchError && (
            <div className="p-3 rounded-xl border border-status-warning/30 bg-status-warning/5 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-status-warning shrink-0" />
              <p className="text-xs text-lia-text-secondary">
                Não foi possível carregar o briefing do servidor. Exibindo dados parciais.
              </p>
              <Button
                size="sm"
                variant="ghost"
                className="ml-auto text-xs h-6 px-2"
                onClick={handleRefresh}
              >
                Tentar novamente
              </Button>
            </div>
          )}
          {/* Cards de Métricas - Paleta Monocromática WeDo DS */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            {/* Card Urgentes */}
            <div 
              data-testid="briefing-urgent-count"
              className="p-2 rounded-xl border border-lia-border-subtle bg-lia-bg-secondary cursor-pointer transition-colors motion-reduce:transition-none hover:bg-lia-interactive-hover"
              onClick={() => handleActionClick('view_urgent')}
            >
              <div className="flex items-center gap-2 mb-1">
                <AlertCircle className="w-3.5 h-3.5 text-lia-text-secondary" />
                <span className="text-xs font-medium text-lia-text-secondary">Urgentes</span>
              </div>
              <p className="text-lg font-semibold text-wedo-cyan-dark">
                {briefing.summary.urgent_count}
              </p>
            </div>
            
            {/* Card Tarefas Hoje */}
            <div 
              data-testid="briefing-tasks-today"
              className="p-2 rounded-xl border border-lia-border-subtle bg-lia-bg-secondary cursor-pointer transition-colors motion-reduce:transition-none hover:bg-lia-interactive-hover"
              onClick={() => handleActionClick('view_tasks')}
            >
              <div className="flex items-center gap-2 mb-1">
                <Target className="w-3.5 h-3.5 text-lia-text-secondary" />
                <span className="text-xs font-medium text-lia-text-secondary">Tarefas Hoje</span>
              </div>
              <p className="text-lg font-semibold text-wedo-cyan-dark">
                {briefing.summary.tasks_today}
              </p>
            </div>
            
            {/* Card Entrevistas */}
            <div 
              data-testid="briefing-interviews-today"
              className="p-2 rounded-xl border border-lia-border-subtle bg-lia-bg-secondary cursor-pointer transition-colors motion-reduce:transition-none hover:bg-lia-interactive-hover"
              onClick={() => handleActionClick('view_interviews')}
            >
              <div className="flex items-center gap-2 mb-1">
                <Calendar className="w-3.5 h-3.5 text-lia-text-secondary" />
                <span className="text-xs font-medium text-lia-text-secondary">Entrevistas</span>
              </div>
              <p className="text-lg font-semibold text-wedo-cyan-dark">
                {briefing.summary.interviews_today}
              </p>
            </div>
            
            {/* Card Alertas */}
            <div 
              data-testid="briefing-alerts-active"
              className="p-2 rounded-xl border border-lia-border-subtle bg-lia-bg-secondary cursor-pointer transition-colors motion-reduce:transition-none hover:bg-lia-interactive-hover"
              onClick={() => handleActionClick('view_alerts')}
            >
              <div className="flex items-center gap-2 mb-1">
                <Bell className="w-3.5 h-3.5 text-lia-text-secondary" />
                <span className="text-xs font-medium text-lia-text-secondary">Alertas</span>
              </div>
              <p className="text-lg font-semibold text-wedo-cyan-dark">
                {briefing.summary.alerts_active}
              </p>
            </div>
          </div>

          {briefing.urgent_actions.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-xs font-medium flex items-center gap-2 text-wedo-cyan-dark">
                <Zap className="w-4 h-4 text-lia-text-secondary" />
                Ações Urgentes
              </h4>
              <div className="space-y-2">
                {briefing.urgent_actions.slice(0, 3).map((action) => (
                  <div
                    key={action.id}
                    data-testid={`urgent-action-${action.id}`}
                    className="flex items-center justify-between p-2 rounded-xl border border-lia-border-subtle bg-lia-bg-secondary"
                  >
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-medium truncate text-wedo-cyan-dark">
                        {action.title}
                      </p>
                      <p className="text-xs truncate text-lia-text-secondary">
                        {action.description}
                      </p>
                    </div>
                    <Button
                      size="sm"
                      variant="outline"
                      className="ml-3 h-7 text-xs shrink-0 font-semibold border-lia-border-default"
                      onClick={() => handleActionClick(action.action_type, action as unknown as Record<string, unknown>)}
                    >
                      {action.action_label}
                      <ArrowRight className="w-3 h-3 ml-1" />
                    </Button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {briefing.schedule.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-xs font-medium flex items-center gap-2 text-wedo-cyan-dark">
                <Calendar className="w-4 h-4 text-lia-text-secondary" />
                Agenda do Dia
              </h4>
              <div className="flex gap-2 overflow-x-auto pb-1">
                {briefing.schedule.map((item) => (
                  <div
                    key={item.id}
                    data-testid={`schedule-item-${item.id}`}
                    className="flex items-center gap-2 p-2 rounded-xl border border-lia-border-subtle bg-lia-bg-secondary shrink-0 cursor-pointer transition-colors motion-reduce:transition-none hover:bg-lia-interactive-hover"
                    onClick={() => handleActionClick('view_interview', item as unknown as Record<string, unknown>)}
                  >
                    <div className="w-8 h-8 rounded-xl flex items-center justify-center shrink-0 bg-lia-bg-tertiary">
                      <Clock className="w-4 h-4 text-lia-text-secondary" />
                    </div>
                    <div className="min-w-0">
                      <p className="text-xs font-medium text-wedo-cyan-dark">
                        {item.time}
                      </p>
                      <p className="text-xs truncate text-lia-text-secondary">
                        {item.title}
                      </p>
                      {item.location && (
                        <p className="text-xs truncate text-lia-text-secondary">
                          {item.location}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {briefing.insights.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-xs font-medium flex items-center gap-2 text-wedo-cyan-dark">
                <Brain className="w-4 h-4 text-wedo-cyan" />
                Insights IA
              </h4>
              <div className="grid md:grid-cols-2 gap-2">
                {briefing.insights.map((insight, index) => (
                  <div
                    key={`insight-${index}`}
                    className={`p-2 rounded-md border ${getInsightStyle(insight.type)}`}
                  >
                    <div className="flex items-start gap-2">
                      <div className="shrink-0 mt-0.5">
                        {getInsightIcon(insight.icon)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-xs font-medium">{insight.title}</p>
                        <p className="text-xs mt-0.5 opacity-80">{insight.description}</p>
                        {insight.action && (
                          <Button
                            size="sm"
                            variant="link"
                            className="h-auto p-0 mt-1 text-xs"
                            onClick={() => handleActionClick(insight.action_type || 'view', insight as unknown as Record<string, unknown>)}
                          >
                            {insight.action} <ArrowRight className="w-3 h-3 ml-1" />
                          </Button>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {briefing.recruiter_benchmark?.benchmark_available && (
            <div className="p-3 rounded-xl border bg-lia-bg-secondary">
              <h4 className="text-xs font-medium flex items-center gap-2 mb-2 text-wedo-cyan-dark">
                <TrendingUp className="w-4 h-4 text-wedo-cyan" />
                Benchmark do Recrutador
              </h4>
              <div className="grid grid-cols-2 gap-3">
                {briefing.recruiter_benchmark.comparison?.response_time && (
                  <div>
                    <p className="text-xs text-lia-text-secondary">Tempo de Resposta</p>
                    <p className="text-sm font-semibold text-lia-text-primary">
                      {briefing.recruiter_benchmark.comparison.response_time.recruiter?.toFixed(1)}h
                    </p>
                    <p className="text-xs text-lia-text-tertiary">
                      Média empresa: {briefing.recruiter_benchmark.comparison.response_time.company_avg?.toFixed(1)}h
                    </p>
                  </div>
                )}
                {briefing.recruiter_benchmark.comparison?.advanced_per_week && (
                  <div>
                    <p className="text-xs text-lia-text-secondary">Avanços/Semana</p>
                    <p className="text-sm font-semibold text-lia-text-primary">
                      {briefing.recruiter_benchmark.comparison.advanced_per_week.recruiter}
                    </p>
                    <p className="text-xs text-lia-text-tertiary">
                      Média empresa: {briefing.recruiter_benchmark.comparison.advanced_per_week.company_avg}
                    </p>
                  </div>
                )}
              </div>
              {briefing.recruiter_benchmark.overall_performance && (
                <p className="text-xs mt-2 text-lia-text-secondary">
                  Performance geral: <strong className="text-lia-text-primary">{briefing.recruiter_benchmark.overall_performance}</strong>
                </p>
              )}
            </div>
          )}

          {briefing.pipeline_prediction?.available && (briefing.pipeline_prediction.at_risk_count ?? 0) > 0 && (
            <div className="p-3 rounded-xl border bg-lia-bg-secondary">
              <h4 className="text-xs font-medium flex items-center gap-2 mb-2 text-wedo-cyan-dark">
                <Target className="w-4 h-4 text-wedo-cyan" />
                Predição de Pipeline
              </h4>
              <div className="space-y-1.5">
                {briefing.pipeline_prediction.vacancies
                  .filter(v => v.closure_probability < 50)
                  .slice(0, 3)
                  .map(v => (
                    <div key={v.job_id} className="flex items-center justify-between text-xs">
                      <span className="text-lia-text-primary truncate flex-1">{v.title}</span>
                      <span className={`ml-2 font-medium ${v.closure_probability < 30 ? 'text-status-error' : 'text-status-warning'}`}>
                        {v.closure_probability}% chance de fechar
                      </span>
                    </div>
                  ))}
              </div>
              <Button
                size="sm"
                variant="ghost"
                className="text-xs font-semibold text-lia-text-secondary mt-2 h-auto p-0"
                onClick={() => onActionClick?.('view_pipeline_prediction', {
                  pipeline_prediction: briefing.pipeline_prediction,
                })}
              >
                Ver todas predições <ArrowRight className="w-3 h-3 ml-1" />
              </Button>
            </div>
          )}

          {/* Card Pipeline - Paleta Monocromática */}
          <div 
            data-testid="briefing-pipeline-card"
            className="p-3 rounded-xl border bg-lia-bg-secondary"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-xl flex items-center justify-center bg-lia-bg-tertiary">
                  <BarChart3 className="w-4 h-4 text-lia-text-secondary" />
                </div>
                <div>
                  <p className="text-sm font-medium text-lia-text-primary">
                    Pipeline: {briefing.pipeline.total_candidates} candidatos em {briefing.pipeline.active_jobs} vagas
                  </p>
                  <div className="flex items-center gap-3 mt-0.5">
                    {briefing.pipeline.stages_summary.slice(0, 4).map((stage, i) => (
                      <span key={i} className="text-xs text-lia-text-secondary">
                        {stage.label}: <strong>{stage.count}</strong>
                      </span>
                    ))}
                  </div>
                </div>
              </div>
              <Button
                size="sm"
                variant="ghost"
                className="text-xs font-semibold text-lia-text-secondary"
                onClick={() => onActionClick?.('open_pipeline_chat', { 
                  pipeline: briefing.pipeline,
                  stale_days: 3 
                })}
              >
                Ver Pipeline <ArrowRight className="w-3 h-3 ml-1" />
              </Button>
            </div>
          </div>
        </CardContent>
      )}
    </Card>
  )
}
