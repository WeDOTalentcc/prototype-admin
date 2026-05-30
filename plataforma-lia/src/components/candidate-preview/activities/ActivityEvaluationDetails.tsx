"use client"
import React from"react"
import { Chip } from "@/components/ui/chip"
import { Button } from"@/components/ui/button"
import { textStyles, cardStyles, badgeStyles, formatScorePercent } from '@/lib/design-tokens'
import {
  Brain, Mic, Play, ClipboardCheck, Eye, Video
} from"lucide-react"
import { ScreeningQuestion, TranscriptionSegment } from"@/components/modals/screening-media-modal"
import type { TimelineActivity as ActivityData } from"./ActivityTimeline"

interface ActivityEvaluationDetailsProps {
  activity: ActivityData & { details: NonNullable<ActivityData['details']> }
  candidate: Record<string, unknown>
  onOpenTriagemDetails?: (candidate: Record<string, unknown>) => void
  onSetScreeningModalData: (data: {
    type: 'audio' | 'video'
    title: string
    duration: string
    mediaUrl?: string
    questions: ScreeningQuestion[]
    transcription?: TranscriptionSegment[]
    highlights?: string[]
  } | null) => void
  onSetScreeningModalOpen: (open: boolean) => void
  onSetDiscModalData: (data: Record<string, unknown>) => void
  onSetDiscModalOpen: (open: boolean) => void
  onSetBigFiveModalCandidate: (candidate: Record<string, unknown>) => void
  onSetBigFiveModalOpen: (open: boolean) => void
}

