"use client"

import React, { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
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
}

interface DailyBriefingCardProps {
  userName?: string
  onNavigate?: (page: string) => void
  onActionClick?: (action: string, context?: Record<string, unknown>) => void
}

// [OPT-043] TODO: revisar inline styles dinâmicos (18 ocorrências)
const API_BASE = '/api/backend-proxy'

function getDefaultBriefing(): BriefingData {
  const hour = new Date().getHours()
  const greeting = hour < 12 ? "Bom dia" : hour < 18 ? "Boa tarde" : "Boa noite"
  
  return {
    id: 'default-briefing',
    generated_at: new Date().toISOString(),
    greeting,
    summary: {
      urgent_count: 3,
      tasks_today: 8,
      interviews_today: 2,
      alerts_active: 4
    },
    urgent_actions: [
      {
        id: 'ua-1',
        type: 'feedback_pending',
        title: 'Feedback pendente há 48h',
        description: 'João Silva aguarda retorno sobre entrevista técnica',
        priority: 'high',
        action_label: 'Avaliar',
        action_type: 'provide_feedback',
        related_candidate_id: 'cand-1'
      },
      {
        id: 'ua-2',
        type: 'critical_alert',
        title: 'Vaga sem movimento há 5 dias',
        description: 'UX Designer Sênior precisa de atenção',
        priority: 'critical',
        action_label: 'Verificar',
        action_type: 'view_job',
        related_job_id: 'job-1'
      }
    ],
    pipeline: {
      active_jobs: 6,
      total_candidates: 45,
      candidates_to_contact: 12,
      awaiting_feedback: 5,
      offers_pending: 2,
      stages_summary: [
        { stage: 'triagem', count: 12, label: 'Em Triagem' },
        { stage: 'entrevista', count: 8, label: 'Entrevista' },
        { stage: 'avaliacao', count: 5, label: 'Avaliação' },
        { stage: 'oferta', count: 2, label: 'Oferta' }
      ]
    },
    schedule: [
      {
        id: 'sch-1',
        type: 'interview',
        title: 'Entrevista: Maria Santos',
        time: '10:00',
        duration_minutes: 60,
        location: 'Google Meet'
      },
      {
        id: 'sch-2',
        type: 'interview',
        title: 'Entrevista: Carlos Oliveira',
        time: '15:00',
        duration_minutes: 45,
        location: 'Presencial'
      }
    ],
    insights: [
      {
        type: 'attention',
        icon: 'AlertTriangle',
        title: 'Feedbacks acumulados',
        description: '5 candidatos aguardando avaliação. Priorize para não perder talentos.',
        priority: 'high',
        action: 'Ver candidatos',
        action_type: 'view_awaiting_feedback'
      },
      {
        type: 'opportunity',
        icon: 'TrendingUp',
        title: 'Ofertas pendentes',
        description: '2 candidatos com oferta. Acompanhe para garantir aceite.',
        priority: 'medium',
        action: 'Ver ofertas',
        action_type: 'view_offers'
      }
    ]
  }
}

