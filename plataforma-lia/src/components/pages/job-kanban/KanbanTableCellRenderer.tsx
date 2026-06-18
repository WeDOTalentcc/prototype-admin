"use client"

import React from"react"
import { useTranslations } from "next-intl"
import { Button } from"@/components/ui/button"
import { Chip } from "@/components/ui/chip"
import { Avatar, AvatarFallback, AvatarImage } from"@/components/ui/avatar"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from"@/components/ui/popover"
import { InteractiveSubStatusCell } from"@/components/tables"
import {
  DataRequestIndicator,
} from"@/components/ui/data-request-indicator"
import {
  Brain, Target, Fingerprint,
  ThumbsUp, XCircle, Flag, Eye, ChevronDown, CheckCircle,
  ChevronRight, MoreVertical, Video, BrainCircuit,
} from"lucide-react"
import { CandidateChatPopover } from "@/components/shared/CandidateChatPopover"
import { renderScoreCell } from"./KanbanScoreCells"
import { renderPearchCell } from"./KanbanPearchCells"
import type {
  KanbanCandidate,
  KanbanTableCellRendererProps,
} from"./KanbanTableCellRenderer.types"

export type { KanbanCandidate, KanbanTableCellRendererProps }
export type { DynamicStageItem, QueryInsight } from"./KanbanTableCellRenderer.types"

