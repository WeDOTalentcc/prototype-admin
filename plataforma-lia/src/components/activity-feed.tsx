"use client"

import React, { useState, useEffect } from "react"
import { formatRelativeTime } from "@/lib/format-utils"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import {
  Phone, Mail, Video, FileText, Users, TrendingUp, Brain, Send,
  CheckCircle, AlertCircle, Clock, ExternalLink, Loader2, Target,
  Check, AlertTriangle, X, Calendar
} from "lucide-react"
import { textStyles, cardStyles, badgeStyles } from "@/lib/design-tokens"
import { RubricEvaluationCard } from "@/components/rubric-evaluation-card"

interface Activity {
  id: string
  activity_type: string
  title: string
  description: string | null
  summary: string | null
  actor: {
    id: string | null
    name: string | null
    type: string | null
  } | null
  target: {
    id: string | null
    name: string | null
    type: string | null
  } | null
  extra_data: Record<string, any>
  priority: string
  category: string | null
  action: {
    url: string
    label: string
  } | null
  created_at: string
}

interface ActivityFeedProps {
  candidateId?: string
  limit?: number
  className?: string
}

export function ActivityFeed({ candidateId, limit = 20, className = "" }: ActivityFeedProps) {
  const [activities, setActivities] = useState<Activity[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [total, setTotal] = useState(0)

  useEffect(() => {
    const fetchActivities = async () => {
      try {
        setLoading(true)
        setError(null)

        const params = new URLSearchParams({
          limit: limit.toString(),
        })

        if (candidateId) {
          params.append('candidate_id', candidateId)
        }

        const response = await fetch(`/api/backend-proxy/activities?${params}`)
        
        if (!response.ok) {
          throw new Error(`Erro ao carregar atividades: ${response.statusText}`)
        }

        const data = await response.json()
        setActivities(data.activities || [])
        setTotal(data.total || 0)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Erro desconhecido')
      } finally {
        setLoading(false)
      }
    }

    fetchActivities()
  }, [candidateId, limit])

  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'voice_screening':
        return <Phone className="w-3.5 h-3.5" />
      case 'email_sent':
        return <Mail className="w-3.5 h-3.5" />
      case 'interview_completed':
        return <Video className="w-3.5 h-3.5" />
      case 'test_completed':
        return <FileText className="w-3.5 h-3.5" />
      case 'profile_approval':
        return <CheckCircle className="w-3.5 h-3.5" />
      case 'pipeline_movement':
        return <TrendingUp className="w-3.5 h-3.5" />
      case 'rubric_evaluation':
        return <Target className="w-3.5 h-3.5" />
      default:
        return <AlertCircle className="w-3.5 h-3.5" />
    }
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'urgent':
        return 'bg-status-error/10 text-status-error border-status-error/30 dark:bg-status-error/20 dark:text-status-error dark:border-status-error/30'
      case 'normal':
        return 'bg-lia-bg-tertiary text-lia-text-secondary border-lia-border-default dark:bg-lia-bg-secondary dark:border-lia-border-default'
      case 'low':
        return 'bg-lia-bg-secondary text-lia-text-primary border-lia-border-subtle dark:bg-lia-bg-primary/20'
      default:
        return 'bg-lia-bg-secondary text-lia-text-primary border-lia-border-subtle'
    }
  }

  const getRecommendationBadge = (recommendation: string) => {
    const badges = {
      'strong_yes': { label: 'Forte Sim', className: badgeStyles.success },
      'interview': { label: 'Entrevistar', className: badgeStyles.info },
      'maybe': { label: 'Talvez', className: badgeStyles.warning },
      'reject': { label: 'Rejeitar', className: badgeStyles.error },
    }
    return badges[recommendation as keyof typeof badges] || { label: recommendation, className: badgeStyles.default }
  }

  const getActivityCardBackground = (activityType: string) => {
    const typeMap: Record<string, string> = {
      'interview_scheduled': 'var(--lia-bg-tertiary)',
      'lia_suggestion': 'var(--lia-bg-tertiary)',
      'candidate_moved': 'var(--lia-bg-tertiary)',
      'email_sent': 'var(--lia-bg-tertiary)',
      'offer_sent': 'var(--lia-bg-tertiary)',
      'approval_pending': 'var(--lia-bg-tertiary)',
      'voice_screening': 'var(--lia-bg-tertiary)',
      'rubric_evaluation': 'var(--lia-bg-tertiary)',
      'screening_analysis': 'var(--lia-bg-tertiary)',
    }
    return typeMap[activityType] || 'var(--lia-bg-tertiary)'
  }

  const getActivityIconBackground = (activityType: string) => {
    const typeMap: Record<string, string> = {
      'interview_scheduled': 'var(--status-success)',
      'lia_suggestion': 'var(--lia-text-tertiary)',
      'candidate_moved': 'var(--lia-text-tertiary)',
      'email_sent': 'var(--lia-text-tertiary)',
      'offer_sent': 'var(--lia-text-tertiary)',
      'approval_pending': 'var(--lia-text-tertiary)',
      'voice_screening': 'var(--lia-text-tertiary)',
      'rubric_evaluation': 'var(--lia-text-tertiary)',
      'screening_analysis': 'var(--lia-text-secondary)',
    }
    return typeMap[activityType] || 'var(--lia-text-tertiary)'
  }

  const getActivityIconComponent = (activityType: string) => {
    switch (activityType) {
      case 'interview_scheduled':
        return <Video className="w-3.5 h-3.5 text-white" />
      case 'lia_suggestion':
      case 'candidate_moved':
      case 'voice_screening':
        return <Brain className="w-3.5 h-3.5 text-white" />
      case 'email_sent':
        return <Mail className="w-3.5 h-3.5 text-white" />
      case 'offer_sent':
        return <Send className="w-3.5 h-3.5 text-white" />
      case 'approval_pending':
        return <FileText className="w-3.5 h-3.5 text-white" />
      case 'rubric_evaluation':
        return <Target className="w-3.5 h-3.5 text-white" />
      case 'screening_analysis':
        return <Brain className="w-3.5 h-3.5 text-white" />
      default:
        return <AlertCircle className="w-3.5 h-3.5 text-white" />
    }
  }

  const getScoreBadge = (score: number) => {
    if (score >= 80) return { label: 'Forte', className: 'bg-status-success/15 text-status-success border-status-success/30' }
    if (score >= 60) return { label: 'Bom', className: 'bg-lia-bg-tertiary text-lia-text-secondary border-lia-border-default' }
    if (score >= 40) return { label: 'Moderado', className: 'bg-status-warning/15 text-status-warning border-status-warning/30' }
    return { label: 'Fraco', className: 'bg-status-error/15 text-status-error border-status-error/30' }
  }

  const getRubricIcon = (evaluation: string) => {
    switch (evaluation?.toLowerCase()) {
      case 'exceeds':
      case 'meets':
        return <Check className="w-3 h-3 text-status-success" />
      case 'partial':
        return <AlertTriangle className="w-3 h-3 text-status-warning" />
      case 'missing':
        return <X className="w-3 h-3 text-status-error" />
      default:
        return <AlertCircle className="w-3 h-3 lia-text-secondary" />
    }
  }

  const getRubricColor = (evaluation: string) => {
    switch (evaluation?.toLowerCase()) {
      case 'exceeds':
        return 'text-status-success'
      case 'meets':
        return 'text-wedo-cyan-dark'
      case 'partial':
        return 'text-status-warning'
      case 'missing':
        return 'text-status-error'
      default:
        return 'text-lia-text-secondary'
    }
  }

  const getRubricLabel = (evaluation: string) => {
    switch (evaluation?.toLowerCase()) {
      case 'exceeds':
        return 'Exceeds'
      case 'meets':
        return 'Meets'
      case 'partial':
        return 'Partial'
      case 'missing':
        return 'Missing'
      default:
        return evaluation
    }
  }

  if (loading) {
    return (
      <div className={`flex items-center justify-center py-8 ${className}`} role="status" aria-live="polite" aria-label="Carregando...">
        <div className="flex flex-col items-center gap-2" role="status" aria-live="polite" aria-label="Carregando...">
          <Loader2 className="w-5 h-5 animate-spin motion-reduce:animate-none text-lia-text-secondary" />
          <p className={textStyles.bodySmall}>Carregando atividades...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className={`flex items-center justify-center py-8 ${className}`}>
        <div className="text-center">
          <AlertCircle className="w-5 h-5 text-lia-text-secondary mx-auto mb-2" />
          <p className={textStyles.bodySmall}>{error}</p>
        </div>
      </div>
    )
  }

  if (activities.length === 0) {
    return (
      <div className={`flex items-center justify-center py-8 ${className}`}>
        <div className="text-center">
          <Clock className="w-5 h-5 text-lia-text-secondary mx-auto mb-2" />
          <p className={textStyles.bodySmall}>Nenhuma atividade registrada ainda</p>
          {candidateId && (
            <p className={`${textStyles.description} mt-1`} aria-live="polite" aria-atomic="true">
              As atividades relacionadas a este candidato aparecerão aqui
            </p>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className={`space-y-2 ${className}`}>
      {activities.map((activity, index) => (
        <div
          key={activity.id}
          className="rounded-md p-2 border border-lia-border-subtle dark:border-lia-border-subtle transition-colors motion-reduce:transition-none cursor-pointer"
          style={{backgroundColor: getActivityCardBackground(activity.activity_type)}}
        >
          <div className="flex items-start gap-2">
            {/* Icon with colored background (mockup style) */}
            <div 
              className="w-7 h-7 rounded-md flex items-center justify-center flex-shrink-0" 
              style={{backgroundColor: getActivityIconBackground(activity.activity_type)}}
            >
              {getActivityIconComponent(activity.activity_type)}
            </div>

            {/* Content */}
            <div className="flex-1 min-w-0">
              {/* Header */}
              <div className="flex items-start justify-between gap-2 mb-1">
                <h4 className={`${textStyles.title}`}>
                  {activity.title}
                </h4>
                <span className={`${textStyles.description} flex-shrink-0`}>
                  {formatRelativeTime(activity.created_at)}
                </span>
              </div>

              {/* Voice Screening specific content */}
              {activity.activity_type === 'voice_screening' && activity.extra_data && (
                <div className="space-y-1.5">
                  {/* Candidate + Job */}
                  <p className={`${textStyles.bodySmall}`} aria-live="polite" aria-atomic="true">
                    {activity.target?.name} • {activity.extra_data.screening_id ? 'Backend Sênior' : 'Vaga'}
                  </p>

                  {/* Recommendation badge */}
                  {activity.extra_data.recommendation && (
                    <div className="flex items-center gap-1.5">
                      <span className={textStyles.label}>Recomendação:</span>
                      <Badge className={`${getRecommendationBadge(activity.extra_data.recommendation).className} border-0`}>
                        {getRecommendationBadge(activity.extra_data.recommendation).label}
                      </Badge>
                    </div>
                  )}


                  {/* Scores */}
                  {(activity.extra_data.overall_score || activity.extra_data.tech_score || activity.extra_data.comm_score) && (

                    <div className="flex items-center gap-2 flex-wrap">
                      {activity.extra_data.overall_score !== undefined && (
                        <div className="flex items-center gap-1">
                          <span className={textStyles.label}>Geral:</span>
                          <span className={`${textStyles.label} text-lia-text-primary`}>{activity.extra_data.overall_score}/100</span>
                        </div>
                      )}
                      {activity.extra_data.tech_score !== undefined && (
                        <div className="flex items-center gap-1">
                          <span className={textStyles.label}>Técnico:</span>
                          <span className={`${textStyles.label} text-lia-text-primary`}>{activity.extra_data.tech_score}/100</span>
                        </div>
                      )}
                      {activity.extra_data.comm_score !== undefined && (
                        <div className="flex items-center gap-1">
                          <span className={textStyles.label}>Comunicação:</span>
                          <span className={`${textStyles.label} text-lia-text-primary`}>{activity.extra_data.comm_score}/100</span>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Summary */}
                  {activity.summary && (
                    // @ts-ignore TODO: fix type
                    <p className={`${textStyles.bodySmall} line-clamp-2`}>
                      {activity.summary}
                    </p>
                  )}

                  {/* Key strengths */}
                  {activity.extra_data.key_strengths && activity.extra_data.key_strengths.length > 0 && (
                    // @ts-ignore TODO: fix type
                    <div className="flex items-center gap-1 flex-wrap">
                      <span className={textStyles.label}>Pontos fortes:</span>
                      {activity.extra_data.key_strengths.slice(0, 3).map((strength: string, idx: number) => (
                        <Badge key={idx} variant="secondary" className={`${badgeStyles.default} dark:bg-lia-bg-secondary`}>
                          {strength}
                        </Badge>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Rubric Evaluation (CV vs Vaga) specific content */}
              {activity.activity_type === 'rubric_evaluation' && activity.extra_data && (
                <RubricEvaluationCard
                  data={activity.extra_data}
                  summary={activity.summary}
                  onViewAnalysis={() => {
                  // @ts-ignore TODO: fix type
                  }}
                  onScheduleInterview={() => {
                  }}
                />
              )}

              {/* Screening Analysis (Triagem Detalhada) specific content */}
              {activity.activity_type === 'screening_analysis' && activity.extra_data && (
                <div className="space-y-1.5">
                  {/* Score and Type */}
                  <div className="flex items-center gap-2 flex-wrap">
                    {(() => {
                      const score = Number(activity.extra_data.overall_score) || 0
                      return (
                        <Badge className={`${
 score >= 70 ? badgeStyles.success :
                          score >= 55 ? badgeStyles.warning :
                          badgeStyles.error
                        } border-0`}>
                          {activity.extra_data.score_label || 'Avaliado'} • {score}%
                        </Badge>
                      )
                    })()}
                    {activity.extra_data.analysis_type && (
                      <span className={textStyles.label}>
                        Análise {activity.extra_data.analysis_type === 'curricular' ? 'Curricular' : 
                                 activity.extra_data.analysis_type === 'behavioral' ? 'Comportamental' : 'Técnica'}
                      </span>
                    )}
                  </div>

                  {/* Summary */}
                  {activity.summary && (
                    <p className={`${textStyles.bodySmall}`}>
                      {activity.summary}
                    </p>
                  )}

                  {/* Red Flags */}
                  {Array.isArray(activity.extra_data.red_flags) && activity.extra_data.red_flags.length > 0 && (
                    <div className="flex items-center gap-1 flex-wrap">
                      <span className={`${textStyles.label} text-status-warning`}>Atenção:</span>
                      {activity.extra_data.red_flags.slice(0, 2).map((flag: string, idx: number) => (
                        <Badge key={idx} variant="secondary" className="bg-status-warning/10 text-status-warning border-status-warning/30 text-micro">
                          {flag}
                        </Badge>
                      ))}
                      {activity.extra_data.red_flags.length > 2 && (
                        <span className={`${textStyles.label} text-status-warning`}>
                          +{activity.extra_data.red_flags.length - 2}
                        </span>
                      )}
                    </div>
                  )}

                  {/* Green Flags */}
                  {Array.isArray(activity.extra_data.green_flags) && activity.extra_data.green_flags.length > 0 && (
                    <div className="flex items-center gap-1 flex-wrap">
                      <span className={`${textStyles.label} text-status-success`}>Pontos fortes:</span>
                      {activity.extra_data.green_flags.slice(0, 2).map((flag: string, idx: number) => (
                        <Badge key={idx} variant="secondary" className="bg-status-success/10 text-status-success border-status-success/30 text-micro">
                          {flag}
                        </Badge>
                      ))}
                      {activity.extra_data.green_flags.length > 2 && (
                        <span className={`${textStyles.label} text-status-success`}>
                          +{activity.extra_data.green_flags.length - 2}
                        </span>
                      )}
                    </div>
                  )}
                </div>
              )}

              {/* Generic content for other activity types */}
              {activity.activity_type !== 'voice_screening' && activity.activity_type !== 'rubric_evaluation' && activity.activity_type !== 'screening_analysis' && (
                <div className="space-y-1">
                  {activity.summary && (
                    <p className={`${textStyles.bodySmall}`}>
                      {activity.summary}
                    </p>
                  )}
                  {activity.description && (
                    <p className={`${textStyles.bodySmall} text-lia-text-primary line-clamp-2`}>
                      {activity.description}
                    </p>
                  )}
                </div>
              )}

              {/* Action button */}
              {activity.action && (
                <Button
                  variant="ghost"
                  size="sm"
                  className={`h-5 px-2 gap-1 mt-1.5 ${textStyles.bodySmall}`}
                  onClick={() => {
                  }}
                >
                  {activity.action.label}
                  <ExternalLink className="w-2.5 h-2.5" />
                </Button>
              )}
            </div>
          </div>
        </div>
      ))}

      {/* Show more indicator if there are more items */}
      {total > activities.length && (
        <p className={`text-center py-2 ${textStyles.bodySmall}`}>
          Mostrando {activities.length} de {total} atividades
        </p>
      )}
    </div>
  )
}