export function DailyBriefingCard({
  userName,
  onNavigate,
  onActionClick
}: DailyBriefingCardProps) {
  const { user } = useAuth()
  const { user: jwtUser } = useJWTAuth()
  // Usa user.id real via JWT; fallback para 'default_user' se não autenticado
  const userId = jwtUser?.id || 'default_user'
  const [briefing, setBriefing] = useState<BriefingData | null>(() => getDefaultBriefing())
  const [loading, setLoading] = useState(false)
  const [expanded, setExpanded] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [mounted, setMounted] = useState(false)

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
    fetchBriefing()
  }, [])

  const fetchBriefing = async () => {
    try {
      const response = await fetch(`${API_BASE}/briefing?user_id=${userId}`)
      if (response.ok) {
        const result = await response.json()
        if (result.success && result.data) {
          setBriefing(result.data)
        }
      }
    } catch (error) {
    }
  }

  const handleRefresh = async () => {
    setRefreshing(true)
    try {
      const response = await fetch(`${API_BASE}/briefing`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId })
      })
      if (response.ok) {
        const result = await response.json()
        setBriefing(result.data)
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
          onNavigate('Chat com LIA')
      }
    }
  }

  if (!briefing) return null

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
                Seu resumo do dia - {new Date().toLocaleDateString('pt-BR', { weekday: 'long', day: 'numeric', month: 'long' })}
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
          {/* Cards de Métricas - Paleta Monocromática WeDo DS */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            {/* Card Urgentes */}
            <div 
              className="p-2 rounded-md border cursor-pointer transition-colors motion-reduce:transition-none"
              style={{backgroundColor: briefing.summary.urgent_count > 0 ? 'var(--lia-bg-secondary)' : 'var(--lia-bg-secondary)',
                borderColor: 'var(--lia-border-subtle)'}}
              onClick={() => handleActionClick('view_urgent')}
            >
              <div className="flex items-center gap-2 mb-1">
                <AlertCircle className="w-3.5 h-3.5 text-lia-text-secondary" />
                <span className="text-xs font-medium text-lia-text-secondary">Urgentes</span>
              </div>
              <p className="text-lg font-bold" style={{color: 'var(--wedo-cyan-dark)'}}>
                {briefing.summary.urgent_count}
              </p>
            </div>
            
            {/* Card Tarefas Hoje */}
            <div 
              className="p-2 rounded-md border cursor-pointer transition-colors motion-reduce:transition-none"
              style={{backgroundColor: 'var(--lia-bg-secondary)', borderColor: 'var(--lia-border-subtle)'}}
              onClick={() => handleActionClick('view_tasks')}
            >
              <div className="flex items-center gap-2 mb-1">
                <Target className="w-3.5 h-3.5 text-lia-text-secondary" />
                <span className="text-xs font-medium text-lia-text-secondary">Tarefas Hoje</span>
              </div>
              <p className="text-lg font-bold" style={{color: 'var(--wedo-cyan-dark)'}}>
                {briefing.summary.tasks_today}
              </p>
            </div>
            
            {/* Card Entrevistas */}
            <div 
              className="p-2 rounded-md border cursor-pointer transition-colors motion-reduce:transition-none"
              style={{backgroundColor: 'var(--lia-bg-secondary)', borderColor: 'var(--lia-border-subtle)'}}
              onClick={() => handleActionClick('view_interviews')}
            >
              <div className="flex items-center gap-2 mb-1">
                <Calendar className="w-3.5 h-3.5 text-lia-text-secondary" />
                <span className="text-xs font-medium text-lia-text-secondary">Entrevistas</span>
              </div>
              <p className="text-lg font-bold" style={{color: 'var(--wedo-cyan-dark)'}}>
                {briefing.summary.interviews_today}
              </p>
            </div>
            
            {/* Card Alertas */}
            <div 
              className="p-2 rounded-md border cursor-pointer transition-colors motion-reduce:transition-none"
              style={{backgroundColor: 'var(--lia-bg-secondary)', borderColor: 'var(--lia-border-subtle)'}}
              onClick={() => handleActionClick('view_alerts')}
            >
              <div className="flex items-center gap-2 mb-1">
                <Bell className="w-3.5 h-3.5 text-lia-text-secondary" />
                <span className="text-xs font-medium text-lia-text-secondary">Alertas</span>
              </div>
              <p className="text-lg font-bold" style={{color: 'var(--wedo-cyan-dark)'}}>
                {briefing.summary.alerts_active}
              </p>
            </div>
          </div>

          {briefing.urgent_actions.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-xs font-medium flex items-center gap-2" style={{color: 'var(--wedo-cyan-dark)'}}>
                <Zap className="w-4 h-4 text-lia-text-secondary" />
                Ações Urgentes
              </h4>
              <div className="space-y-2">
                {briefing.urgent_actions.slice(0, 3).map((action) => (
                  <div
                    key={action.id}
                    className="flex items-center justify-between p-2 rounded-md border"
                    style={{backgroundColor: 'var(--lia-bg-secondary)',
                      borderColor: 'var(--lia-border-subtle)'}}
                  >
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-medium truncate" style={{color: 'var(--wedo-cyan-dark)'}}>
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
              <h4 className="text-xs font-medium flex items-center gap-2" style={{color: 'var(--wedo-cyan-dark)'}}>
                <Calendar className="w-4 h-4 text-lia-text-secondary" />
                Agenda do Dia
              </h4>
              <div className="flex gap-2 overflow-x-auto pb-1">
                {briefing.schedule.map((item) => (
                  <div
                    key={item.id}
                    className="flex items-center gap-2 p-2 rounded-md border shrink-0 cursor-pointer transition-colors motion-reduce:transition-none"
                    style={{backgroundColor: 'var(--lia-bg-secondary)', borderColor: 'var(--lia-border-subtle)'}}
                    onClick={() => handleActionClick('view_interview', item as unknown as Record<string, unknown>)}
                  >
                    <div 
                      className="w-8 h-8 rounded-md flex items-center justify-center shrink-0"
                      style={{backgroundColor: 'var(--lia-bg-tertiary)'}}
                    >
                      <Clock className="w-4 h-4 text-lia-text-secondary" />
                    </div>
                    <div className="min-w-0">
                      <p className="text-xs font-medium" style={{color: 'var(--wedo-cyan-dark)'}}>
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
              <h4 className="text-xs font-medium flex items-center gap-2" style={{color: 'var(--wedo-cyan-dark)'}}>
                <Brain className="w-4 h-4 text-wedo-cyan" />
                Insights LIA
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

          {/* Card Pipeline - Paleta Monocromática */}
          <div 
            className="p-3 rounded-md border"
            style={{backgroundColor: 'var(--lia-bg-secondary)'}}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div 
                  className="w-8 h-8 rounded-md flex items-center justify-center"
                  style={{backgroundColor: 'var(--lia-bg-tertiary)'}}
                >
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