export function createKanbanCellRenderer(props: KanbanTableCellRendererProps) {
  const {
    t,
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
    onDirectTransition,
    onCandidateClick,
  } = props

  const scoreCellProps = {
    calculateNotaLiaGeral,
    onSetSelectedCandidateForModal,
    onSetActiveModal,
    onSetShowBigFiveModal,
    onOpenTriagem,
    onOpenAnalysis,
  }

  return function renderCustomCell(candidate: KanbanCandidate, columnId: string): React.ReactNode {
    const tBridge = t as unknown as (key: string, params?: Record<string, unknown>) => string
    const scoreResult = renderScoreCell(candidate, columnId, scoreCellProps, tBridge)
    if (scoreResult !== undefined) return scoreResult

    const pearchResult = renderPearchCell(candidate, columnId, tBridge)
    if (pearchResult !== undefined) return pearchResult

    switch (columnId) {
      case 'quickActions': {
        const quickActionStage = ((candidate.stage as string | undefined) || (candidate.etapa as string | undefined) || 'funil').toLowerCase()
        const isAlreadyDecided = quickActionStage === 'aprovados' || quickActionStage === 'reprovados'
        const showNeedsAction = candidate.needsAction === true

        if (isAlreadyDecided) {
          return null
        }

        return (
          <div className="relative flex items-center justify-center">
            {showNeedsAction && (
              <div className="flex items-center gap-1 group-hover:hidden transition-opacity motion-reduce:transition-none">
                <Flag className="w-3.5 h-3.5 text-status-warning" strokeWidth={2} />
              </div>
            )}
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
                className="w-7 h-7 rounded-full flex items-center justify-center hover:opacity-80 transition-opacity motion-reduce:transition-none bg-lia-btn-primary-hover"
                title={t('approveCandidate')}
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
                title={t('rejectCandidate')}
              >
                <XCircle className="w-3.5 h-3.5 text-white" strokeWidth={2} />
              </button>
            </div>
          </div>
        )
      }

      case 'name': {
        const getAvatarUrl = (_id: string, _name: string): string | undefined => {
          return undefined
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
                <div className="absolute -bottom-0.5 -right-0.5 w-4 h-4 bg-lia-border-default rounded-full flex items-center justify-center border border-white" title={t('profileViewed')}>
                  <Eye className="w-2.5 h-2.5 text-white" />
                </div>
              )}
            </div>
            <div className="flex items-center gap-1.5 group/name">
              {!!(isDemo) && (
                <span className="text-micro font-medium text-lia-text-tertiary">[D]</span>
              )}
              <CandidateChatPopover
                candidateId={candidate.id as string}
                candidateName={candidate.name as string}
                jobId={jobVacancyId}
              >
                <span
                  className="font-medium text-sm text-lia-text-primary"
                  data-lia-entity-type="candidate"
                  data-lia-entity-id={candidate.id as string}
                  data-lia-entity-label={candidate.name as string}
                >
                  {candidate.name as string}
                </span>
              </CandidateChatPopover>
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
      }

      case 'role':
        return (
          <div className="text-xs text-lia-text-primary">
            {((candidate.role as string | undefined) || (candidate.position as string | undefined) || 'UX Designer')}
          </div>
        )

      case 'currentCompany':
        return (
          <div className="text-xs text-lia-text-primary">
            {((candidate.current_company as string | undefined) || ((candidate.source as string | undefined) === 'LinkedIn' ? 'TechCorp' : 'Digital Agency'))}
          </div>
        )

      case 'stage': {
        const candidateStageId = (candidate.stageId as string | undefined) || (candidate.stage as string | undefined)
        const currentStageObj = dynamicStages.find(s => s.id === candidateStageId)
        return (
          <StageDropdown
            candidate={candidate}
            dynamicStages={dynamicStages}
            currentStageId={candidateStageId}
            currentStageObj={currentStageObj}
            jobVacancyId={jobVacancyId}
            onTransitionRequired={onTransitionRequired}
            onDirectTransition={onDirectTransition}
          />
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
                  onSetTransitionInitialPrompt(t('manageInterviewPrompt', { name: candidate.name as string, date: dateStr }))
                  onSetTransitionAllowStageSelection(true)
                  onSetTransitionInterviewAlert({ name: candidate.name as string, date: dateStr })
                  openTransition([candidate], stage, stage)
                }}
                className="w-5 h-5 rounded-md flex items-center justify-center text-wedo-cyan-text hover:bg-wedo-cyan/10 dark:hover:bg-wedo-cyan-dark/20 transition-colors motion-reduce:transition-none flex-shrink-0"
                title={t('manageInterviewTitle', { date: (candidate.interviewDate as string | undefined) || new Date(candidate.agendada as string).toLocaleDateString('pt-BR') })}
              >
                <Video className="w-3 h-3" />
              </button>
            )}
          </div>
        )
      }

      case 'analise': {
        const candidateStage = candidate.stage || candidate.etapa || 'funil'
        const hasAnalysisData = candidate.liaAnalysis || candidate.cvAnalysis || candidate.score
        const hasTriagemData = candidate.triagemHistory || candidate.screeningHistory || (candidateStage as string).toLowerCase() !== 'funil'
        return (
          <div className="flex items-center justify-center gap-1">
            <Button
              variant="ghost"
              size="sm"
              className={`h-7 w-7 p-0 ${hasAnalysisData ? 'text-lia-text-secondary hover:text-lia-text-primary hover:bg-lia-bg-tertiary' : 'text-lia-text-disabled cursor-not-allowed'}`}
              title={hasAnalysisData ? t('viewCVAnalysis') : t('analysisPending')}
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
              className={`h-7 w-7 p-0 ${hasTriagemData ? 'text-lia-text-secondary hover:text-lia-text-primary hover:bg-lia-bg-tertiary' : 'text-lia-text-disabled cursor-not-allowed'}`}
              title={hasTriagemData ? t('viewScreeningDetails') : t('screeningPending')}
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
      }

      case 'acoes':
      case 'actions':
        return (
          <div className="flex items-center justify-center">
            <Popover>
              <PopoverTrigger asChild>
                <button
                  onClick={(e) => e.stopPropagation()}
                  className="p-1.5 rounded-xl hover:bg-lia-bg-tertiary dark:hover:bg-lia-btn-primary-hover transition-colors motion-reduce:transition-none"
                  title={t('moreActions')}
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
                  className="w-full flex items-center gap-2 px-3 py-2 text-sm text-lia-text-primary hover:bg-lia-bg-tertiary dark:hover:bg-lia-btn-primary-hover rounded-xl"
                >
                  <Eye className="w-4 h-4" />
                  {t('viewFullProfile')}
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    onOpenTriagem(candidate)
                  }}
                  className="w-full flex items-center gap-2 px-3 py-2 text-sm text-lia-text-primary hover:bg-lia-bg-tertiary dark:hover:bg-lia-btn-primary-hover rounded-xl"
                >
                  <Brain className="w-4 h-4 text-wedo-cyan" />
                  {t('viewLIAScreening')}
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    onSetScoreModalCandidate(candidate)
                    onSetShowBigFiveModal(true)
                  }}
                  className="w-full flex items-center gap-2 px-3 py-2 text-sm text-lia-text-primary hover:bg-lia-bg-tertiary dark:hover:bg-lia-btn-primary-hover rounded-xl"
                >
                  <Fingerprint className="w-4 h-4 text-lia-text-secondary" />
                  {t('viewBigFive')}
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
                  className="w-full flex items-center gap-2 px-3 py-2 text-sm text-lia-text-primary hover:bg-lia-bg-tertiary dark:hover:bg-lia-btn-primary-hover rounded-xl"
                >
                  <ThumbsUp className="w-4 h-4" />
                  {t('approve')}
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
                  {t('reject')}
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

