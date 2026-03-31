// @ts-nocheck
"use client"

import React from "react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator
} from "@/components/ui/dropdown-menu"
import { InteractiveSubStatusCell } from "@/components/tables"
import {
  DataRequestIndicator,
} from "@/components/ui/data-request-indicator"
import {
  Brain, Target, Code, Globe, Fingerprint, Gauge,
  ThumbsUp, XCircle, Flag, Eye, ChevronDown, CheckCircle,
  MoreVertical, Video, Copy, BrainCircuit,
} from "lucide-react"
import { textStyles, badgeStyles, formatScorePercent } from "@/lib/design-tokens"
import { getUrgencyLevel } from "@/components/kanban/utils/status-utils"

type QueryInsight = {
  match_level?: string
  subquery?: string
}

type KanbanCandidate = {
  id: string
  name: string
  stage?: string
  etapa?: string
  stageId?: string
  candidateCode?: string
  score?: number | null
  liaScore?: number | null
  skillsMatch?: number | null
  fitScore?: number | null
  technicalTestScore?: number | null
  englishTestScore?: number | null
  bigFive?: Record<string, number> | null
  bigFiveScores?: Record<string, number> | null
  agendada?: string | boolean
  interviewDate?: string
  status?: string
  sub_status?: string
  needsAction?: boolean
  avatar?: string
  role?: string
  position?: string
  currentCompany?: string
  source?: string
  isDemo?: boolean
  is_opentowork?: boolean
  is_open_to_work?: boolean
  is_decision_maker?: boolean
  is_top_universities?: boolean
  is_hiring?: boolean
  headline?: string
  expertise?: string | string[]
  linkedin_followers_count?: number
  linkedin_connections_count?: number
  outreach_message?: string
  best_personal_email?: string
  phone_types?: Record<string, boolean>
  estimated_age?: number
  pearch_insights?: {
    overall_summary?: string
    query_insights?: QueryInsight[]
    match_reasoning?: string
  }
  middle_name?: string
  best_business_email?: string
  personal_emails?: string[]
  business_emails?: string[]
  company_followers_count?: number
  company_keywords?: string[]
  liaAnalysis?: unknown
  cvAnalysis?: unknown
  triagemHistory?: unknown
  screeningHistory?: unknown
  [key: string]: unknown
}

interface DynamicStageItem {
  id: string
  name: string
  displayName: string
  color?: string
}

export interface KanbanTableCellRendererProps {
  dynamicStages: DynamicStageItem[]
  jobVacancyId?: string
  viewedCandidateIds: Set<string>
  calculateNotaLiaGeral: (candidate: KanbanCandidate) => number | null
  getLiaAlerts: (candidate: KanbanCandidate) => Record<string, unknown>[]
  getDataRequestForCandidate: (candidateId: string) => Record<string, unknown> | null | undefined
  onDataRequestResend: (candidateId: string) => void
  onDataRequestViewDetails: (candidateId: string) => void
  onOpenTriagem: (candidate: KanbanCandidate) => void
  onOpenAnalysis: (candidate: KanbanCandidate) => void
  onSetSelectedCandidateForModal: (candidate: KanbanCandidate) => void
  onSetActiveModal: (modal: string) => void
  onSetShowBigFiveModal: (show: boolean) => void
  onSetScoreModalCandidate: (candidate: KanbanCandidate) => void
  onApproveFromScreening: (candidate: KanbanCandidate) => void
  onRejectFromScreening: (candidate: KanbanCandidate) => void
  onApproveCandidate: (candidate: KanbanCandidate) => void
  onRejectCandidate: (candidate: KanbanCandidate) => void
  openDecisionFlowModal: (candidate: KanbanCandidate, action: "approve" | "reject") => void
  onSetTransitionInitialPrompt: (prompt: string) => void
  onSetTransitionAllowStageSelection: (allow: boolean) => void
  onSetTransitionInterviewAlert: (alert: { name: string; date: string }) => void
  openTransition: (candidates: KanbanCandidate[], fromStage: string, toStage: string) => void
  onTransitionRequired: (candidates: KanbanCandidate[], fromStage: string, toStage: string) => void
  onStatusChange: (candidateId: string, newSubStatus: string, stage: string, jobVacancyId?: string) => Promise<boolean>
  onCandidateClick: (candidate: KanbanCandidate) => void
}

