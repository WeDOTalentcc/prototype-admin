"use client"

import React from "react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Target, Check, AlertTriangle, X, FileText, 
  ExternalLink, Calendar, ChevronDown, ChevronUp,
  TrendingUp, AlertCircle
} from "lucide-react"
import { textStyles, badgeStyles, colors } from "@/lib/design-tokens"

interface RubricRequirement {
  requirement: string
  name?: string
  priority: 'essential' | 'important' | 'nice-to-have' | string
  level: 'exceeds' | 'meets' | 'partial' | 'missing' | string
  evidence?: string
  evaluation?: string
}

interface RubricEvaluationData {
  job_id?: string
  job_title?: string
  job_code?: string
  score?: number
  overall_score?: number
  score_label?: string
  evaluations?: RubricRequirement[]
  requirements?: RubricRequirement[]
  summary?: string
  recommendation?: 'strong_yes' | 'interview' | 'maybe' | 'reject' | string
  strengths?: string[]
  concerns?: string[]
}

interface RubricEvaluationCardProps {
  data: RubricEvaluationData
  summary?: string | null
  className?: string
  showFullDetails?: boolean
  onViewAnalysis?: () => void
  onScheduleInterview?: () => void
}

const ACCENT_COLOR = 'var(--gray-600)'

export function RubricEvaluationCard({
  data,
  summary,
  className = "",
  showFullDetails = false,
  onViewAnalysis,
  onScheduleInterview
}: RubricEvaluationCardProps) {
  const [isExpanded, setIsExpanded] = React.useState(showFullDetails)
  
  const score = data.score ?? data.overall_score ?? 0
  const requirements = data.evaluations ?? data.requirements ?? []
  const displaySummary = summary ?? data.summary
  const jobTitle = data.job_title || 'Vaga não especificada'
  const jobCode = data.job_code || data.job_id

  const getScoreBadge = (scoreValue: number) => {
    if (scoreValue >= 80) return { label: 'Forte', className: 'bg-status-success/15 text-status-success border-status-success/30' }
    if (scoreValue >= 60) return { label: 'Bom', className: 'bg-gray-100 dark:bg-gray-800 text-wedo-cyan-dark border-gray-300 dark:border-gray-600' }
    if (scoreValue >= 40) return { label: 'Moderado', className: 'bg-status-warning/15 text-status-warning border-status-warning/30' }
    return { label: 'Fraco', className: 'bg-status-error/15 text-status-error border-status-error/30' }
  }

  const getScoreColor = (scoreValue: number) => {
    if (scoreValue >= 80) return 'var(--status-success)'
    if (scoreValue >= 60) return 'var(--gray-600)'
    if (scoreValue >= 40) return 'var(--status-warning)'
    return 'var(--status-error)'
  }

  const getEvaluationLevel = (req: RubricRequirement): string => {
    return req.level || req.evaluation || 'unknown'
  }

  const getRubricIcon = (level: string) => {
    switch (level?.toLowerCase()) {
      case 'exceeds':
        return <Check className="w-3.5 h-3.5 text-status-success" />
      case 'meets':
        return <Check className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
      case 'partial':
        return <AlertTriangle className="w-3.5 h-3.5 text-status-warning" />
      case 'missing':
        return <X className="w-3.5 h-3.5 text-status-error" />
      default:
        return <AlertCircle className="w-3.5 h-3.5 text-gray-400" />
    }
  }

  const getRubricColor = (level: string) => {
    switch (level?.toLowerCase()) {
      case 'exceeds':
        return 'text-status-success'
      case 'meets':
        return 'text-wedo-cyan-dark'
      case 'partial':
        return 'text-status-warning'
      case 'missing':
        return 'text-status-error'
      default:
        return 'text-gray-600'
    }
  }

  const getRubricBgColor = (level: string) => {
    switch (level?.toLowerCase()) {
      case 'exceeds':
        return 'bg-status-success/10'
      case 'meets':
        return 'bg-gray-50 dark:bg-gray-900'
      case 'partial':
        return 'bg-status-warning/10'
      case 'missing':
        return 'bg-status-error/10'
      default:
        return 'bg-gray-50'
    }
  }

  const getRubricLabel = (level: string) => {
    switch (level?.toLowerCase()) {
      case 'exceeds':
        return 'Exceeds'
      case 'meets':
        return 'Meets'
      case 'partial':
        return 'Partial'
      case 'missing':
        return 'Missing'
      default:
        return level
    }
  }

  const getPriorityLabel = (priority: string) => {
    switch (priority?.toLowerCase()) {
      case 'essential':
        return 'Essencial'
      case 'important':
        return 'Importante'
      case 'nice-to-have':
        return 'Desejável'
      default:
        return priority
    }
  }

  const getRecommendationBadge = (recommendation: string) => {
    const badges: Record<string, { label: string; className: string }> = {
      'strong_yes': { label: 'Forte Sim', className: badgeStyles.success },
      'interview': { label: 'Entrevistar', className: badgeStyles.info },
      'maybe': { label: 'Talvez', className: badgeStyles.warning },
      'reject': { label: 'Rejeitar', className: badgeStyles.error },
    }
    return badges[recommendation] || { label: recommendation, className: badgeStyles.default }
  }

  const sortedRequirements = [...requirements].sort((a, b) => {
    const order = { 'exceeds': 0, 'meets': 1, 'partial': 2, 'missing': 3 }
    const aLevel = getEvaluationLevel(a).toLowerCase()
    const bLevel = getEvaluationLevel(b).toLowerCase()
    return (order[aLevel as keyof typeof order] ?? 4) - (order[bLevel as keyof typeof order] ?? 4)
  })

  const visibleRequirements = isExpanded ? sortedRequirements : sortedRequirements.slice(0, 4)
  const hasMoreRequirements = sortedRequirements.length > 4

  const scoreBadge = getScoreBadge(score)

  return (
    <div className={`space-y-3 ${className}`}>
      <div className="flex items-center justify-between border-b border-gray-200/50 pb-2">
        <div className="flex items-center gap-2">
          <Target className="w-4 h-4" style={{ color: ACCENT_COLOR }} />
          <span className={`${textStyles.subtitle} text-gray-800`}>
            Análise CV vs Vaga
          </span>
        </div>
        {data.recommendation && (
          <Badge className={`${getRecommendationBadge(data.recommendation).className} border-0`}>
            {getRecommendationBadge(data.recommendation).label}
          </Badge>
        )}
      </div>

      <div className="flex items-center justify-between">
        <p className={`${textStyles.bodySmall} text-gray-800 dark:text-gray-200`}>
          <span className="font-medium">Vaga:</span> {jobTitle}
        </p>
        {jobCode && (
          <span className={`${textStyles.caption} text-gray-500 font-mono`}>
            ID: {jobCode}
          </span>
        )}
      </div>

      <div className="space-y-1.5">
        <div className="flex items-center gap-3">
          <span className={`${textStyles.label} text-gray-600 min-w-[45px]`}>Score:</span>
          <div className="flex-1 h-2.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden max-w-[160px]">
            <div 
              className="h-full rounded-full transition-all duration-500 ease-out"
              style={{ 
                width: `${score}%`,
                backgroundColor: getScoreColor(score)
              }}
            />
          </div>
          <span className={`${textStyles.label} text-gray-950 dark:text-gray-50 font-bold min-w-10`}>
            {score}%
          </span>
          <Badge className={`${scoreBadge.className} text-micro px-2 py-0.5 border font-medium`}>
            {data.score_label || scoreBadge.label}
          </Badge>
        </div>
      </div>

      {visibleRequirements.length > 0 && (
        <div className="space-y-1.5 pt-1">
          {visibleRequirements.map((req, idx) => {
            const level = getEvaluationLevel(req)
            const reqName = req.name || req.requirement
            return (
              <div 
                key={idx} 
                className={`flex items-start gap-2 p-1.5 rounded ${getRubricBgColor(level)} transition-colors`}
              >
                <div className="mt-0.5 flex-shrink-0">
                  {getRubricIcon(level)}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5 flex-wrap">
                    <span className={`${textStyles.bodySmall} font-medium ${getRubricColor(level)}`}>
                      {getRubricLabel(level)}:
                    </span>
                    <span className={`${textStyles.bodySmall} text-gray-800`}>
                      {reqName}
                    </span>
                    {req.priority && (
                      <span className={`${textStyles.caption} text-gray-500 bg-white/50 px-1.5 py-0.5 rounded`}>
                        {getPriorityLabel(req.priority)}
                      </span>
                    )}
                  </div>
                  {req.evidence && isExpanded && (
                    <p className={`${textStyles.caption} text-gray-600 mt-0.5 line-clamp-1`}>
                      {req.evidence}
                    </p>
                  )}
                </div>
              </div>
            )
          })}
          
          {hasMoreRequirements && (
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className={`flex items-center gap-1 ${textStyles.caption} text-gray-500 hover:text-gray-700 transition-colors pl-1 pt-1`}
            >
              {isExpanded ? (
                <>
                  <ChevronUp className="w-3 h-3" />
                  Mostrar menos
                </>
              ) : (
                <>
                  <ChevronDown className="w-3 h-3" />
                  +{sortedRequirements.length - 4} mais requisitos
                </>
              )}
            </button>
          )}
        </div>
      )}

      {displaySummary && (
        <div className="flex items-start gap-2 pt-1 bg-gray-50/50 p-2 rounded-md">
          <FileText className="w-3.5 h-3.5 text-gray-400 mt-0.5 flex-shrink-0" />
          <div>
            <span className={`${textStyles.caption} text-gray-500 font-medium block mb-0.5`}>
              Resumo LIA:
            </span>
            <p className={`${textStyles.bodySmall} text-gray-800 dark:text-gray-200 ${isExpanded ? '' : 'line-clamp-2'} italic`}>
              "{displaySummary}"
            </p>
          </div>
        </div>
      )}

      {(data.strengths && data.strengths.length > 0) && isExpanded && (
        <div className="flex items-start gap-2 pt-1">
          <TrendingUp className="w-3.5 h-3.5 text-status-success mt-0.5 flex-shrink-0" />
          <div className="flex-1">
            <span className={`${textStyles.caption} text-gray-500 font-medium block mb-1`}>
              Pontos Fortes:
            </span>
            <div className="flex flex-wrap gap-1">
              {data.strengths.map((strength, idx) => (
                <Badge key={idx} variant="secondary" className="bg-status-success/10 text-status-success text-micro">
                  {strength}
                </Badge>
              ))}
            </div>
          </div>
        </div>
      )}

      {(data.concerns && data.concerns.length > 0) && isExpanded && (
        <div className="flex items-start gap-2">
          <AlertCircle className="w-3.5 h-3.5 text-status-warning mt-0.5 flex-shrink-0" />
          <div className="flex-1">
            <span className={`${textStyles.caption} text-gray-500 font-medium block mb-1`}>
              Pontos de Atenção:
            </span>
            <div className="flex flex-wrap gap-1">
              {data.concerns.map((concern, idx) => (
                <Badge key={idx} variant="secondary" className="bg-status-warning/10 text-status-warning text-micro">
                  {concern}
                </Badge>
              ))}
            </div>
          </div>
        </div>
      )}

      <div className="flex items-center gap-2 pt-2 border-t border-gray-200/50">
        <Button
          variant="ghost"
          size="sm"
          className={`h-7 px-3 gap-1.5 ${textStyles.bodySmall} bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 border border-gray-200 dark:border-gray-700 text-gray-800 dark:text-gray-200`}
          onClick={(e) => {
            e.stopPropagation()
            onViewAnalysis?.()
          }}
        >
          <ExternalLink className="w-3.5 h-3.5" />
          Ver Análise Completa
        </Button>
        <Button
          variant="ghost"
          size="sm"
          className={`h-7 px-3 gap-1.5 ${textStyles.bodySmall} hover:bg-opacity-20 border`}
          style={{ 
            backgroundColor: `${ACCENT_COLOR}15`,
            borderColor: `${ACCENT_COLOR}40`,
            color: ACCENT_COLOR
          }}
          onClick={(e) => {
            e.stopPropagation()
            onScheduleInterview?.()
          }}
        >
          <Calendar className="w-3.5 h-3.5" />
          Agendar Entrevista
        </Button>
      </div>
    </div>
  )
}

export default RubricEvaluationCard