export function ActivityEvaluationDetails({
  activity,
  candidate,
  onOpenTriagemDetails,
  onSetScreeningModalData,
  onSetScreeningModalOpen,
  onSetDiscModalData,
  onSetDiscModalOpen,
  onSetBigFiveModalCandidate,
  onSetBigFiveModalOpen,
}: ActivityEvaluationDetailsProps) {
  return (
    <>
      {activity.type === 'lia-evaluation' && (
        <div className="mt-3 space-y-3">
          <div className="bg-lia-bg-primary p-3 rounded-xl border border-lia-border-subtle">
            <h5 className="text-xs font-semibold text-lia-text-primary mb-2 flex items-center gap-1">
              <Brain className="w-3 h-3 text-wedo-cyan" />
              Avaliação Automática da IA
            </h5>
            <div className="grid grid-cols-4 gap-2 mb-3">
              <div className="text-center p-2 bg-lia-bg-secondary rounded-xl">
                <p className="text-base font-bold text-lia-text-primary">{formatScorePercent(activity.details.technicalScore)}</p>
                <p className={textStyles.bodySmall}>Técnico</p>
              </div>
              <div className="text-center p-2 bg-lia-bg-secondary rounded-xl">
                <p className="text-base font-bold text-lia-text-primary">{formatScorePercent(activity.details.culturalFit)}</p>
                <p className={textStyles.bodySmall}>Fit Cultural</p>
              </div>
              <div className="text-center p-2 bg-lia-bg-secondary rounded-xl">
                <p className="text-base font-bold text-lia-text-primary">{formatScorePercent(activity.details.experience)}</p>
                <p className={textStyles.bodySmall}>Experiência</p>
              </div>
              <div className="text-center p-2 bg-lia-bg-secondary rounded-xl">
                <p className="text-base font-bold text-lia-text-primary">{formatScorePercent(activity.details.softSkills)}</p>
                <p className={textStyles.bodySmall}>Soft Skills</p>
              </div>
            </div>
            {activity.details.strengths && (
              <div className="mb-2">
                <p className="text-xs font-semibold text-lia-text-primary mb-1">Pontos Fortes</p>
                <div className="flex flex-wrap gap-1">
                  {activity.details.strengths.map((s: string, i: number) => (
                    <Chip variant="success" muted key={`str-${i}`} className="text-micro px-1.5 py-0">
                      ✓ {s}
                    </Chip>
                  ))}
                </div>
              </div>
            )}
            <div className="bg-lia-bg-secondary p-2 rounded-xl">
              <p className="text-xs font-semibold text-lia-text-primary mb-1">Recomendação</p>
              <p className="text-xs text-lia-text-secondary">{activity.details.recommendation}</p>
            </div>
          </div>
        </div>
      )}

      {activity.type === 'voice-screening' && (
        <div className="mt-3 space-y-3">
          <div className="bg-lia-bg-primary p-3 rounded-xl border border-lia-border-subtle">
            <h5 className="text-xs font-semibold text-lia-text-primary mb-2 flex items-center gap-1">
              <Mic className="w-3 h-3 text-status-error" />
              Triagem por Voz
              <Chip variant="neutral" muted className="ml-2 text-micro px-1.5 py-0">
                {activity.details.questionsAnswered}/{activity.details.totalQuestions} perguntas
              </Chip>
            </h5>
            <div className="grid grid-cols-3 gap-2 mb-3">
              <div className="text-center p-2 bg-lia-bg-secondary rounded-xl">
                <p className="text-base font-bold text-lia-text-primary">{activity.details.duration}</p>
                <p className={textStyles.bodySmall}>Duração</p>
              </div>
              <div className="text-center p-2 bg-lia-bg-secondary rounded-xl">
                <p className="text-base font-bold text-lia-text-primary">{activity.details.completionRate}%</p>
                <p className={textStyles.bodySmall}>Completude</p>
              </div>
              <div className="text-center p-2 bg-lia-bg-secondary rounded-xl">
                <p className="text-base font-bold text-lia-text-primary">{Math.round(activity.details.transcriptionConfidence * 100)}%</p>
                <p className={textStyles.bodySmall}>Confiança</p>
              </div>
            </div>
            {activity.details.highlights && (
              <div className="bg-status-success/10 border border-status-success/30 p-2 rounded-xl mb-3">
                <p className="text-xs font-semibold text-status-success mb-1">✨ Destaques</p>
                <ul className="space-y-0.5">
                  {activity.details.highlights.map((h: string, i: number) => (
                    <li key={`hl-${i}`} className="text-xs text-status-success flex items-start gap-1">
                      <span>•</span> {h}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            <div className="bg-lia-bg-secondary p-2 rounded-xl mb-3">
              <p className="text-xs font-semibold text-lia-text-primary mb-1">Impressão Geral</p>
              <p className="text-xs text-lia-text-secondary">{activity.details.overallImpression}</p>
            </div>
            <div className="flex gap-2">
              <Button
                size="sm"
                className="text-xs h-7 bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text"
                onClick={() => {
                  const questions: ScreeningQuestion[] = activity.details.questions?.map((q: Record<string, unknown>) => ({
                    id: q.id,
                    question: q.question,
                    duration: q.duration,
                    transcription: q.transcription,
                    timestamp: q.timestamp || `${q.id}:00`,
                    analysis: q.analysis
                  })) || []
                  const transcription: TranscriptionSegment[] = activity.details.questions?.map((q: Record<string, unknown>, idx: number) => ({
                    timestamp: q.timestamp || `${idx}:00`,
                    speaker: 'Candidato' as const,
                    text: q.transcription
                  })) || []
                  onSetScreeningModalData({
                    type: 'audio',
                    title: 'Triagem por Voz',
                    duration: activity.details.duration,
                    mediaUrl: activity.details.audioUrl,
                    questions,
                    transcription,
                    highlights: activity.details.highlights || [],
                  })
                  onSetScreeningModalOpen(true)
                }}
              >
                <Play className="w-3 h-3 mr-1" />
                Ouvir Triagem
              </Button>
              {onOpenTriagemDetails && (
                <Button
                  size="sm"
                  variant="outline"
                  className="text-xs h-7"
                  onClick={() => onOpenTriagemDetails(candidate)}
                >
                  <ClipboardCheck className="w-3 h-3 mr-1" />
                  Ver Avaliação
                </Button>
              )}
            </div>
          </div>
        </div>
      )}

      {activity.type === 'rubric_evaluation' && (
        <div className="mt-3 space-y-3">
          <div className={`${cardStyles.default} p-3`}>
            <h5 className={`${textStyles.label} mb-2 flex items-center gap-1`}>
              <ClipboardCheck className="w-3 h-3 text-lia-text-secondary" />
              Avaliação por Rubrica (CV vs Vaga)
              <Chip variant="neutral" muted className={`ml-2 ${activity.details.overallFit >= 80 ? badgeStyles.success : activity.details.overallFit >= 60 ? badgeStyles.warning : badgeStyles.error}`}>
                {activity.details.overallFit}% fit
              </Chip>
            </h5>
            <div className="text-center p-3 bg-gradient-to-r from-lia-bg-secondary to-lia-bg-tertiary rounded-xl border border-lia-border-subtle mb-3">
              <p className="text-3xl font-semibold text-lia-text-primary">{activity.details.overallFit}%</p>
              <p className={textStyles.caption}>Fit Geral</p>
            </div>
            {activity.details.criteriaScores && (
              <div className="space-y-1.5 mb-3">
                {activity.details.criteriaScores.slice(0, 4).map((c: Record<string, unknown>, i: number) => {
                  const cScore = Number(c.score ?? 0)
                  return (
                  <div key={i} className="flex justify-between text-xs bg-lia-bg-secondary p-1.5 rounded-xl border border-lia-border-subtle">
                    <span className="text-lia-text-primary">{String(c.criteria ?? '')}</span>
                    <Chip variant="neutral" muted className={`text-micro px-1.5 ${cScore >= 80 ? badgeStyles.success : cScore >= 60 ? badgeStyles.warning : badgeStyles.error}`}>
                      {cScore}%
                    </Chip>
                  </div>
                  )
                })}
              </div>
            )}
            <div className="bg-lia-bg-secondary p-2 rounded-xl border border-lia-border-subtle">
              <p className={`${textStyles.labelSmall} mb-1`}>💡 Recomendação</p>
              <p className={`${textStyles.caption} text-lia-text-secondary`}>{activity.details.recommendation}</p>
            </div>
          </div>
        </div>
      )}

      {activity.type === 'assessment' && (
        <div className="mt-3 space-y-3">
          <div className={`${cardStyles.default} p-3`}>
            <h5 className={`${textStyles.label} mb-2 flex items-center gap-1`}>
              <Brain className="w-3 h-3 text-wedo-cyan" />
              {activity.details.assessmentType || 'Assessment Comportamental'}
              <Chip variant="neutral" muted className={`ml-2 ${badgeStyles.primary}`}>
                {activity.details.profile}
              </Chip>
            </h5>
            <div className="text-center p-3 bg-gradient-to-r from-lia-bg-tertiary to-lia-bg-secondary rounded-xl border border-lia-border-default mb-3">
              <p className="text-xl font-semibold text-lia-text-primary">{activity.details.profile}</p>
              <p className={textStyles.caption}>{activity.details.profileDescription}</p>
            </div>
            <div className="grid grid-cols-2 gap-2 mb-3">
              <div className="bg-lia-bg-secondary p-2 rounded-xl border border-lia-border-subtle text-center">
                <p className="text-sm font-bold text-lia-text-primary">{activity.details.culturalFit || activity.details.culturalFitScore}%</p>
                <p className={textStyles.caption}>Fit Cultural</p>
              </div>
              <div className="bg-lia-bg-secondary p-2 rounded-xl border border-lia-border-subtle text-center">
                <p className="text-sm font-bold text-lia-text-primary">{activity.details.teamworkScore}%</p>
                <p className={textStyles.caption}>Trabalho em Equipe</p>
              </div>
            </div>
            {activity.details.developmentAreas && activity.details.developmentAreas.length > 0 && (
              <div className="bg-lia-bg-secondary p-2 rounded-xl border border-lia-border-subtle">
                <p className={`${textStyles.labelSmall} text-lia-text-primary mb-1`}>⚠️ Áreas de Desenvolvimento</p>
                <div className="flex flex-wrap gap-1">
                  {activity.details.developmentAreas.map((a: string, i: number) => (
                    <Chip key={`dev-${i}`} variant="neutral" className="text-micro px-1.5 py-0 bg-lia-bg-tertiary text-lia-text-secondary border-lia-border-default">
                      {a}
                    </Chip>
                  ))}
                </div>
              </div>
            )}
            <Button
              size="sm"
              variant="outline"
              className="w-full mt-3 text-xs h-7 border-lia-border-default text-lia-text-secondary hover:bg-lia-bg-secondary hover:bg-lia-interactive-hover"
              onClick={() => {
                if (activity.details.discScores) {
                  onSetDiscModalData(activity.details)
                  onSetDiscModalOpen(true)
                } else if (activity.details.bigFiveScores) {
                  onSetBigFiveModalCandidate({
                    ...candidate,
                    bigFiveScores: activity.details.bigFiveScores
                  })
                  onSetBigFiveModalOpen(true)
                }
              }}
            >
              <Eye className="w-3 h-3 mr-1" />
              Ver Relatório Completo
            </Button>
          </div>
        </div>
      )}

      {activity.type === 'video-interview' && (
        <div className="mt-3 space-y-3">
          <div className={`${cardStyles.default} p-3`}>
            <h5 className={`${textStyles.label} mb-2 flex items-center gap-1`}>
              <Video className="w-3 h-3 text-wedo-purple" />
              Entrevista em Vídeo
              <Chip variant="neutral" muted className={`ml-2 ${badgeStyles.success}`}>
                {activity.details.questionsAnswered}/{activity.details.totalQuestions} perguntas
              </Chip>
            </h5>
            <div className="grid grid-cols-3 gap-2 mb-3">
              <div className="text-center p-2 bg-lia-bg-secondary rounded-xl border border-lia-border-subtle">
                <p className="text-sm font-bold text-lia-text-primary">{activity.details.duration}</p>
                <p className={textStyles.caption}>Duração</p>
              </div>
              <div className="text-center p-2 bg-lia-bg-secondary rounded-xl border border-lia-border-subtle">
                <p className="text-sm font-bold text-lia-text-primary">{activity.details.completionRate || 100}%</p>
                <p className={textStyles.caption}>Completude</p>
              </div>
              <div className="text-center p-2 bg-lia-bg-secondary rounded-xl border border-lia-border-subtle">
                <p className="text-sm font-bold text-lia-text-primary">{Math.round((activity.details.transcriptionConfidence || 0.95) * 100)}%</p>
                <p className={textStyles.caption}>Confiança</p>
              </div>
            </div>
            {activity.details.overallImpression && (
              <div className="bg-lia-bg-secondary p-2 rounded-xl border border-lia-border-subtle mb-3">
                <p className={`${textStyles.labelSmall} mb-1`}>Impressão Geral</p>
                <p className={`${textStyles.caption} text-lia-text-secondary`}>{activity.details.overallImpression}</p>
              </div>
            )}
            <div className="flex gap-2">
              <Button
                size="sm"
                className="text-xs h-7 bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text"
                onClick={() => {
                  const questions: ScreeningQuestion[] = activity.details.questions?.map((q: Record<string, unknown>) => ({
                    id: q.id,
                    question: q.question,
                    duration: q.duration,
                    transcription: q.transcription,
                    timestamp: q.timestamp || `${q.id}:00`,
                    analysis: q.analysis
                  })) || []
                  const transcription: TranscriptionSegment[] = activity.details.questions?.map((q: Record<string, unknown>, idx: number) => ({
                    timestamp: q.timestamp || `${idx}:00`,
                    speaker: 'Candidato' as const,
                    text: q.transcription
                  })) || []
                  onSetScreeningModalData({
                    type: 'video',
                    title: 'Entrevista em Vídeo',
                    duration: activity.details.duration,
                    mediaUrl: activity.details.videoUrl,
                    questions,
                    transcription,
                    highlights: activity.details.highlights || [],
                  })
                  onSetScreeningModalOpen(true)
                }}
              >
                <Play className="w-3 h-3 mr-1" />
                Assistir Entrevista
              </Button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