export function createKanbanCellRenderer(props: KanbanTableCellRendererProps) {
  const {
    dynamicStages,
    jobVacancyId,
    viewedCandidateIds,
    calculateNotaLiaGeral,
    getLiaAlerts,
    getDataRequestForCandidate,
    onDataRequestResend,
    onDataRequestViewDetails,
    onOpenTriagem,
    onOpenAnalysis,
    onSetSelectedCandidateForModal,
    onSetActiveModal,
    onSetShowBigFiveModal,
    onSetScoreModalCandidate,
    onApproveFromScreening,
    onRejectFromScreening,
    onApproveCandidate,
    onRejectCandidate,
    openDecisionFlowModal,
    onSetTransitionInitialPrompt,
    onSetTransitionAllowStageSelection,
    onSetTransitionInterviewAlert,
    openTransition,
    onTransitionRequired,
    onStatusChange,
    onCandidateClick,
  } = props

  return function renderCustomCell(candidate: KanbanCandidate, columnId: string): React.ReactNode {
const ranking = calculateNotaLiaGeral(candidate)
const alerts = getLiaAlerts(candidate)
const urgency = getUrgencyLevel(ranking as number)

switch (columnId) {
  case 'id':
    return (
      <div className="text-xs font-mono text-lia-text-secondary dark:text-lia-text-tertiary">
        {(candidate.candidateCode as string | undefined) || (candidate.id as string | undefined)?.substring(0, 6).toUpperCase()}
      </div>
    )

  case 'score':
    const hasNotaGeral = ranking !== null && ranking !== undefined && ranking > 0
    return (
      <div
        className={`flex items-center gap-1 justify-center cursor-pointer group ${hasNotaGeral ? '' : 'opacity-40'}`}
        onClick={(e) => {
          e.stopPropagation()
          if (hasNotaGeral) {
            onSetSelectedCandidateForModal(candidate)
            onSetActiveModal('notaGeral')
          }
        }}
        title={hasNotaGeral ? 'Clique para ver detalhes' : 'Não avaliado'}
      >
        <Gauge className="w-3.5 h-3.5" style={{color: hasNotaGeral ? 'var(--gray-950)' : 'var(--gray-400)'}} strokeWidth={2} />
 <span className={`text-xs font-semibold ${hasNotaGeral ? 'text-lia-text-primary' : 'text-lia-text-disabled dark:text-lia-text-tertiary'}`}>
          {hasNotaGeral ? ranking : '—'}
        </span>
      </div>
    )

  case 'liaScore':
    const hasTriagem = (candidate.liaScore !== null && candidate.liaScore !== undefined) || (candidate.score !== null && candidate.score !== undefined)
    const triagemValue = candidate.liaScore ?? candidate.score
    return (
      <div
        className={`flex items-center gap-1 justify-center cursor-pointer group ${hasTriagem ? '' : 'opacity-40'}`}
        onClick={(e) => {
          e.stopPropagation()
          if (hasTriagem) {
            onOpenTriagem(candidate)
          }
        }}
        title={hasTriagem ? 'Clique para ver Triagem LIA' : 'Não avaliado'}
      >
        <Brain className={`w-3.5 h-3.5 ${hasTriagem ? 'text-wedo-cyan' : 'text-lia-text-disabled'}`} strokeWidth={2} />
 <span className={`text-xs font-semibold ${hasTriagem ? 'text-lia-text-primary' : 'text-lia-text-disabled dark:text-lia-text-tertiary'}`}>
          {hasTriagem ? formatScorePercent(triagemValue as number, 0) : '—'}
        </span>
      </div>
    )

  case 'fitScore':
    const hasFitScore = (candidate.skillsMatch !== null && candidate.skillsMatch !== undefined && (candidate.skillsMatch as number) > 0) || (candidate.fitScore !== null && candidate.fitScore !== undefined && (candidate.fitScore as number) > 0)
    const fitValue = candidate.skillsMatch || candidate.fitScore || 0
    return (
      <div
        className={`flex items-center gap-1 justify-center cursor-pointer group ${hasFitScore ? '' : 'opacity-40'}`}
        onClick={(e) => {
          e.stopPropagation()
          if (hasFitScore) {
            onOpenAnalysis(candidate)
          }
        }}
        title={hasFitScore ? 'Clique para ver Análise CV vs Vaga' : 'Não avaliado'}
      >
        <Target className="w-3.5 h-3.5" style={{color: hasFitScore ? 'var(--gray-950)' : 'var(--gray-400)'}} strokeWidth={2} />
 <span className={`text-xs font-semibold ${hasFitScore ? 'text-lia-text-primary' : 'text-lia-text-disabled dark:text-lia-text-tertiary'}`}>
          {hasFitScore ? formatScorePercent(fitValue as number, 0) : '—'}
        </span>
      </div>
    )

  case 'technicalTestScore':
    const hasTechnical = candidate.technicalTestScore !== null && candidate.technicalTestScore !== undefined
    return (
      <div
        className={`flex items-center gap-1 justify-center cursor-pointer group ${hasTechnical ? '' : 'opacity-40'}`}
        onClick={(e) => {
          e.stopPropagation()
          if (hasTechnical) {
            onSetSelectedCandidateForModal(candidate)
            onSetActiveModal('testeTecnico')
          }
        }}
        title={hasTechnical ? 'Clique para ver detalhes' : 'Não realizado'}
      >
        <Code className="w-3.5 h-3.5" style={{color: hasTechnical ? 'var(--gray-600)' : 'var(--gray-400)'}} strokeWidth={2} />
        {hasTechnical && (
          <span className="text-xs font-semibold text-lia-text-primary dark:text-lia-text-primary">
            {formatScorePercent(candidate.technicalTestScore as number, 0)}
          </span>
        )}
      </div>
    )

  case 'englishTestScore':
    const hasEnglish = candidate.englishTestScore !== null && candidate.englishTestScore !== undefined
    return (
      <div
        className={`flex items-center gap-1 justify-center cursor-pointer group ${hasEnglish ? '' : 'opacity-40'}`}
        onClick={(e) => {
          e.stopPropagation()
          if (hasEnglish) {
            onSetSelectedCandidateForModal(candidate)
            onSetActiveModal('testeIngles')
          }
        }}
        title={hasEnglish ? 'Clique para ver detalhes' : 'Não realizado'}
      >
        <Globe className="w-3.5 h-3.5" style={{color: hasEnglish ? 'var(--gray-600)' : 'var(--gray-400)'}} strokeWidth={2} />
        {hasEnglish && (
          <span className="text-xs font-semibold text-lia-text-primary dark:text-lia-text-primary">
            {formatScorePercent(candidate.englishTestScore as number, 0)}
          </span>
        )}
      </div>
    )

  case 'bigFive':
    const hasBigFive = candidate.bigFive || candidate.bigFiveScores
    const bigFiveData = candidate.bigFive || candidate.bigFiveScores || {}
    const bigFiveValues = Object.values(bigFiveData).filter((v): v is number => typeof v === 'number')
    const bigFiveAvg = bigFiveValues.length > 0 ? Math.round(bigFiveValues.reduce((a, b) => a + b, 0) / bigFiveValues.length) : null
    return (
      <div
        className={`flex items-center gap-1 justify-center cursor-pointer group ${hasBigFive ? '' : 'opacity-40'}`}
        onClick={(e) => {
          e.stopPropagation()
          if (hasBigFive) {
            onSetSelectedCandidateForModal(candidate)
            onSetShowBigFiveModal(true)
          }
        }}
        title={hasBigFive ? 'Clique para ver relatório Big Five completo' : 'Não realizado'}
      >
        <Fingerprint className="w-3.5 h-3.5" style={{color: hasBigFive ? 'var(--gray-600)' : 'var(--gray-400)'}} strokeWidth={2} />
 <span className={`text-xs font-semibold ${hasBigFive ? 'text-lia-text-primary' : 'text-lia-text-disabled dark:text-lia-text-tertiary'}`}>
          {hasBigFive && bigFiveAvg !== null ? bigFiveAvg : '—'}
        </span>
      </div>
    )

  case 'quickActions':
    const quickActionStage = ((candidate.stage as string | undefined) || (candidate.etapa as string | undefined) || 'funil').toLowerCase()
    const isAlreadyDecided = quickActionStage === 'aprovados' || quickActionStage === 'reprovados'
    const showNeedsAction = candidate.needsAction === true

    if (isAlreadyDecided) {
      return null
    }

    return (
      <div className="relative flex items-center justify-center">
        {/* Indicador "Ação Necessária" - aparece quando não está em hover */}
        {showNeedsAction && (
          <div className="flex items-center gap-1 group-hover:hidden transition-opacity motion-reduce:transition-none">
            <Flag className="w-3.5 h-3.5 text-status-warning" strokeWidth={2} />
          </div>
        )}
        {/* Botões de ação - aparecem no hover */}
        <div className="hidden group-hover:flex items-center justify-center gap-1.5">
          <button
            onClick={(e) => {
              e.stopPropagation()
              if (quickActionStage === 'screening' || quickActionStage === 'triagem') {
                onApproveFromScreening(candidate)
              } else {
                openDecisionFlowModal(candidate, 'approve')
              }
            }}
            className="w-7 h-7 rounded-full flex items-center justify-center hover:opacity-80 transition-opacity motion-reduce:transition-none bg-gray-800"
            title="Aprovar candidato"
          >
            <ThumbsUp className="w-3.5 h-3.5 text-white" strokeWidth={2} />
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation()
              if (quickActionStage === 'screening' || quickActionStage === 'triagem') {
                onRejectFromScreening(candidate)
              } else {
                openDecisionFlowModal(candidate, 'reject')
              }
            }}
            className="w-7 h-7 rounded-full flex items-center justify-center hover:opacity-80 transition-opacity motion-reduce:transition-none bg-wedo-coral"
            title="Reprovar candidato"
          >
            <XCircle className="w-3.5 h-3.5 text-white" strokeWidth={2} />
          </button>
        </div>
      </div>
    )

  case 'name':
    const getAvatarUrl = (id: string, name: string): string => {
      let hash = 0
      const str = id + name
      for (let i = 0; i < str.length; i++) {
        const char = str.charCodeAt(i)
        hash = ((hash << 5) - hash) + char
        hash = hash & hash
      }
      const avatarIndex = Math.abs(hash % 70) + 1
      const gender = Math.abs(hash % 2) === 0 ? 'men' : 'women'
      return `https://randomuser.me/api/portraits/${gender}/${avatarIndex}.jpg`
    }
    const avatarUrl = (candidate.avatar as string | undefined)?.startsWith('http') ? (candidate.avatar as string) : getAvatarUrl(candidate.id || '', candidate.name || '')
    const isDemo = !(candidate.avatar as string | undefined)?.startsWith('http') || candidate.isDemo
    return (
      <div className="flex items-center gap-2">
        <div className="relative">
          <Avatar className="w-8 h-8">
            <AvatarImage src={avatarUrl as string | undefined} alt={candidate.name as string} />
            <AvatarFallback>{(candidate.name as string || '').split(' ').map((n: string) => n[0]).join('')}</AvatarFallback>
          </Avatar>
          {viewedCandidateIds.has(candidate.id) && (
            <div className="absolute -bottom-0.5 -right-0.5 w-4 h-4 bg-gray-300 rounded-full flex items-center justify-center border border-white" title="Perfil visualizado">
              <Eye className="w-2.5 h-2.5 text-white" />
            </div>
          )}
        </div>
        <div className="flex items-center gap-1.5">
          {!!(isDemo) && (
            <span className="text-micro font-medium text-lia-text-disabled dark:text-lia-text-tertiary">[D]</span>
          )}
          <span className="font-medium text-sm text-lia-text-primary dark:text-lia-text-primary">
            {candidate.name as string}
          </span>
          {(() => {
            const dataRequest = getDataRequestForCandidate(candidate.id as string)
            if (!dataRequest) return null
            return (
              <DataRequestIndicator
                candidateId={candidate.id}
                status={dataRequest.status as unknown as Parameters<typeof DataRequestIndicator>[0]["status"]}
                fieldsRequested={dataRequest.fieldsRequested as unknown as Parameters<typeof DataRequestIndicator>[0]["fieldsRequested"]}
                fieldsCompleted={dataRequest.fieldsCompleted as unknown as Parameters<typeof DataRequestIndicator>[0]["fieldsCompleted"]}
                expiresAt={dataRequest.expiresAt as string | Date | null | undefined}
                size="sm"
                onResend={onDataRequestResend}
                onViewDetails={onDataRequestViewDetails}
              />
            )
          })()}
        </div>
      </div>
    )

  case 'role':
    return (
      <div className="text-xs text-lia-text-primary dark:text-lia-text-primary">
        {((candidate.role as string | undefined) || (candidate.position as string | undefined) || 'UX Designer')}
      </div>
    )

  case 'currentCompany':
    return (
      <div className="text-xs text-lia-text-primary dark:text-lia-text-primary">
        {((candidate.currentCompany as string | undefined) || ((candidate.source as string | undefined) === 'LinkedIn' ? 'TechCorp' : 'Digital Agency'))}
      </div>
    )

  case 'stage': {
    const stageDropdownStages = dynamicStages.map(s => ({ id: s.id, name: s.name, displayName: s.displayName, color: s.color }))
    const currentStageObj = stageDropdownStages.find(s => s.id === ((candidate.stageId as string | undefined) || (candidate.stage as string | undefined)))
    return (
      <Popover>
        <PopoverTrigger asChild>
          <button className="inline-flex items-center gap-1 group/stage" onClick={(e) => e.stopPropagation()}>
            <Badge
              className="text-xs font-semibold border-0 whitespace-nowrap text-lia-text-primary dark:text-lia-text-primary cursor-pointer"
              style={{backgroundColor: currentStageObj?.color || 'var(--gray-200)'}}
            >
              {currentStageObj?.displayName || (candidate.stage as string | undefined)}
            </Badge>
            <ChevronDown className="w-3 h-3 text-lia-text-disabled group-hover/stage:text-lia-text-secondary transition-colors motion-reduce:transition-none" />
          </button>
        </PopoverTrigger>
        <PopoverContent className="w-44 p-1.5" align="start" sideOffset={4}>
          <div className="space-y-0.5">
            {stageDropdownStages.map((stage) => {
              const isCurrent = stage.id === ((candidate.stageId as string | undefined) || (candidate.stage as string | undefined))
              return (
                <button
                  key={stage.id}
                  className={`w-full flex items-center gap-2 px-2 py-1.5 rounded-md text-xs transition-colors motion-reduce:transition-none ${
                    isCurrent
                      ? 'bg-gray-100 dark:bg-lia-bg-secondary font-bold'
                      : 'hover:bg-gray-50 dark:hover:bg-gray-800/50'
                  }`}

                  onClick={() => {
                    if (!isCurrent) {
                      onTransitionRequired([candidate], (candidate.stageId as string | undefined) || (candidate.stage as string | undefined) || '', stage.id)
                    }
                  }}
                >
                  <div
                    className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                    style={{backgroundColor: stage.color}}
                  />
                  <span className="flex-1 text-left text-lia-text-primary dark:text-lia-text-primary truncate">
                    {stage.displayName}
                  </span>
                  {isCurrent && <CheckCircle className="w-3.5 h-3.5 text-wedo-cyan flex-shrink-0" />}
                </button>
              )
            })}
          </div>
        </PopoverContent>
      </Popover>
    )
  }

  case 'status': {
    const hasScheduledInterview = !!candidate.agendada
    return (
      <div className="flex items-center gap-1.5">
        <InteractiveSubStatusCell
          candidateId={candidate.id as string}
          candidateName={candidate.name as string}
          stage={candidate.stage as string | undefined}
          subStatus={(candidate.sub_status as string | undefined) || (candidate.status as string | undefined)}
          jobVacancyId={jobVacancyId}
          onStatusChange={onStatusChange}
        />
        {hasScheduledInterview && (
          <button
            onClick={(e) => {
              e.stopPropagation()
              const stage = (candidate.stageId as string | undefined) || (candidate.stage as string | undefined) || 'interview_hr'
              const dateStr = (candidate.interviewDate as string | undefined) || new Date(candidate.agendada as string).toLocaleDateString('pt-BR', { day: 'numeric', month: 'long', hour: '2-digit', minute: '2-digit' })
              onSetTransitionInitialPrompt(`O recrutador quer gerenciar a entrevista de ${candidate.name as string} agendada para ${dateStr}. Pergunte se quer alterar o horário (peça nova data/hora) ou cancelar. Se cancelar, pergunte para qual etapa quer mover o candidato.`)
              onSetTransitionAllowStageSelection(true)
              onSetTransitionInterviewAlert({ name: candidate.name as string, date: dateStr })
              openTransition([candidate], stage, stage)
            }}
            className="w-5 h-5 rounded-md flex items-center justify-center text-wedo-cyan-dark hover:bg-wedo-cyan/10 dark:hover:bg-wedo-cyan-dark/20 transition-colors motion-reduce:transition-none flex-shrink-0"
            title={`Gerenciar entrevista — ${(candidate.interviewDate as string | undefined) || new Date(candidate.agendada as string).toLocaleDateString('pt-BR')}`}
          >
            <Video className="w-3 h-3" />
          </button>
        )}
      </div>
    )
  }

  // Busca Global / Pearch columns
  case 'is_open_to_work':
    const isOpenToWork = candidate.is_opentowork || candidate.is_open_to_work
    return isOpenToWork ? (
      <Badge className="text-xs bg-status-success/15 text-status-success">Open to Work</Badge>
    ) : <span className="text-xs text-lia-text-disabled">—</span>

  case 'is_decision_maker':
    return candidate.is_decision_maker ? (
      <Badge className="text-xs bg-wedo-purple/15 text-wedo-purple">Decision Maker</Badge>
    ) : <span className="text-xs text-lia-text-disabled">—</span>

  case 'is_top_universities':
    return candidate.is_top_universities ? (
      <Badge className="text-xs bg-gray-100 dark:bg-lia-bg-secondary text-lia-text-secondary dark:text-lia-text-secondary">Top University</Badge>
    ) : <span className="text-xs text-lia-text-disabled">—</span>

  case 'is_hiring':
    return candidate.is_hiring ? (
      <Badge className="text-xs bg-wedo-orange/15 text-wedo-orange">Contratando</Badge>
    ) : <span className="text-xs text-lia-text-disabled">—</span>

  case 'headline':
    return <span className="text-xs text-lia-text-primary dark:text-lia-text-primary truncate">{(candidate.headline as string | undefined) || ''}</span>

  case 'expertise':
    const expertiseArray = candidate.expertise
    return <span className="text-xs text-lia-text-primary dark:text-lia-text-primary truncate">{Array.isArray(expertiseArray) ? expertiseArray.join(', ') : (expertiseArray || '')}</span>

  case 'linkedin_followers_count':
    return candidate.linkedin_followers_count ? (
      <span className="text-xs text-lia-text-primary dark:text-lia-text-primary">{(candidate.linkedin_followers_count as number).toLocaleString('pt-BR')}</span>
    ) : <span className="text-xs text-lia-text-disabled">—</span>

  case 'linkedin_connections_count':
    return candidate.linkedin_connections_count ? (
      <span className="text-xs text-lia-text-primary dark:text-lia-text-primary">{(candidate.linkedin_connections_count as number).toLocaleString('pt-BR')}</span>
    ) : <span className="text-xs text-lia-text-disabled">—</span>

  case 'outreach_message':
    return candidate.outreach_message ? (
      <div className="flex items-center gap-1">
        <span className="text-xs text-lia-text-primary dark:text-lia-text-primary truncate max-w-sidebar-content">{(candidate.outreach_message as string).slice(0, 50)}...</span>
        <button
          onClick={(e) => {
            e.stopPropagation()
            navigator.clipboard.writeText(candidate.outreach_message as string)
          }}
          className="p-0.5 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-md"
          title="Copiar mensagem"
        >
          <Copy className="w-3 h-3 text-lia-text-tertiary" />
        </button>
      </div>
    ) : <span className="text-xs text-lia-text-disabled">—</span>

  case 'best_personal_email':
    return candidate.best_personal_email ? (
      <a href={`mailto:${candidate.best_personal_email as string}`} className="text-xs text-lia-text-secondary hover:text-lia-text-primary hover:underline truncate dark:text-lia-text-secondary dark:hover:text-lia-text-inverse">
        {candidate.best_personal_email as string}
      </a>
    ) : <span className="text-xs text-lia-text-disabled">—</span>

  case 'phone_types':
    if (!candidate.phone_types || Object.keys(candidate.phone_types).length === 0) {
      return <span className="text-xs text-lia-text-disabled">—</span>
    }
    const activePhoneTypes = Object.entries(candidate.phone_types)
      .filter(([_, active]) => active)
      .map(([type]) => type)
    return <span className="text-xs text-lia-text-primary dark:text-lia-text-primary">{activePhoneTypes.join(', ') || '—'}</span>

  case 'estimated_age':
    return candidate.estimated_age ? (
      <span className="text-xs text-lia-text-primary dark:text-lia-text-primary">{candidate.estimated_age as number} anos</span>
    ) : <span className="text-xs text-lia-text-disabled">—</span>

  case 'match_reasoning':
    return (candidate.pearch_insights as unknown as Record<string, string | undefined>)?.match_reasoning ? (
      <span className="text-xs text-lia-text-primary dark:text-lia-text-primary truncate" title={(candidate.pearch_insights as unknown as Record<string, string>).match_reasoning}>
        {(candidate.pearch_insights as unknown as Record<string, string>).match_reasoning.slice(0, 60)}...
      </span>
    ) : <span className="text-xs text-lia-text-disabled">—</span>

  case 'overall_summary':
    return candidate.pearch_insights?.overall_summary ? (
      <span className="text-xs text-lia-text-primary dark:text-lia-text-primary truncate" title={candidate.pearch_insights.overall_summary}>
        {candidate.pearch_insights.overall_summary.slice(0, 60)}...
      </span>
    ) : <span className="text-xs text-lia-text-disabled">—</span>

  case 'query_insights':
    const queryInsightsData = candidate.pearch_insights?.query_insights
    if (!queryInsightsData || queryInsightsData.length === 0) {
      return <span className="text-xs text-lia-text-disabled">—</span>
    }
    return (
      <div className="flex flex-col gap-0.5">
        {queryInsightsData.slice(0, 2).map((insight: QueryInsight, idx: number) => (
          <div key={idx} className="flex items-center gap-1">
            <Badge className={`${textStyles.caption} !text-micro px-1 py-0 ${
              insight.match_level === 'Exceeds' ? badgeStyles.success :
              insight.match_level === 'Meets' ? badgeStyles.info :
              insight.match_level === 'Partial' ? badgeStyles.warning :
              badgeStyles.default
            }`}>
              {insight.match_level}
            </Badge>
            <span className={`${textStyles.caption} dark:!text-lia-text-disabled truncate max-w-[150px]`} title={insight.subquery}>
              {insight.subquery?.slice(0, 25)}...
            </span>
          </div>
        ))}
        {queryInsightsData.length > 2 && (
          <span className={textStyles.caption}>+{queryInsightsData.length - 2} mais</span>
        )}
      </div>
    )

  case 'pearch_insights':
    return candidate.pearch_insights?.overall_summary ? (
      <span className="text-xs text-lia-text-primary dark:text-lia-text-primary truncate">{candidate.pearch_insights.overall_summary.slice(0, 50)}...</span>
    ) : <span className="text-xs text-lia-text-disabled">—</span>

  case 'middle_name':
    return candidate.middle_name ? (
      <span className="text-xs text-lia-text-primary dark:text-lia-text-primary truncate">{candidate.middle_name as string}</span>
    ) : <span className="text-xs text-lia-text-disabled">—</span>

  case 'best_business_email':
    return candidate.best_business_email ? (
      <a href={`mailto:${candidate.best_business_email as string}`} className="text-xs text-lia-text-secondary hover:text-lia-text-primary hover:underline truncate dark:text-lia-text-secondary dark:hover:text-lia-text-inverse">
        {candidate.best_business_email as string}
      </a>
    ) : <span className="text-xs text-lia-text-disabled">—</span>

  case 'personal_emails':
    const personalEmails = candidate.personal_emails as string[] | undefined
    if (!personalEmails || personalEmails.length === 0) {
      return <span className="text-xs text-lia-text-disabled">—</span>
    }
    return (
      <span className="text-xs text-lia-text-primary dark:text-lia-text-primary truncate" title={personalEmails.join(', ')}>
        {personalEmails.length === 1 ? personalEmails[0] : `${personalEmails[0]} (+${personalEmails.length - 1})`}
      </span>
    )

  case 'business_emails':
    const businessEmails = candidate.business_emails as string[] | undefined
    if (!businessEmails || businessEmails.length === 0) {
      return <span className="text-xs text-lia-text-disabled">—</span>
    }
    return (
      <span className="text-xs text-lia-text-primary dark:text-lia-text-primary truncate" title={businessEmails.join(', ')}>
        {businessEmails.length === 1 ? businessEmails[0] : `${businessEmails[0]} (+${businessEmails.length - 1})`}
      </span>
    )

  case 'company_followers_count':
    return candidate.company_followers_count != null ? (
      <span className="text-xs text-lia-text-primary dark:text-lia-text-primary">{(candidate.company_followers_count as number).toLocaleString('pt-BR')}</span>
    ) : <span className="text-xs text-lia-text-disabled">—</span>

  case 'company_keywords':
    const companyKeywords = candidate.company_keywords as string[] | undefined
    if (!companyKeywords || companyKeywords.length === 0) {
      return <span className="text-xs text-lia-text-disabled">—</span>
    }
    return (
      <div className="flex flex-wrap gap-1">
        {companyKeywords.slice(0, 3).map((keyword: string, idx: number) => (
          <Badge key={idx} variant="outline" className="text-micro px-1 py-0 bg-gray-50 text-lia-text-secondary dark:bg-lia-bg-elevated dark:text-lia-text-secondary">
            {keyword}
          </Badge>
        ))}
        {companyKeywords.length > 3 && (
          <span className={textStyles.caption}>+{companyKeywords.length - 3}</span>
        )}
      </div>
    )

  case 'analise':
    const candidateStage = candidate.stage || candidate.etapa || 'funil'
    const hasAnalysisData = candidate.liaAnalysis || candidate.cvAnalysis || candidate.score
    const hasTriagemData = candidate.triagemHistory || candidate.screeningHistory || (candidateStage as string).toLowerCase() !== 'funil'
    return (
      <div className="flex items-center justify-center gap-1">
        <Button
          variant="ghost"
          size="sm"
          className={`h-7 w-7 p-0 ${hasAnalysisData ? 'text-lia-text-secondary hover:text-lia-text-primary hover:bg-gray-100' : 'text-lia-text-disabled cursor-not-allowed'}`}
          title={hasAnalysisData ? "Ver Análise CV vs Vaga" : "Análise pendente"}
          onClick={(e) => {
            e.stopPropagation()
            if (hasAnalysisData) onOpenAnalysis(candidate)
          }}
          disabled={!hasAnalysisData}
        >
          <Target className="w-4 h-4" />
        </Button>
        <Button
          variant="ghost"
          size="sm"
          className={`h-7 w-7 p-0 ${hasTriagemData ? 'text-lia-text-secondary hover:text-lia-text-primary hover:bg-gray-100' : 'text-lia-text-disabled cursor-not-allowed'}`}
          title={hasTriagemData ? "Ver Detalhes da Triagem" : "Triagem pendente"}
          onClick={(e) => {
            e.stopPropagation()
            if (hasTriagemData) onOpenTriagem(candidate)
          }}
          disabled={!hasTriagemData}
        >
          <BrainCircuit className="w-4 h-4" />
        </Button>
      </div>
    )

  case 'acoes':
  case 'actions':
    return (
      <div className="flex items-center justify-center">
        <Popover>
          <PopoverTrigger asChild>
            <button
              onClick={(e) => e.stopPropagation()}
              className="p-1.5 rounded-md hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors motion-reduce:transition-none"
              title="Mais ações"
            >
              <MoreVertical className="w-4 h-4 text-lia-text-tertiary" />
            </button>
          </PopoverTrigger>
          <PopoverContent align="end" className="w-48 p-1">
            <button
              onClick={(e) => {
                e.stopPropagation()
                onOpenAnalysis(candidate)
              }}
              className="w-full flex items-center gap-2 px-3 py-2 text-sm text-lia-text-primary dark:text-lia-text-primary hover:bg-gray-100 dark:hover:bg-gray-800 rounded-md"
            >
              <Eye className="w-4 h-4" />
              Ver perfil completo
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation()
                onOpenTriagem(candidate)
              }}
              className="w-full flex items-center gap-2 px-3 py-2 text-sm text-lia-text-primary dark:text-lia-text-primary hover:bg-gray-100 dark:hover:bg-gray-800 rounded-md"
            >
              <Brain className="w-4 h-4 text-wedo-cyan" />
              Ver triagem LIA
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation()
                // Abrir modal BigFive
                onSetScoreModalCandidate(candidate)
                onSetShowBigFiveModal(true)
              }}
              className="w-full flex items-center gap-2 px-3 py-2 text-sm text-lia-text-primary dark:text-lia-text-primary hover:bg-gray-100 dark:hover:bg-gray-800 rounded-md"
            >
              <Fingerprint className="w-4 h-4 text-lia-text-secondary" />
              Ver BigFive
            </button>
            <div className="my-1 border-t border-lia-border-subtle dark:border-lia-border-subtle" />
            <button
              onClick={(e) => {
                e.stopPropagation()
                const cStage = ((candidate.stage as string | undefined) || (candidate.etapa as string | undefined) || 'funil').toLowerCase()
                if (cStage === 'screening' || cStage === 'triagem') {
                  onApproveFromScreening(candidate)
                } else {
                  openDecisionFlowModal(candidate, 'approve')
                }
              }}
              className="w-full flex items-center gap-2 px-3 py-2 text-sm text-lia-text-primary dark:text-lia-text-primary hover:bg-gray-100 dark:hover:bg-gray-800 rounded-md"
            >
              <ThumbsUp className="w-4 h-4" />
              Aprovar
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation()
                const cStage = ((candidate.stage as string | undefined) || (candidate.etapa as string | undefined) || 'funil').toLowerCase()
                if (cStage === 'screening' || cStage === 'triagem') {
                  onRejectFromScreening(candidate)
                } else {
                  openDecisionFlowModal(candidate, 'reject')
                }
              }}
              className="w-full flex items-center gap-2 px-3 py-2 text-sm hover:bg-status-error/10 dark:hover:bg-status-error/20 rounded-md text-wedo-coral"
            >
              <XCircle className="w-4 h-4" />
              Reprovar
            </button>
          </PopoverContent>
        </Popover>
      </div>
    )

  default:
    return null
}
  }
}