// StageDropdown — two-level Popover: stage (→ modal) + sub-statuses (→ direct PATCH)
function StageDropdown({
  candidate,
  dynamicStages,
  currentStageId,
  currentStageObj,
  jobVacancyId,
  onTransitionRequired,
  onDirectTransition,
}: {
  candidate: import("./KanbanTableCellRenderer.types").KanbanCandidate
  dynamicStages: import("./KanbanTableCellRenderer.types").DynamicStageItem[]
  currentStageId: string | undefined
  currentStageObj: import("./KanbanTableCellRenderer.types").DynamicStageItem | undefined
  jobVacancyId?: string
  onTransitionRequired: (candidates: import("./KanbanTableCellRenderer.types").KanbanCandidate[], fromStage: string, toStage: string) => void
  onDirectTransition?: (candidate: import("./KanbanTableCellRenderer.types").KanbanCandidate, toStage: string, subStatus: string, jobVacancyId?: string) => Promise<void>
}) {
  const [expandedStageId, setExpandedStageId] = React.useState<string | null>(null)
  const [open, setOpen] = React.useState(false)

  return (
    <Popover open={open} onOpenChange={(v) => { setOpen(v); if (!v) setExpandedStageId(null) }}>
      <PopoverTrigger asChild>
        <button className="inline-flex items-center gap-1 group/stage" onClick={(e) => e.stopPropagation()}>
          <Chip variant="neutral" muted
            className="text-xs font-semibold border-0 whitespace-nowrap text-lia-text-primary cursor-pointer"
            style={{ backgroundColor: currentStageObj?.color || 'var(--lia-border-subtle)' }}
          >
            {currentStageObj?.displayName || currentStageId}
          </Chip>
          <ChevronDown className="w-3 h-3 text-lia-text-muted group-hover/stage:text-lia-text-secondary transition-colors motion-reduce:transition-none" />
        </button>
      </PopoverTrigger>
      <PopoverContent className="w-48 p-1.5" align="start" sideOffset={4}>
        <div className="space-y-0.5">
          {dynamicStages.map((stage) => {
            const isCurrent = stage.id === currentStageId
            const hasSubStatuses = !!stage.subStatuses?.length
            const isExpanded = expandedStageId === stage.id
            return (
              <div key={stage.id}>
                <button
                  className={`w-full flex items-center gap-2 px-2 py-1.5 rounded-md text-xs transition-colors motion-reduce:transition-none ${
                    isCurrent
                      ? 'bg-lia-bg-tertiary dark:bg-lia-bg-secondary font-bold'
                      : 'hover:bg-lia-bg-secondary dark:hover:bg-lia-btn-primary-hover/50'
                  }`}
                  onClick={() => {
                    if (isCurrent) return
                    if (hasSubStatuses) {
                      setExpandedStageId(prev => prev === stage.id ? null : stage.id)
                    } else {
                      setOpen(false)
                      onTransitionRequired([candidate], currentStageId || '', stage.id)
                    }
                  }}
                >
                  <div className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ backgroundColor: stage.color }} />
                  <span className="flex-1 text-left text-lia-text-primary truncate">{stage.displayName}</span>
                  {isCurrent && <CheckCircle className="w-3.5 h-3.5 text-wedo-cyan-text flex-shrink-0" />}
                  {!isCurrent && hasSubStatuses && (
                    <ChevronRight className={`w-3 h-3 text-lia-text-tertiary flex-shrink-0 transition-transform motion-reduce:transition-none ${isExpanded ? 'rotate-90' : ''}`} />
                  )}
                </button>

                {isExpanded && hasSubStatuses && (
                  <div className="ml-4 mt-0.5 space-y-0.5 border-l border-lia-border-subtle pl-2">
                    <button
                      className="w-full flex items-center gap-1.5 px-2 py-1 rounded-md text-xs italic text-lia-text-tertiary hover:bg-lia-bg-secondary transition-colors motion-reduce:transition-none"
                      onClick={() => {
                        setOpen(false)
                        onTransitionRequired([candidate], currentStageId || '', stage.id)
                      }}
                    >
                      Mover sem sub-status
                    </button>
                    {stage.subStatuses!.map((sub) => (
                      <button
                        key={sub.name}
                        className="w-full flex items-center gap-1.5 px-2 py-1 rounded-md text-xs text-lia-text-secondary hover:bg-lia-bg-secondary transition-colors motion-reduce:transition-none"
                        onClick={async () => {
                          setOpen(false)
                          if (onDirectTransition) {
                            await onDirectTransition(candidate, stage.id, sub.name, jobVacancyId)
                          } else {
                            onTransitionRequired([candidate], currentStageId || '', stage.id)
                          }
                        }}
                      >
                        {sub.display_name}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </PopoverContent>
    </Popover>
  )
}
