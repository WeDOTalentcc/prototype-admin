"use client"

import { Chip } from "@/components/ui/chip"
import { Tooltip, TooltipContent, TooltipTrigger } from"@/components/ui/tooltip"
import { textStyles, cardStyles, previewChipVariants } from '@/lib/design-tokens'
import { cn } from '@/lib/utils'
import { getWsiScoreColor } from '@/lib/wsi/visual'
import {
  X, CheckCircle, AlertCircle, Clock, Brain, Target,
  TrendingUp, Edit, BarChart3, Briefcase, Copy, Check,
  ChevronUp, ChevronDown
} from"lucide-react"

interface OpinionCardProps {
  opinion: Record<string, unknown>
  isExpanded: boolean
  onToggle: () => void
  type: 'general' | 'wsi'
  copiedItemId: string | null
  onCopyOpinion: (opinion: Record<string, unknown>, type: 'general' | 'wsi') => void
}

export function OpinionCard({ opinion, isExpanded, onToggle, type, copiedItemId, onCopyOpinion }: OpinionCardProps) {
  const getScoreColor = (score: number | null, isWsi: boolean = false) => {
    if (score === null || score === undefined) return 'text-lia-text-secondary'
    if (isWsi) return getWsiScoreColor(score)
    if (score >= 80) return 'text-status-success'
    if (score >= 60) return 'text-status-warning'
    return 'text-status-error'
  }

  const getRecommendationBadge = (rec: string | null) => {
    if (!rec) return null
    if (rec === 'approved') {
      return (
        <Chip variant="success" muted className={cn(previewChipVariants.success, 'gap-0.5')}>
          <CheckCircle className="w-2.5 h-2.5" />
          APROVADO
        </Chip>
      )
    }
    if (rec === 'pending_review') {
      return (
        <Chip variant="warning" muted className={cn(previewChipVariants.warning, 'gap-0.5')}>
          <Clock className="w-2.5 h-2.5" />
          PENDENTE
        </Chip>
      )
    }
    if (rec === 'not_approved') {
      return (
        <Chip variant="danger" muted className={cn(previewChipVariants.error, 'gap-0.5')}>
          <X className="w-2.5 h-2.5" />
          NÃO APROVADO
        </Chip>
      )
    }
    return null
  }

  const isWsiOpinion = type === 'wsi' || opinion.opinion_type === 'wsi'
  const displayScore = (isWsiOpinion ? opinion.wsi_score : opinion.score) as number | null

  const formatOpinionDate = (dateStr: string | null) => {
    if (!dateStr) return ''
    const date = new Date(dateStr)
    return date.toLocaleDateString('pt-BR', { day: '2-digit', month: 'short', year: 'numeric' })
  }

  return (
    <div className={`${cardStyles.default} p-3 overflow-hidden`}>
      <div
        onClick={onToggle}
        className="w-full p-3 flex items-center justify-between hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none cursor-pointer"
        role="button"
        tabIndex={0}
        onKeyDown={(e) => e.key === 'Enter' && onToggle()}
      >
        <div className="flex items-center gap-2">
          <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
 isWsiOpinion ? 'bg-wedo-purple/15' : 'bg-lia-bg-tertiary'
          }`}>
            {isWsiOpinion ? (
              <Target className="w-4 h-4 text-wedo-purple" />
            ) : (
              <Brain className="w-4 h-4 text-wedo-cyan" />
            )}
          </div>
          <div className="text-left">
            <div className="flex items-center gap-2 flex-wrap">
              <span className={textStyles.label}>
                {isWsiOpinion ? 'Parecer WSI' : (opinion.job_vacancy_id ? 'Parecer de Vaga' : 'Parecer Geral')}
              </span>
              {opinion.job_vacancy_id && opinion.job_vacancy_title ? (
                <Chip variant="neutral" muted className="text-micro px-1.5 py-0 h-4 flex items-center bg-lia-bg-tertiary text-lia-text-secondary border-lia-border-subtle flex items-center gap-1">
                  <Briefcase className="w-2.5 h-2.5" />
                  #{String(opinion.job_vacancy_id).slice(0, 6)} - {String(opinion.job_vacancy_title)}
                </Chip>
              ) : opinion.job_vacancy_title ? (
                <Chip variant="neutral" muted className="text-micro px-1.5 py-0 h-4 flex items-center bg-lia-bg-tertiary text-lia-text-secondary border-lia-border-subtle flex items-center gap-1">
                  <Briefcase className="w-2.5 h-2.5" />
                  {String(opinion.job_vacancy_title)}
                </Chip>
              ) : !opinion.job_vacancy_id ? (
                <Chip variant="neutral" muted className="text-micro px-1.5 py-0 h-4 flex items-center bg-lia-bg-tertiary text-lia-text-secondary border-lia-border-subtle">
                  Sem vaga vinculada
                </Chip>
              ) : null}
            </div>
            <div className="flex items-center gap-2 mt-0.5">
              {displayScore !== null && displayScore !== undefined && (
                <span className={`text-micro font-semibold ${getScoreColor(displayScore, isWsiOpinion)}`}>
                  {/* @canonical-allow-100 fallback display for non-WSI legacy opinion (canonical Surface 1) */}
                  {isWsiOpinion ? `WSI: ${displayScore.toFixed(1)}/10` : `Nota: ${Math.round(displayScore)}/100`}
                </span>
              )}
              {!!opinion.archetype && (
                <>
                  <span className="lia-text-muted">•</span>
                  <span className={textStyles.caption}>{String(opinion.archetype)}</span>
                </>
              )}
              {getRecommendationBadge(opinion.recommendation as string | null)}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {!!opinion.created_at && (
            <span className="text-micro text-lia-text-muted">{formatOpinionDate(String(opinion.created_at))}</span>
          )}
          <Tooltip>
            <TooltipTrigger asChild>
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  onCopyOpinion(opinion, type)
                }}
                className="p-1 hover:bg-lia-interactive-hover rounded-md transition-colors motion-reduce:transition-none"
              >
                {copiedItemId === `opinion-${opinion.id}` ? (
                  <Check className="w-3.5 h-3.5 text-status-success" />
                ) : (
                  <Copy className="w-3.5 h-3.5 text-lia-text-muted hover:text-lia-text-secondary" />
                )}
              </button>
            </TooltipTrigger>
            <TooltipContent side="top" className="text-micro">Copiar parecer</TooltipContent>
          </Tooltip>
          {isExpanded ? (
            <ChevronUp className="w-4 h-4 text-lia-text-muted" />
          ) : (
            <ChevronDown className="w-4 h-4 text-lia-text-muted" />
          )}
        </div>
      </div>

      {isExpanded && (
        <div className="px-3 pb-3 pt-0 border-t border-lia-border-subtle space-y-3">
          {!!opinion.summary && (
            <div className="pt-3">
              <p className="text-xs text-lia-text-primary leading-relaxed">
                {String(opinion.summary)}
              </p>
            </div>
          )}

          {(!!opinion.score_breakdown && Object.keys(opinion.score_breakdown as Record<string, unknown>).length > 0) && (
            <div>
              <h5 className={`${textStyles.label} mb-1.5 flex items-center gap-1`}>
                <BarChart3 className="w-3 h-3" />
                Score Breakdown
              </h5>
              <div className="grid grid-cols-2 gap-1.5">
                {Object.entries(opinion.score_breakdown as Record<string, unknown>).map(([key, value]) => (
                  key !== 'f11_report' && (typeof value === 'number' || typeof value === 'string') && (
                    <div key={key} className="flex items-center justify-between text-micro bg-lia-bg-secondary rounded-full px-2 py-1">
                      <span className="text-lia-text-secondary capitalize">{key.replace(/_/g, ' ')}</span>
                      <span className="font-medium text-lia-text-primary">{typeof value === 'number' ? `${Math.round(value)}%` : String(value)}</span>
                    </div>
                  )
                ))}
              </div>
            </div>
          )}

          {(opinion.strengths as string[])?.length > 0 && (
            <div>
              <h5 className={`${textStyles.label} text-status-success mb-1 flex items-center gap-1`}>
                <CheckCircle className="w-3 h-3" />
                Pontos Fortes
              </h5>
              <ul className="space-y-0.5">
                {(opinion.strengths as string[]).map((s: string, i: number) => (
                  <li key={`str-${i}`} className={`${textStyles.caption} text-lia-text-secondary flex items-start gap-1`}>
                    <span className="text-status-success mt-0.5">•</span>
                    {s}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {(opinion.concerns as string[])?.length > 0 && (
            <div>
              <h5 className={`${textStyles.label} text-status-warning mb-1 flex items-center gap-1`}>
                <AlertCircle className="w-3 h-3" />
                Pontos de Atenção
              </h5>
              <ul className="space-y-0.5">
                {(opinion.concerns as string[]).map((c: string, i: number) => (
                  <li key={`con-${i}`} className={`${textStyles.caption} text-lia-text-secondary flex items-start gap-1`}>
                    <span className="text-status-warning mt-0.5">•</span>
                    {c}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {(opinion.gaps as string[])?.length > 0 && (
            <div>
              <h5 className={`${textStyles.label} text-status-error mb-1 flex items-center gap-1`}>
                <AlertCircle className="w-3 h-3" />
                Gaps Identificados
              </h5>
              <ul className="space-y-0.5">
                {(opinion.gaps as string[]).map((g: string, i: number) => (
                  <li key={`gap-${i}`} className={`${textStyles.caption} text-lia-text-secondary flex items-start gap-1`}>
                    <span className="text-status-error mt-0.5">•</span>
                    {g}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {((opinion.matched_skills as string[])?.length > 0 || (opinion.missing_skills as string[])?.length > 0) && (
            <div className="flex gap-3">
              {(opinion.matched_skills as string[])?.length > 0 && (
                <div className="flex-1">
                  <h5 className={`${textStyles.label} text-status-success mb-1`}>Skills Match</h5>
                  <div className="flex flex-wrap gap-1">
                    {(opinion.matched_skills as string[]).map((skill: string) => (
                      <Chip variant="success" muted key={skill} className={previewChipVariants.success}>
                        {skill}
                      </Chip>
                    ))}
                  </div>
                </div>
              )}
              {(opinion.missing_skills as string[])?.length > 0 && (
                <div className="flex-1">
                  <h5 className={`${textStyles.label} text-status-error mb-1`}>Skills Faltantes</h5>
                  <div className="flex flex-wrap gap-1">
                    {(opinion.missing_skills as string[]).map((skill: string) => (
                      <Chip variant="danger" muted key={skill} className={previewChipVariants.error}>
                        {skill}
                      </Chip>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {!!opinion.next_steps && (
            <div>
              <h5 className={`${textStyles.label} mb-1 flex items-center gap-1`}>
                <TrendingUp className="w-3 h-3" />
                Próximos Passos
              </h5>
              <p className={`${textStyles.caption} text-lia-text-secondary`}>{String(opinion.next_steps)}</p>
            </div>
          )}

          {!!opinion.recruiter_notes && (
            <div className="bg-status-warning/10 rounded-xl p-2 border border-status-warning/30">
              <h5 className={`${textStyles.label} text-status-warning mb-1 flex items-center gap-1`}>
                <Edit className="w-3 h-3" />
                Notas do Recrutador
              </h5>
              <p className={`${textStyles.caption} text-status-warning`}>{String(opinion.recruiter_notes)}</p>
            </div>
          )}

          {(() => {
            const f11 = (opinion.score_breakdown as Record<string, unknown> | undefined)?.f11_report as Record<string, unknown> | undefined
            if (!f11) return null
            const flags = ((f11.attention_flags as unknown[] | undefined) || []).filter((x) => typeof x === 'string') as string[]
            const confRaw = typeof f11.decision_confidence === 'number' ? (f11.decision_confidence as number) : null
            const conf = confRaw === null ? '' : ` (${Math.round(confRaw <= 1 ? confRaw * 100 : confRaw)}%)`
            return (
              <div className="bg-lia-bg-secondary rounded-xl p-2 border border-lia-border-subtle">
                <h5 className={`${textStyles.label} mb-1 flex items-center gap-1`}>
                  <Target className="w-3 h-3 text-wedo-cyan" />
                  Relatório WSI (consultor)
                </h5>
                {!!f11.classification_label && (
                  <p className={`${textStyles.caption} text-lia-text-secondary`}>Classificação: {String(f11.classification_label)}</p>
                )}
                {!!f11.decision_result && (
                  <p className={`${textStyles.caption} text-lia-text-secondary`}>Decisão: {String(f11.decision_result)}{conf}</p>
                )}
                {!!f11.decision_reason && (
                  <p className={`${textStyles.caption} text-lia-text-secondary`}>{String(f11.decision_reason)}</p>
                )}
                {flags.length > 0 && (
                  <ul className="mt-1 space-y-0.5">
                    {flags.map((fl: string, i: number) => (
                      <li key={`flag-${i}`} className={`${textStyles.caption} text-status-warning flex items-start gap-1`}>
                        <AlertCircle className="w-3 h-3 mt-0.5" />{fl}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )
          })()}

          {!!opinion.recruiter_override && (
            <div className="bg-wedo-purple/10 rounded-xl p-2 border border-wedo-purple/30">
              <div className="flex items-center gap-2 mb-1">
                <h5 className={`${textStyles.label} text-lia-text-secondary`}>Override do Recrutador</h5>
                {getRecommendationBadge(opinion.recruiter_override as string)}
              </div>
              {!!opinion.recruiter_override_reason && (
                <p className={`${textStyles.caption} text-lia-text-secondary`}>{String(opinion.recruiter_override_reason)}</p>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
