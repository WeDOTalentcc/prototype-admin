"use client"

import React, { useState, useEffect } from "react"
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
        console.error('Erro ao buscar atividades:', err)
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
        return 'bg-red-50 text-red-700 border-red-200 dark:bg-red-900/20 dark:text-red-400 dark:border-red-800'
      case 'normal':
        return 'bg-gray-100 text-gray-700 border-gray-300 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-600'
      case 'low':
        return 'bg-gray-50 text-gray-800 dark:text-gray-200 border-gray-200 dark:bg-gray-900/20 dark:border-gray-800'
      default:
        return 'bg-gray-50 text-gray-800 dark:text-gray-200 border-gray-200'
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
      'interview_scheduled': 'var(--gray-100)',
      'lia_suggestion': 'var(--gray-100)',
      'candidate_moved': 'var(--gray-100)',
      'email_sent': 'var(--gray-100)',
      'offer_sent': 'var(--gray-100)',
      'approval_pending': 'var(--gray-100)',
      'voice_screening': 'var(--gray-100)',
      'rubric_evaluation': 'var(--gray-100)',
      'screening_analysis': 'var(--gray-100)',
    }
    return typeMap[activityType] || 'var(--gray-100)'
  }

  const getActivityIconBackground = (activityType: string) => {
    const typeMap: Record<string, string> = {
      'interview_scheduled': 'var(--status-success)',
      'lia_suggestion': 'var(--gray-400)',
      'candidate_moved': 'var(--gray-400)',
      'email_sent': 'var(--gray-400)',
      'offer_sent': 'var(--gray-400)',
      'approval_pending': 'var(--gray-400)',
      'voice_screening': 'var(--gray-400)',
      'rubric_evaluation': 'var(--gray-400)',
      'screening_analysis': 'var(--gray-500)',
    }
    return typeMap[activityType] || 'var(--gray-400)'
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
    if (score >= 80) return { label: 'Forte', className: 'bg-emerald-100 text-emerald-700 border-emerald-200' }
    if (score >= 60) return { label: 'Bom', className: 'bg-gray-100 text-gray-700 border-gray-300' }
    if (score >= 40) return { label: 'Moderado', className: 'bg-amber-100 text-amber-700 border-amber-200' }
    return { label: 'Fraco', className: 'bg-red-100 text-red-700 border-red-200' }
  }

  const getRubricIcon = (evaluation: string) => {
    switch (evaluation?.toLowerCase()) {
      case 'exceeds':
      case 'meets':
        return <Check className="w-3 h-3 text-emerald-600" />
      case 'partial':
        return <AlertTriangle className="w-3 h-3 text-amber-600" />
      case 'missing':
        return <X className="w-3 h-3 text-red-600" />
      default:
        return <AlertCircle className="w-3 h-3 text-gray-400" />
    }
  }

  const getRubricColor = (evaluation: string) => {
    switch (evaluation?.toLowerCase()) {
      case 'exceeds':
        return 'text-emerald-700'
      case 'meets':
        return 'text-wedo-cyan-dark'
      case 'partial':
        return 'text-amber-700'
      case 'missing':
        return 'text-red-700'
      default:
        return 'text-gray-600'
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

  const formatRelativeTime = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffInMs = now.getTime() - date.getTime()
    const diffInMins = Math.floor(diffInMs / 60000)
    const diffInHours = Math.floor(diffInMs / 3600000)
    const diffInDays = Math.floor(diffInMs / 86400000)

    if (diffInMins < 1) return 'agora'
    if (diffInMins < 60) return `há ${diffInMins} ${diffInMins === 1 ? 'minuto' : 'minutos'}`
    if (diffInHours < 24) return `há ${diffInHours} ${diffInHours === 1 ? 'hora' : 'horas'}`
    if (diffInDays < 7) return `há ${diffInDays} ${diffInDays === 1 ? 'dia' : 'dias'}`
    
    return date.toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' })
  }

  if (loading) {
    return (
      <div className={`flex items-center justify-center py-8 ${className}`}>
        <div className="flex flex-col items-center gap-2">
          <Loader2 className="w-5 h-5 animate-spin text-gray-600" />
          <p className={textStyles.bodySmall}>Carregando atividades...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className={`flex items-center justify-center py-8 ${className}`}>
        <div className="text-center">
          <AlertCircle className="w-5 h-5 text-gray-600 mx-auto mb-2" />
          <p className={textStyles.bodySmall}>{error}</p>
        </div>
      </div>
    )
  }

  if (activities.length === 0) {
    return (
      <div className={`flex items-center justify-center py-8 ${className}`}>
        <div className="text-center">
          <Clock className="w-5 h-5 text-gray-600 mx-auto mb-2" />
          <p className={textStyles.bodySmall}>Nenhuma atividade registrada ainda</p>
          {candidateId && (
            <p className={`${textStyles.description} mt-1`}>
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
          className="rounded-md p-2 border border-gray-200 dark:border-gray-700 transition-all cursor-pointer"
          style={{ backgroundColor: getActivityCardBackground(activity.activity_type) }}
        >
          <div className="flex items-start gap-2">
            {/* Icon with colored background (mockup style) */}
            <div 
              className="w-7 h-7 rounded flex items-center justify-center flex-shrink-0" 
              style={{ backgroundColor: getActivityIconBackground(activity.activity_type) }}
            >
              {getActivityIconComponent(activity.activity_type)}
            </div>

            {/* Content */}
            <div className="flex-1 min-w-0">
              {/* Header */}
              <div className="flex items-start justify-between gap-2 mb-1">
                <h4 className={`${textStyles.title} dark:text-gray-100`}>
                  {activity.title}
                </h4>
                <span className={`${textStyles.description} dark:text-gray-500 flex-shrink-0`}>
                  {formatRelativeTime(activity.created_at)}
                </span>
              </div>

              {/* Voice Screening specific content */}
              {activity.activity_type === 'voice_screening' && activity.extra_data && (
                <div className="space-y-1.5">
                  {/* Candidate + Job */}
                  <p className={`${textStyles.bodySmall} dark:text-gray-400`}>
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
                          <span className={`${textStyles.label} text-gray-950 dark:text-gray-50`}>{activity.extra_data.overall_score}/100</span>
                        </div>
                      )}
                      {activity.extra_data.tech_score !== undefined && (
                        <div className="flex items-center gap-1">
                          <span className={textStyles.label}>Técnico:</span>
                          <span className={`${textStyles.label} text-gray-950 dark:text-gray-50`}>{activity.extra_data.tech_score}/100</span>
                        </div>
                      )}
                      {activity.extra_data.comm_score !== undefined && (
                        <div className="flex items-center gap-1">
                          <span className={textStyles.label}>Comunicação:</span>
                          <span className={`${textStyles.label} text-gray-950 dark:text-gray-50`}>{activity.extra_data.comm_score}/100</span>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Summary */}
                  {activity.summary && (
                    <p className={`${textStyles.bodySmall} dark:text-gray-400 line-clamp-2`}>
                      {activity.summary}
                    </p>
                  )}

                  {/* Key strengths */}
                  {activity.extra_data.key_strengths && activity.extra_data.key_strengths.length > 0 && (
                    <div className="flex items-center gap-1 flex-wrap">
                      <span className={textStyles.label}>Pontos fortes:</span>
                      {activity.extra_data.key_strengths.slice(0, 3).map((strength: string, idx: number) => (
                        <Badge key={idx} variant="secondary" className={`${badgeStyles.default} dark:bg-gray-800 dark:text-gray-300`}>
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
                    console.log('View full analysis:', activity.id)
                  }}
                  onScheduleInterview={() => {
                    console.log('Schedule interview:', activity.id)
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
                    <p className={`${textStyles.bodySmall} dark:text-gray-400`}>
                      {activity.summary}
                    </p>
                  )}

                  {/* Red Flags */}
                  {Array.isArray(activity.extra_data.red_flags) && activity.extra_data.red_flags.length > 0 && (
                    <div className="flex items-center gap-1 flex-wrap">
                      <span className={`${textStyles.label} text-amber-700`}>Atenção:</span>
                      {activity.extra_data.red_flags.slice(0, 2).map((flag: string, idx: number) => (
                        <Badge key={idx} variant="secondary" className="bg-amber-50 text-amber-700 border-amber-200 text-micro">
                          {flag}
                        </Badge>
                      ))}
                      {activity.extra_data.red_flags.length > 2 && (
                        <span className={`${textStyles.label} text-amber-600`}>
                          +{activity.extra_data.red_flags.length - 2}
                        </span>
                      )}
                    </div>
                  )}

                  {/* Green Flags */}
                  {Array.isArray(activity.extra_data.green_flags) && activity.extra_data.green_flags.length > 0 && (
                    <div className="flex items-center gap-1 flex-wrap">
                      <span className={`${textStyles.label} text-emerald-700`}>Pontos fortes:</span>
                      {activity.extra_data.green_flags.slice(0, 2).map((flag: string, idx: number) => (
                        <Badge key={idx} variant="secondary" className="bg-emerald-50 text-emerald-700 border-emerald-200 text-micro">
                          {flag}
                        </Badge>
                      ))}
                      {activity.extra_data.green_flags.length > 2 && (
                        <span className={`${textStyles.label} text-emerald-600`}>
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
                    <p className={`${textStyles.bodySmall} dark:text-gray-400`}>
                      {activity.summary}
                    </p>
                  )}
                  {activity.description && (
                    <p className={`${textStyles.bodySmall} text-gray-800 dark:text-gray-200 line-clamp-2`}>
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
                    console.log('Navigate to:', activity.action?.url)
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
