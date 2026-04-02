"use client"
import React from "react"
import { textStyles, cardStyles, badgeStyles, formatScorePercent } from '@/lib/design-tokens'
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Brain,
  Calendar, ExternalLink, CheckCircle, Mail, Download, Linkedin,
  Mic, Play, ClipboardCheck, FileText, Code, Gift, UserCheck,
  Shield, Users, Building, Clock,
  Eye, Video, Target, ThumbsUp, ThumbsDown, AlertCircle
} from "lucide-react"
import { ScreeningQuestion, TranscriptionSegment } from "@/components/modals/screening-media-modal"
import { Activity as ActivityData } from "@/data/demo-activities"

interface ActivityExpandedDetailsProps {
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
  onSetSelectedFile: (file: Record<string, unknown>) => void
  onSetPreviewType: (type: 'pdf' | 'image' | 'video' | 'audio' | null) => void
  onSetShowPreview: (show: boolean) => void
}

export function ActivityExpandedDetails({
  activity,
  candidate,
  onOpenTriagemDetails,
  onSetScreeningModalData,
  onSetScreeningModalOpen,
  onSetDiscModalData,
  onSetDiscModalOpen,
  onSetBigFiveModalCandidate,
  onSetBigFiveModalOpen,
  onSetSelectedFile,
  onSetPreviewType,
  onSetShowPreview,
}: ActivityExpandedDetailsProps) {
    return (
      <div className="px-3 pb-3 border-t border-lia-border-subtle bg-lia-bg-primary/50/50">
        {activity.type === 'email-sent' && (
          <div className="mt-3 space-y-3">
            <div className="bg-lia-bg-primary border border-lia-border-subtle rounded-md overflow-hidden">
              <div className="bg-lia-bg-secondary px-4 py-3 border-b border-lia-border-subtle">
                <div className="space-y-1.5">
                  <div className="flex items-center gap-2 text-xs">
                    <span className="text-lia-text-tertiary w-12">De:</span>
                    <span className="text-lia-text-primary font-medium">{activity.details.from}</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs">
                    <span className="text-lia-text-tertiary w-12">Para:</span>
                    <span className="text-lia-text-primary">{activity.details.to}</span>
                  </div>
                  {activity.details.cc && (
                    <div className="flex items-center gap-2 text-xs">
                      <span className="text-lia-text-tertiary w-12">Cc:</span>
                      <span className="text-lia-text-primary">{activity.details.cc}</span>
                    </div>
                  )}
                  <div className="flex items-center gap-2 text-xs">
                    <span className="text-lia-text-tertiary w-12">Assunto:</span>
                    <span className="text-lia-text-primary font-semibold">{activity.details.subject}</span>
                  </div>
                </div>
              </div>
              <div className="px-4 py-3">
                <div className="text-xs text-lia-text-primary whitespace-pre-line leading-relaxed max-h-48 overflow-y-auto">
                  {activity.details.body}
                </div>
              </div>
              {activity.details.attachments && activity.details.attachments.length > 0 && (
                <div className="px-4 py-2 bg-lia-bg-secondary border-t border-lia-border-subtle">
                  <p className="text-micro text-lia-text-tertiary mb-1">Anexos:</p>
                  <div className="flex flex-wrap gap-1">
                    {activity.details.attachments.map((att: string, i: number) => (
                      <Badge key={`att-${i}`} variant="outline" className="text-micro px-1.5 py-0 bg-lia-bg-primary">
                        📎 {att}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </div>
            {activity.details.opened && (
              <div className="flex items-center gap-2 text-xs text-status-success bg-status-success/10 p-2 rounded-md">
                <CheckCircle className="w-3 h-3" />
                <span>Email aberto em {activity.details.openedAt}</span>
              </div>
            )}
            {activity.details.suggestedTimes && (
              <div className="flex flex-wrap gap-1">
                {activity.details.suggestedTimes.map((t: string, i: number) => (
                  <Badge key={`stime-${i}`} className="text-micro px-2 py-0.5 bg-lia-bg-tertiary text-lia-text-secondary border-lia-border-subtle">
                    📅 {t}
                  </Badge>
                ))}
              </div>
            )}
          </div>
        )}

        {activity.type === 'interview-scheduled' && (
          <div className="mt-3 space-y-3">
            <div className="bg-lia-bg-primary p-3 rounded-md border border-lia-border-subtle">
              <h5 className="text-xs font-semibold text-lia-text-primary mb-2 flex items-center gap-1">
                <Calendar className="w-3 h-3 text-wedo-purple" />
                {activity.details.interviewType}
                {activity.details.stage && (
                  <Badge className="ml-2 text-micro px-1.5 py-0 bg-wedo-purple/10 text-wedo-purple">{activity.details.stage}</Badge>
                )}
              </h5>
              <div className="grid grid-cols-2 gap-2 mb-3">
                <div className="bg-lia-bg-secondary p-2 rounded-md">
                  <p className={textStyles.bodySmall}>Data e Hora</p>
                  <p className="text-xs font-semibold text-lia-text-primary">{activity.details.dateTime}</p>
                </div>
                <div className="bg-lia-bg-secondary p-2 rounded-md">
                  <p className={textStyles.bodySmall}>Duração</p>
                  <p className="text-xs font-semibold text-lia-text-primary">{activity.details.duration}</p>
                </div>
              </div>
              <div className="bg-lia-bg-secondary p-2 rounded-md mb-3">
                <p className={`${textStyles.bodySmall} mb-1`}>📍 Local</p>
                <p className="text-xs font-medium text-lia-text-primary">{activity.details.location}</p>
                {activity.details.meetLink && (
                  <a href={activity.details.meetLink} target="_blank" rel="noopener noreferrer" className="text-xs text-lia-text-secondary hover:underline flex items-center gap-1 mt-1">
                    <ExternalLink className="w-3 h-3" />
                    Acessar link da reunião
                  </a>
                )}
              </div>
              {activity.details.interviewers && (
                <div className="mb-3">
                  <p className="text-xs font-semibold text-lia-text-primary mb-1">👥 Entrevistadores</p>
                  <div className="space-y-1">
                    {activity.details.interviewers.map((int: Record<string, unknown> | string, i: number) => (
                      <div key={`int-${i}`} className="flex items-center gap-2 text-xs bg-lia-bg-secondary p-1.5 rounded-md">
                        <div className="w-5 h-5 rounded-full bg-lia-interactive-active flex items-center justify-center text-micro font-medium text-lia-text-secondary">
                          {typeof int === 'string' ? int.charAt(0) : String(int.name ?? '').charAt(0)}
                        </div>
                        <span className="font-medium text-lia-text-primary">{typeof int === 'string' ? int : String(int.name ?? '')}</span>
                        {typeof int !== 'string' && int.role ? <span className="text-lia-text-tertiary">- {String(int.role)}</span> : null}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {activity.type === 'lia-evaluation' && (
          <div className="mt-3 space-y-3">
            <div className="bg-lia-bg-primary p-3 rounded-md border border-lia-border-subtle">
              <h5 className="text-xs font-semibold text-lia-text-primary mb-2 flex items-center gap-1">
                <Brain className="w-3 h-3 text-wedo-cyan" />
                Avaliação Automática da LIA
              </h5>
              <div className="grid grid-cols-4 gap-2 mb-3">
                <div className="text-center p-2 bg-lia-bg-secondary rounded-md">
                  <p className="text-base font-bold text-lia-text-primary">{formatScorePercent(activity.details.technicalScore)}</p>
                  <p className={textStyles.bodySmall}>Técnico</p>
                </div>
                <div className="text-center p-2 bg-lia-bg-secondary rounded-md">
                  <p className="text-base font-bold text-lia-text-primary">{formatScorePercent(activity.details.culturalFit)}</p>
                  <p className={textStyles.bodySmall}>Fit Cultural</p>
                </div>
                <div className="text-center p-2 bg-lia-bg-secondary rounded-md">
                  <p className="text-base font-bold text-lia-text-primary">{formatScorePercent(activity.details.experience)}</p>
                  <p className={textStyles.bodySmall}>Experiência</p>
                </div>
                <div className="text-center p-2 bg-lia-bg-secondary rounded-md">
                  <p className="text-base font-bold text-lia-text-primary">{formatScorePercent(activity.details.softSkills)}</p>
                  <p className={textStyles.bodySmall}>Soft Skills</p>
                </div>
              </div>
              {activity.details.strengths && (
                <div className="mb-2">
                  <p className="text-xs font-semibold text-lia-text-primary mb-1">Pontos Fortes</p>
                  <div className="flex flex-wrap gap-1">
                    {activity.details.strengths.map((s: string, i: number) => (
                      <Badge key={`str-${i}`} className="text-micro px-1.5 py-0 bg-status-success/10 text-status-success border-status-success/30">
                        ✓ {s}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
              <div className="bg-lia-bg-secondary p-2 rounded-md">
                <p className="text-xs font-semibold text-lia-text-primary mb-1">Recomendação</p>
                <p className="text-xs text-lia-text-secondary">{activity.details.recommendation}</p>
              </div>
            </div>
          </div>
        )}

        {activity.type === 'job-application' && (
          <div className="mt-3 space-y-3">
            <div className="bg-lia-bg-primary p-3 rounded-md border border-lia-border-subtle">
              <h5 className="text-xs font-semibold text-lia-text-primary mb-2 flex items-center gap-1">
                <FileText className="w-3 h-3 text-status-success" />
                Candidatura Recebida
                <Badge className="ml-2 text-micro px-1.5 py-0 bg-status-success/10 text-status-success">{activity.details.source}</Badge>
              </h5>
              <div className="grid grid-cols-2 gap-2 mb-3">
                <div className="bg-lia-bg-secondary p-2 rounded-md">
                  <p className={textStyles.bodySmall}>ID da Aplicação</p>
                  <p className="text-xs font-mono font-medium text-lia-text-primary">{activity.details.applicationId}</p>
                </div>
                <div className="bg-lia-bg-secondary p-2 rounded-md">
                  <p className={textStyles.bodySmall}>Método</p>
                  <p className="text-xs font-medium text-lia-text-primary">{activity.details.applicationMethod}</p>
                </div>
                <div className="bg-lia-bg-secondary p-2 rounded-md">
                  <p className={textStyles.bodySmall}>Recebido em</p>
                  <p className="text-xs font-medium text-lia-text-primary">{activity.details.receivedAt}</p>
                </div>
                <div className="bg-lia-bg-secondary p-2 rounded-md">
                  <p className={textStyles.bodySmall}>Dispositivo</p>
                  <p className="text-xs font-medium text-lia-text-primary">{activity.details.device}</p>
                </div>
              </div>
              <div className="flex gap-2">
                <Button size="sm" variant="outline" className="text-xs h-7">
                  <Download className="w-3 h-3 mr-1" />
                  Baixar CV
                </Button>
                <Button size="sm" variant="outline" className="text-xs h-7">
                  <Linkedin className="w-3 h-3 mr-1" />
                  Ver LinkedIn
                </Button>
              </div>
            </div>
          </div>
        )}

        {activity.type === 'voice-screening' && (
          <div className="mt-3 space-y-3">
            <div className="bg-lia-bg-primary p-3 rounded-md border border-lia-border-subtle">
              <h5 className="text-xs font-semibold text-lia-text-primary mb-2 flex items-center gap-1">
                <Mic className="w-3 h-3 text-status-error" />
                Triagem por Voz
                <Badge className="ml-2 text-micro px-1.5 py-0 bg-status-success/10 text-status-success">
                  {activity.details.questionsAnswered}/{activity.details.totalQuestions} perguntas
                </Badge>
              </h5>
              <div className="grid grid-cols-3 gap-2 mb-3">
                <div className="text-center p-2 bg-lia-bg-secondary rounded-md">
                  <p className="text-base font-bold text-lia-text-primary">{activity.details.duration}</p>
                  <p className={textStyles.bodySmall}>Duração</p>
                </div>
                <div className="text-center p-2 bg-lia-bg-secondary rounded-md">
                  <p className="text-base font-bold text-lia-text-primary">{activity.details.completionRate}%</p>
                  <p className={textStyles.bodySmall}>Completude</p>
                </div>
                <div className="text-center p-2 bg-lia-bg-secondary rounded-md">
                  <p className="text-base font-bold text-lia-text-primary">{Math.round(activity.details.transcriptionConfidence * 100)}%</p>
                  <p className={textStyles.bodySmall}>Confiança</p>
                </div>
              </div>
              {activity.details.highlights && (
                <div className="bg-status-success/10 border border-status-success/30 p-2 rounded-md mb-3">
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
              <div className="bg-lia-bg-secondary p-2 rounded-md mb-3">
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

        {activity.type === 'test-completed' && (
          <div className="mt-3 space-y-3">
            <div className={`${cardStyles.default} p-3`}>
              <h5 className={`${textStyles.label} mb-2 flex items-center gap-1`}>
                <Code className="w-3 h-3 text-status-warning" />
                {activity.details.testName}
                <Badge className={`ml-2 ${(activity.score ?? 0) >= 70 ? badgeStyles.success : badgeStyles.warning}`}>
                  {(activity.score ?? 0) >= 70 ? 'Aprovado' : 'Atenção'}
                </Badge>
              </h5>
              <div className="grid grid-cols-3 gap-2 mb-3">
                <div className="text-center p-2 bg-lia-bg-secondary rounded-md border border-lia-border-subtle">
                  <p className="text-base font-bold text-lia-text-primary">{activity.details.correctAnswers}/{activity.details.totalQuestions}</p>
                  <p className={textStyles.caption}>Acertos</p>
                </div>
                <div className="text-center p-2 bg-lia-bg-secondary rounded-md border border-lia-border-subtle">
                  <p className="text-base font-bold text-lia-text-primary">{activity.details.timeSpent}</p>
                  <p className={textStyles.caption}>Tempo</p>
                </div>
                <div className={`text-center p-2 rounded-md border ${(activity.score ?? 0) >= 80 ? 'bg-status-success/10 border-status-success/30 dark:bg-status-success/20 dark:border-status-success/30' : (activity.score ?? 0) >= 60 ? 'bg-lia-bg-secondary border-lia-border-subtle' : 'bg-lia-bg-tertiary border-lia-border-default'}`}>
                  <p className={`text-base font-bold ${(activity.score ?? 0) >= 80 ? 'text-status-success' : (activity.score ?? 0) >= 60 ? 'text-lia-text-primary' : 'text-lia-text-tertiary'}`}>{activity.score}%</p>
                  <p className={textStyles.caption}>Score</p>
                </div>
              </div>
              {activity.details.categories && (
                <div className="mb-3">
                  <p className={`${textStyles.labelSmall} mb-2`}>📊 Performance por Categoria</p>
                  <div className="space-y-1.5">
                    {activity.details.categories.map((cat: Record<string, unknown>, i: number) => {
                      const catScore = Number(cat.score ?? 0)
                      return (
                      <div key={i} className="flex items-center gap-2">
                        <span className={`${textStyles.caption} w-28 truncate`}>{String(cat.name ?? '')}</span>
                        <div className="flex-1 bg-lia-bg-tertiary h-2 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full ${catScore >= 80 ? 'bg-status-success' : catScore >= 60 ? 'bg-status-success/60' : 'bg-lia-border-default'}`}
                            style={{width: `${catScore}%`}}
                          />
                        </div>
                        <span className="text-xs font-medium text-lia-text-primary w-8 text-right">{catScore}%</span>
                      </div>
                      )
                    })}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {activity.type === 'offer-sent' && (
          <div className="mt-3 space-y-3">
            <div className={`${cardStyles.default} p-3`}>
              <h5 className={`${textStyles.label} mb-2 flex items-center gap-1`}>
                <Gift className="w-3 h-3 text-lia-text-secondary" />
                Proposta Salarial
                <Badge className={`ml-2 ${badgeStyles.primary}`}>
                  {activity.statusLabel || 'Enviada'}
                </Badge>
              </h5>
              <div className="text-center p-3 bg-gradient-to-r from-lia-bg-secondary to-lia-bg-tertiary rounded-md border border-lia-border-subtle mb-3">
                <p className="text-2xl font-bold text-lia-text-primary">{activity.details.salary}</p>
                {activity.details.annualBonus && (
                  <p className="text-xs text-lia-text-secondary">+ Bônus: {activity.details.annualBonus}</p>
                )}
              </div>
              <div className="grid grid-cols-2 gap-2 mb-3">
                <div className="bg-lia-bg-secondary p-2 rounded-md">
                  <p className={textStyles.bodySmall}>Data de Início</p>
                  <p className="text-xs font-semibold text-lia-text-primary">{activity.details.startDate}</p>
                </div>
                <div className="bg-lia-bg-secondary p-2 rounded-md">
                  <p className={textStyles.bodySmall}>Contrato</p>
                  <p className="text-xs font-semibold text-lia-text-primary">{activity.details.contractType}</p>
                </div>
              </div>
              {activity.details.benefits && (
                <div className="flex flex-wrap gap-1">
                  {activity.details.benefits.map((b: Record<string, unknown> | string, i: number) => (
                    <Badge key={`ben-${i}`} variant="outline" className="text-micro px-1.5 py-0">
                      {typeof b === 'object' ? String(b.name ?? '') : String(b)}
                    </Badge>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {activity.type === 'rubric_evaluation' && (
          <div className="mt-3 space-y-3">
            <div className={`${cardStyles.default} p-3`}>
              <h5 className={`${textStyles.label} mb-2 flex items-center gap-1`}>
                <ClipboardCheck className="w-3 h-3 text-lia-text-secondary" />
                Avaliação por Rubrica (CV vs Vaga)
                <Badge className={`ml-2 ${activity.details.overallFit >= 80 ? badgeStyles.success : activity.details.overallFit >= 60 ? badgeStyles.warning : badgeStyles.error}`}>
                  {activity.details.overallFit}% fit
                </Badge>
              </h5>
              <div className="text-center p-3 bg-gradient-to-r from-lia-bg-secondary to-lia-bg-tertiary rounded-md border border-lia-border-subtle mb-3">
                <p className="text-3xl font-bold text-lia-text-primary">{activity.details.overallFit}%</p>
                <p className={textStyles.caption}>Fit Geral</p>
              </div>
              {activity.details.criteriaScores && (
                <div className="space-y-1.5 mb-3">
                  {activity.details.criteriaScores.slice(0, 4).map((c: Record<string, unknown>, i: number) => {
                    const cScore = Number(c.score ?? 0)
                    return (
                    <div key={i} className="flex justify-between text-xs bg-lia-bg-secondary p-1.5 rounded-md border border-lia-border-subtle">
                      <span className="text-lia-text-primary">{String(c.criteria ?? '')}</span>
                      <Badge className={`text-micro px-1.5 ${cScore >= 80 ? badgeStyles.success : cScore >= 60 ? badgeStyles.warning : badgeStyles.error}`}>
                        {cScore}%
                      </Badge>
                    </div>
                    )
                  })}
                </div>
              )}
              <div className="bg-lia-bg-secondary p-2 rounded-md border border-lia-border-subtle">
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
                <Badge className={`ml-2 ${badgeStyles.primary}`}>
                  {activity.details.profile}
                </Badge>
              </h5>
              <div className="text-center p-3 bg-gradient-to-r from-lia-bg-tertiary to-lia-bg-secondary rounded-md border border-lia-border-default mb-3">
                <p className="text-xl font-bold text-lia-text-primary">{activity.details.profile}</p>
                <p className={textStyles.caption}>{activity.details.profileDescription}</p>
              </div>
              <div className="grid grid-cols-2 gap-2 mb-3">
                <div className="bg-lia-bg-secondary p-2 rounded-md border border-lia-border-subtle text-center">
                  <p className="text-sm font-bold text-lia-text-primary">{activity.details.culturalFit || activity.details.culturalFitScore}%</p>
                  <p className={textStyles.caption}>Fit Cultural</p>
                </div>
                <div className="bg-lia-bg-secondary p-2 rounded-md border border-lia-border-subtle text-center">
                  <p className="text-sm font-bold text-lia-text-primary">{activity.details.teamworkScore}%</p>
                  <p className={textStyles.caption}>Trabalho em Equipe</p>
                </div>
              </div>
              {activity.details.developmentAreas && activity.details.developmentAreas.length > 0 && (
                <div className="bg-lia-bg-secondary p-2 rounded-md border border-lia-border-subtle">
                  <p className={`${textStyles.labelSmall} text-lia-text-primary mb-1`}>⚠️ Áreas de Desenvolvimento</p>
                  <div className="flex flex-wrap gap-1">
                    {activity.details.developmentAreas.map((a: string, i: number) => (
                      <Badge key={`dev-${i}`} variant="outline" className="text-micro px-1.5 py-0 bg-lia-bg-tertiary text-lia-text-secondary border-lia-border-default">
                        {a}
                      </Badge>
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
                <Badge className={`ml-2 ${badgeStyles.success}`}>
                  {activity.details.questionsAnswered}/{activity.details.totalQuestions} perguntas
                </Badge>
              </h5>
              <div className="grid grid-cols-3 gap-2 mb-3">
                <div className="text-center p-2 bg-lia-bg-secondary rounded-md border border-lia-border-subtle">
                  <p className="text-sm font-bold text-lia-text-primary">{activity.details.duration}</p>
                  <p className={textStyles.caption}>Duração</p>
                </div>
                <div className="text-center p-2 bg-lia-bg-secondary rounded-md border border-lia-border-subtle">
                  <p className="text-sm font-bold text-lia-text-primary">{activity.details.completionRate || 100}%</p>
                  <p className={textStyles.caption}>Completude</p>
                </div>
                <div className="text-center p-2 bg-lia-bg-secondary rounded-md border border-lia-border-subtle">
                  <p className="text-sm font-bold text-lia-text-primary">{Math.round((activity.details.transcriptionConfidence || 0.95) * 100)}%</p>
                  <p className={textStyles.caption}>Confiança</p>
                </div>
              </div>
              {activity.details.overallImpression && (
                <div className="bg-lia-bg-secondary p-2 rounded-md border border-lia-border-subtle mb-3">
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

        {activity.type === 'technical-test' && (
          <div className="mt-2 space-y-2">
            <div className="bg-lia-bg-primary p-2 rounded-md">
              <p className={`${textStyles.bodySmall} mb-1`}>Teste Técnico</p>
              <div className="grid grid-cols-2 gap-1">
                <div>
                  <p className={textStyles.bodySmall}>Tipo</p>
                  <p className={`${textStyles.label}`}>{activity.details.testType}</p>
                </div>
                <div>
                  <p className={textStyles.bodySmall}>Duração</p>
                  <p className={`${textStyles.label}`}>{activity.details.duration}</p>
                </div>
                <div>
                  <p className={textStyles.bodySmall}>Score</p>
                  <p className={`${textStyles.label}`}>{activity.details.score}/{activity.details.maxScore}</p>
                </div>
                <div>
                  <p className={textStyles.bodySmall}>Evaluador</p>
                  <p className={`${textStyles.label}`}>{activity.details.evaluator}</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {activity.type === 'english-test' && (
          <div className="mt-2 space-y-2">
            <div className="bg-lia-bg-primary p-2 rounded-md">
              <p className={`${textStyles.bodySmall} mb-1`}>Teste de Inglês</p>
              <div className="grid grid-cols-2 gap-1">
                <div>
                  <p className={textStyles.bodySmall}>Nível</p>
                  <p className={`${textStyles.label}`}>{activity.details.level}</p>
                </div>
                <div>
                  <p className={textStyles.bodySmall}>Score CEFR</p>
                  <p className={`${textStyles.label}`}>{activity.details.score}</p>
                </div>
                <div>
                  <p className={textStyles.bodySmall}>Certificação</p>
                  <p className={`${textStyles.label}`}>{activity.details.certification}</p>
                </div>
                <div>
                  <p className={textStyles.bodySmall}>Válido até</p>
                  <p className={`${textStyles.label}`}>{activity.details.validUntil}</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {activity.type === 'data-collection' && (
          <div className="mt-2 space-y-2">
            <div className="bg-lia-bg-primary p-2 rounded-md">
              <p className={`${textStyles.bodySmall} mb-1`}>Coleta de Dados</p>
              <div className="grid grid-cols-2 gap-1">
                <div>
                  <p className={textStyles.bodySmall}>Documentos Verificados</p>
                  <div className="flex flex-wrap gap-1">
                    {activity.details.documentsVerified?.map((doc: string) => (
                      <Badge key={doc} variant="outline" className="text-xs px-1.5 py-0">
                        {doc}
                      </Badge>
                    ))}
                  </div>
                </div>
                <div>
                  <p className={textStyles.bodySmall}>Referências</p>
                  <p className={`${textStyles.label}`}>{activity.details.referencesChecked}</p>
                </div>
                <div>
                  <p className={textStyles.bodySmall}>Verificação</p>
                  <p className={`${textStyles.label}`}>{activity.details.backgroundCheck}</p>
                </div>
                <div>
                  <p className={textStyles.bodySmall}>Completeness</p>
                  <p className={`${textStyles.label}`}>{activity.details.dataCompleteness}</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {activity.type === 'onboarding' && (
          <div className="mt-3 space-y-3">
            <div className="bg-lia-bg-primary p-3 rounded-md">
              <h5 className="text-xs font-semibold text-lia-text-primary mb-2 flex items-center gap-1">
                <UserCheck className="w-3 h-3 text-lia-text-primary" />
                Processo de Onboarding
              </h5>
              <div className="bg-status-success/10 p-2 rounded-md mb-3">
                <p className="text-xs font-semibold text-lia-text-primary mb-2">📋 Checklist de Integração</p>
                <div className="space-y-1">
                  <div className="flex items-center gap-2 text-xs">
                    <CheckCircle className="w-3 h-3 text-lia-text-primary" />
                    <span className="text-lia-text-primary">Oferta aceita e assinada</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs">
                    <CheckCircle className="w-3 h-3 text-lia-text-primary" />
                    <span className="text-lia-text-primary">Documentação enviada</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs">
                    <Clock className="w-3 h-3 text-lia-text-secondary" />
                    <span className="text-lia-text-primary">Equipamentos solicitados</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs">
                    <Clock className="w-3 h-3 text-lia-text-secondary" />
                    <span className="text-lia-text-primary">Acessos em configuração</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs">
                    <AlertCircle className="w-3 h-3 text-lia-text-secondary" />
                    <span className="text-lia-text-primary">Buddy designado (pendente)</span>
                  </div>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-2 mb-3">
                <div className="bg-lia-bg-primary p-2 rounded-md">
                  <p className={`${textStyles.bodySmall} mb-1`}>Data de Início</p>
                  <p className="text-xs font-semibold text-lia-text-primary">{activity.details.startDate}</p>
                  <p className={textStyles.bodySmall}>Segunda-feira</p>
                </div>
                <div className="bg-lia-bg-primary p-2 rounded-md">
                  <p className={`${textStyles.bodySmall} mb-1`}>Gestor Responsável</p>
                  <p className="text-xs font-semibold text-lia-text-primary">{activity.details.onboardingManager}</p>
                  <p className={textStyles.bodySmall}>People & Culture</p>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div className="text-center p-2 bg-lia-bg-primary rounded-md">
                  <FileText className="w-4 h-4 mx-auto text-lia-text-primary mb-1" />
                  <p className={textStyles.bodySmall}>Documentos</p>
                  <p className="text-xs font-semibold text-lia-text-primary">{activity.details.documentsStatus}</p>
                </div>
                <div className="text-center p-2 bg-lia-bg-primary rounded-md">
                  <Building className="w-4 h-4 mx-auto text-lia-text-secondary mb-1" />
                  <p className={textStyles.bodySmall}>Equipamentos</p>
                  <p className="text-xs font-semibold text-lia-text-primary">{activity.details.equipmentStatus}</p>
                </div>
                <div className="text-center p-2 bg-lia-bg-primary rounded-md">
                  <Shield className="w-4 h-4 mx-auto text-lia-text-primary mb-1" />
                  <p className={textStyles.bodySmall}>Acessos</p>
                  <p className="text-xs font-semibold text-lia-text-primary">{activity.details.accessesStatus}</p>
                </div>
                <div className="text-center p-2 bg-lia-bg-primary rounded-md">
                  <Users className="w-4 h-4 mx-auto text-lia-text-primary mb-1" />
                  <p className={textStyles.bodySmall}>Buddy</p>
                  <p className="text-xs font-semibold text-lia-text-primary">A definir</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {activity.type === 'interview-note' && (
          <div className="mt-2 space-y-2">
            {activity.details.technicalQuestions && (
              <div className="bg-lia-bg-primary p-2 rounded-md">
                <p className={`${textStyles.bodySmall} mb-1`}>Questões Técnicas</p>
                <div className="space-y-1">
                  {activity.details.technicalQuestions.map((q: Record<string, unknown>, i: number) => (
                    <div key={i} className="flex items-center justify-between">
                      <span className={textStyles.bodySmall}>{String(q.question ?? '')}</span>
                      <Badge className="text-xs px-1 py-0">{String(q.score ?? 0)}/10</Badge>
                    </div>
                  ))}
                </div>
              </div>
            )}
            {activity.details.overallScore && (
              <div className="bg-lia-bg-primary p-2 rounded-md">
                <div className="flex items-center justify-between">
                  <span className={textStyles.bodySmall}>Score Geral</span>
                  <span className="text-xs font-bold text-lia-text-primary">{activity.details.overallScore}/10</span>
                </div>
                <p className={`${textStyles.bodySmall} mt-1`}>{activity.details.recommendation}</p>
              </div>
            )}
          </div>
        )}

        {activity.type === 'lia-screening' && activity.details.conversation && (
          <div className="mt-2 space-y-2">
            <div className="bg-lia-bg-primary p-2 rounded-md max-h-48 overflow-y-auto">
              <p className="text-xs text-lia-text-primary mb-2">{activity.platform}</p>
              <div className="space-y-2">
                {activity.details.conversation.map((msg: Record<string, unknown>, i: number) => (
                  <div key={i} className={`flex ${String(msg.sender) === 'LIA' ? 'justify-start' : 'justify-end'}`}>
                    <div className={`max-w-[70%] px-2 py-1 rounded-md ${String(msg.sender) === 'LIA' ? 'bg-lia-bg-tertiary text-lia-text-primary' : 'bg-lia-bg-secondary text-lia-text-primary'}`}>
                      <p className="text-xs">{String(msg.message ?? '')}</p>
                      <span className="text-xs opacity-70">{String(msg.time ?? '')}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            {activity.details.keyPoints && (
              <div className="bg-lia-bg-primary p-2 rounded-md">
                <p className={`${textStyles.bodySmall} mb-1`}>Pontos-Chave</p>
                <div className="space-y-0.5">
                  <div className="flex justify-between text-xs">
                    <span className="text-lia-text-secondary">Disponibilidade:</span>
                    <span className="text-lia-text-primary">{activity.details.keyPoints.availability}</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-lia-text-secondary">Pretensão:</span>
                    <span className="text-lia-text-primary">{activity.details.keyPoints.salary}</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-lia-text-secondary">Inglês:</span>
                    <span className="text-lia-text-primary">{activity.details.keyPoints.english}</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {(activity.type === 'email-sent' || activity.type === 'email-received') && activity.details.subject && !activity.details.from?.includes('@') && (
          <div className="mt-3 space-y-3">
            <div className="bg-lia-bg-primary p-3 rounded-md">
              <div className="flex items-center justify-between mb-2">
                <h5 className="text-xs font-semibold text-lia-text-primary flex items-center gap-1">
                  <Mail className="w-3 h-3 text-lia-text-primary" />
                  {activity.type === 'email-sent' ? 'Email Enviado' : 'Email Recebido'}
                </h5>
                {activity.details.opened && (
                  <Badge className="text-xs px-1.5 py-0.5 bg-lia-bg-tertiary text-lia-text-primary">
                    ✓ Lido
                  </Badge>
                )}
              </div>
              <div className="bg-lia-bg-primary p-2 rounded-md mb-2 text-xs space-y-1">
                <div className="flex items-center gap-2">
                  <span className="text-lia-text-primary font-medium">De:</span>
                  <span className="text-lia-text-primary">
                    {activity.type === 'email-sent' ? activity.author : activity.details.from}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-lia-text-primary font-medium">Para:</span>
                  <span className="text-lia-text-primary">
                    {activity.type === 'email-sent' ? activity.details.to : activity.author}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-lia-text-primary font-medium">Data:</span>
                  <span className="text-lia-text-primary">{activity.date}</span>
                </div>
              </div>
              <p className="text-xs font-semibold text-lia-text-primary mb-2">{activity.details.subject}</p>
              <div className="text-xs text-lia-text-primary space-y-2">
                {activity.details.body ? (
                  <>
                    <p>{activity.details.body}</p>
                    {activity.details.attachments && (
                      <div className="mt-2 pt-2 border-t">
                        <p className={`${textStyles.bodySmall} mb-1`}>📎 Anexos:</p>
                        <div className="flex flex-wrap gap-1">
                          {activity.details.attachments.map((file: string, i: number) => (
                            <Badge key={`file-${i}`} variant="outline" className="text-xs px-1.5 py-0.5">
                              {file}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}
                  </>
                ) : (
                  <p className="text-lia-text-secondary italic">Conteúdo do email não disponível</p>
                )}
              </div>
              {activity.details.opened && (
                <div className="mt-2 flex items-center gap-2 text-xs text-lia-text-primary">
                  <CheckCircle className="w-3 h-3" />
                  <span>Email aberto {activity.details.openedAt}</span>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    )
}
