"use client"

import React from"react"
import { Chip } from "@/components/ui/chip"
import { Button } from"@/components/ui/button"
import { Mic, Play, ClipboardCheck, Video } from"lucide-react"
import { textStyles, cardStyles } from '@/lib/design-tokens'
import type { ScreeningQuestion, TranscriptionSegment } from"@/components/modals/screening-media-modal"
import type { TimelineActivity as ActivityData } from"./ActivityTimeline"

interface ActivityScreeningDetailsProps {
  activity: ActivityData & { details: NonNullable<ActivityData['details']> }
  candidate: Record<string, unknown>
  onOpenTriagemDetails?: (candidate: Record<string, unknown>) => void
  onSetScreeningModalData: (data: {
    type: 'audio' | 'video'; title: string; duration: string; mediaUrl?: string
    questions: ScreeningQuestion[]; transcription?: TranscriptionSegment[]; highlights?: string[]
  } | null) => void
  onSetScreeningModalOpen: (open: boolean) => void
}

export function ActivityVoiceScreeningDetails({ activity, candidate, onOpenTriagemDetails, onSetScreeningModalData, onSetScreeningModalOpen }: ActivityScreeningDetailsProps) {
  return (
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
                <li key={`hl-${i}`} className="text-xs text-status-success flex items-start gap-1"><span>•</span> {h}</li>
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
                id: q.id, question: q.question, duration: q.duration, transcription: q.transcription,
                timestamp: q.timestamp || `${q.id}:00`, analysis: q.analysis
              })) || []
              const transcription: TranscriptionSegment[] = activity.details.questions?.map((q: Record<string, unknown>, idx: number) => ({
                timestamp: q.timestamp || `${idx}:00`, speaker: 'Candidato' as const, text: q.transcription
              })) || []
              onSetScreeningModalData({
                type: 'audio', title: 'Triagem por Voz', duration: activity.details.duration,
                mediaUrl: activity.details.audioUrl, questions, transcription, highlights: activity.details.highlights || [],
              })
              onSetScreeningModalOpen(true)
            }}
          >
            <Play className="w-3 h-3 mr-1" />Ouvir Triagem
          </Button>
          {onOpenTriagemDetails && (
            <Button size="sm" variant="outline" className="text-xs h-7" onClick={() => onOpenTriagemDetails(candidate)}>
              <ClipboardCheck className="w-3 h-3 mr-1" />Ver Avaliação
            </Button>
          )}
        </div>
      </div>
    </div>
  )
}

export function ActivityVideoInterviewDetails({ activity, onSetScreeningModalData, onSetScreeningModalOpen }: Omit<ActivityScreeningDetailsProps, 'candidate' | 'onOpenTriagemDetails'>) {
  return (
    <div className="mt-3 space-y-3">
      <div className={`${cardStyles.default} p-3`}>
        <h5 className={`${textStyles.label} mb-2 flex items-center gap-1`}>
          <Video className="w-3 h-3 text-wedo-purple" />
          Entrevista em Vídeo
          <Chip variant="success" muted className="ml-2">
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
                id: q.id, question: q.question, duration: q.duration, transcription: q.transcription,
                timestamp: q.timestamp || `${q.id}:00`, analysis: q.analysis
              })) || []
              const transcription: TranscriptionSegment[] = activity.details.questions?.map((q: Record<string, unknown>, idx: number) => ({
                timestamp: q.timestamp || `${idx}:00`, speaker: 'Candidato' as const, text: q.transcription
              })) || []
              onSetScreeningModalData({
                type: 'video', title: 'Entrevista em Vídeo', duration: activity.details.duration,
                mediaUrl: activity.details.videoUrl, questions, transcription, highlights: activity.details.highlights || [],
              })
              onSetScreeningModalOpen(true)
            }}
          >
            <Play className="w-3 h-3 mr-1" />Assistir Entrevista
          </Button>
        </div>
      </div>
    </div>
  )
}
