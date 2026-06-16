"use client"

import React from"react"
import { Chip } from "@/components/ui/chip"
import { Button } from"@/components/ui/button"
import {
  Target, Check, AlertTriangle, X, FileText, 
  ExternalLink, Calendar, ChevronDown, ChevronUp,
  TrendingUp, AlertCircle
} from"lucide-react"
import { textStyles, badgeStyles, colors } from"@/lib/design-tokens"

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

const ACCENT_COLOR = 'var(--lia-text-secondary)'

export function RubricEvaluationCard({
  data,
  summary,
  className ="",
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
    if (scoreValue >= 80) return { label: 'Forte', className: ' border-status-success/30' }
    if (scoreValue >= 60) return { label: 'Bom', className: 'bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-secondary border-lia-border-default dark:border-lia-border-default' }
    if (scoreValue >= 40) return { label: 'Moderado', className: ' border-status-warning/30' }
    return { label: 'Fraco', className: ' border-status-error/30' }
  }

  const getScoreColor = (scoreValue: number) => {
    if (scoreValue >= 80) return 'var(--status-success)'
    if (scoreValue >= 60) return 'var(--lia-text-secondary)'
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
        return <Check className="w-3.5 h-3.5 text-lia-text-secondary" />
      case 'partial':
        return <AlertTriangle className="w-3.5 h-3.5 text-status-warning" />
      case 'missing':
        return <X className="w-3.5 h-3.5 text-status-error" />
      default:
        return <AlertCircle className="w-3.5 h-3.5 text-lia-text-secondary" />
    }
  }

  const getRubricColor = (level: string) => {
    switch (level?.toLowerCase()) {
      case 'exceeds':
        return 'text-status-success'
      case 'meets':
        return 'text-lia-text-secondary'
      case 'partial':
        return 'text-status-warning'
      case 'missing':
        return 'text-status-error'
      default:
        return 'text-lia-text-secondary'
    }
  }

  const getRubricBgColor = (level: string) => {
    switch (level?.toLowerCase()) {
      case 'exceeds':
        return 'bg-status-success/10'
      case 'meets':
        return 'bg-lia-bg-secondary dark:bg-lia-bg-primary'
      case 'partial':
        return 'bg-status-warning/10'
      case 'missing':
        return 'bg-status-error/10'
      default:
        return 'bg-lia-bg-secondary'
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
    <div className={`space-y-3 ${className}`} data-testid="rubric-evaluation-card">
      <div className="flex items-center justify-between/50 pb-2">
        <div className="flex items-center gap-2">
          <Target className="w-4 h-4" style={{color: ACCENT_COLOR}} />
          <span className={`${textStyles.subtitle} text-lia-text-primary`}>
            Análise CV vs Vaga
          </span>
        </div>
        {data.recommendation && (
          <Chip variant="neutral" muted className={`${getRecommendationBadge(data.recommendation).className} border-0`}>
            {getRecommendationBadge(data.recommendation).label}
          </Chip>
        )}
      </div>

      <div className="flex items-center justify-between">
        <p className={`${textStyles.bodySmall} text-lia-text-primary`}>
          <span className="font-medium">Vaga:</span> {jobTitle}
        </p>
        {jobCode && (
          <span className={`${textStyles.caption} text-lia-text-secondary font-mono`}>
            ID: {jobCode}
          </span>
        )}
      </div>

      <div className="space-y-1.5">
        <div className="flex items-center gap-3">
          <span className={`${textStyles.label} text-lia-text-secondary min-w-[45px]`}>Score:</span>
          <div className="flex-1 h-2.5 bg-lia-interactive-active dark:bg-lia-bg-elevated rounded-full overflow-hidden max-w-[160px]">
            <div 
              className="h-full rounded-full transition-[width,height] duration-500 ease-out"
              style={{width: `${score}%`,
                backgroundColor: getScoreColor(score)}}
            />
          </div>
          <span className={`${textStyles.label} text-lia-text-primary font-bold min-w-10`}>
            {score}%
          </span>
          <Chip variant="neutral" muted className={`${scoreBadge.className} text-micro px-2 py-0.5 border font-medium`}>
            {data.score_label || scoreBadge.label}
          </Chip>
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
                className={`flex items-start gap-2 p-1.5 rounded-md ${getRubricBgColor(level)} transition-colors motion-reduce:transition-none`}
              >
                <div className="mt-0.5 flex-shrink-0">
                  {getRubricIcon(level)}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5 flex-wrap">
                    <span className={`${textStyles.bodySmall} font-medium ${getRubricColor(level)}`}>
                      {getRubricLabel(level)}:
                    </span>
                    <span className={`${textStyles.bodySmall} text-lia-text-primary`}>
                      {reqName}
                    </span>
                    {req.priority && (
                      <span className={`${textStyles.caption} text-lia-text-secondary bg-lia-bg-primary/50 px-1.5 py-0.5 rounded-md`}>
                        {getPriorityLabel(req.priority)}
                      </span>
                    )}
                  </div>
                  {req.evidence && isExpanded && (
                    <p className={`${textStyles.caption} text-lia-text-secondary mt-0.5 line-clamp-1`}>
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
              className={`flex items-center gap-1 ${textStyles.caption} text-lia-text-secondary hover:text-lia-text-secondary transition-colors motion-reduce:transition-none pl-1 pt-1`}
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
        <div className="flex items-start gap-2 pt-1 bg-lia-bg-secondary/50 p-2 rounded-xl">
          <FileText className="w-3.5 h-3.5 text-lia-text-secondary mt-0.5 flex-shrink-0" />
          <div>
            <span className={`${textStyles.caption} text-lia-text-secondary font-medium block mb-0.5`}>
              Resumo LIA:
            </span>
            <p className={`${textStyles.bodySmall} text-lia-text-primary ${isExpanded ? '' : 'line-clamp-2'} italic`}>"{displaySummary}"
            </p>
          </div>
        </div>
      )}

      {(data.strengths && data.strengths.length > 0) && isExpanded && (
        <div className="flex items-start gap-2 pt-1">
          <TrendingUp className="w-3.5 h-3.5 text-status-success mt-0.5 flex-shrink-0" />
          <div className="flex-1">
            <span className={`${textStyles.caption} text-lia-text-secondary font-medium block mb-1`}>
              Pontos Fortes:
            </span>
            <div className="flex flex-wrap gap-1">
              {data.strengths.map((strength, idx) => (
                <Chip key={idx} variant="neutral" muted className="text-micro">
                  {strength}
                </Chip>
              ))}
            </div>
          </div>
        </div>
      )}

      {(data.concerns && data.concerns.length > 0) && isExpanded && (
        <div className="flex items-start gap-2">
          <AlertCircle className="w-3.5 h-3.5 text-status-warning mt-0.5 flex-shrink-0" />
          <div className="flex-1">
            <span className={`${textStyles.caption} text-lia-text-secondary font-medium block mb-1`}>
              Pontos de Atenção:
            </span>
            <div className="flex flex-wrap gap-1">
              {data.concerns.map((concern, idx) => (
                <Chip key={idx} variant="neutral" muted className="text-micro">
                  {concern}
                </Chip>
              ))}
            </div>
          </div>
        </div>
      )}

      <div className="flex items-center gap-2 pt-2 border-t border-lia-border-subtle/50">
        <Button
          variant="ghost"
          size="sm"
          className={`h-7 px-3 gap-1.5 ${textStyles.bodySmall} bg-lia-bg-primary dark:bg-lia-bg-secondary hover:bg-lia-bg-secondary dark:hover:bg-lia-bg-inverse border border-lia-border-subtle dark:border-lia-border-subtle text-lia-text-primary`}
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
          style={{backgroundColor: 'var(--lia-bg-secondary)',
            borderColor: 'var(--lia-border-default)',
            color: ACCENT_COLOR}}
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
