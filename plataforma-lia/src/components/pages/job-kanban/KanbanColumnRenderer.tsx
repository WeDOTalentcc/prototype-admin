"use client"

import React from "react"
import { useTranslations } from "next-intl"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Checkbox } from "@/components/ui/checkbox"
import { ScoreIconButton } from "@/components/ui/score-icon-button"
import { AISuggestionBadge } from "@/components/ai"
import { OverrideApproveButton } from "@/components/kanban/components/OverrideApproveButton"
import { SaturationBadge } from "@/components/kanban/components/SaturationBadge"
import { ColumnContextMenu } from "@/components/kanban/components/ColumnContextMenu"
import {
  DataRequestIndicator,
  type DataRequestStatus,
  type RequestedField,
} from "@/components/ui/data-request-indicator"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu"
import {
  Briefcase,
  Building,
  MapPin,
  Flag,
  MoreVertical,
  Eye,
  Mail,
  MessageCircle,
  Calendar,
  ClipboardList,
  MessageSquareText,
  Bookmark,
  Heart,
  Gauge,
  BrainCircuit,
  Target,
  Code,
  Globe,
  Fingerprint,
  User,
  CheckCircle,
  Clock,
  CalendarCheck,
  Star,
  FileText,
  Trophy,
  XCircle,
  DollarSign,
  ThumbsUp,
  ThumbsDown,
  AlertCircle,
  Video,
  X,
  GitCompare,
} from "lucide-react"
import { getStageByName, isApplicationSource } from "@/lib/recruitment-stages"
import { getSuggestionForCandidate } from "@/hooks/ai/useCandidateSuggestions"
import { formatScorePercent } from "@/lib/design-tokens"
import type { CandidateLocal } from "@/services/lia-api"
import { KanbanColumnHeader } from "./KanbanColumnHeader"
import { KanbanColumnShell } from "./KanbanColumnShell"
import { KanbanCardShell } from "./KanbanCardShell"
import { KanbanCardActions } from "./KanbanCardActions"
import { KanbanCardScores } from "./KanbanCardScores"
import { KanbanCardStatusBadges } from "./KanbanCardStatusBadges"
import { KanbanCardInterviewButtons } from "./KanbanCardInterviewButtons"

type KanbanCandidate = CandidateLocal & {
  score?: number
  role?: string
  company?: string
  location?: string
  currentCompany?: string
  workModel?: string
  origin?: string
  needsAction?: boolean
  stageId?: string
  pipelineStage?: string
  avatar?: string
  matchPercentage?: number
  applicationId?: string
  appliedAt?: string
  pipelineOrder?: number
  saturationLevel?: string
  dataRequest?: Record<string, unknown>
  [key: string]: unknown
}

type CurrentJob = {
  id?: string | number
  backendId?: string | number
  [key: string]: unknown
}

type CandidatesData = Record<string, KanbanCandidate[]>

type AISuggestion = {
  id: string
  candidate_id?: string
  suggested_action?: string
  confidence?: number
  [key: string]: unknown
}

interface DynamicStage {
  id: string
  name: string
  displayName: string
  order: number
  color: string
  stageType: "active" | "final"
  isInitial?: boolean
  isFinal?: boolean
  isHired?: boolean
  isRejection?: boolean
  isActive?: boolean
  actionBehavior?: string
}

interface ColumnStyle {
  dot: string
  header: string
}

interface DataRequestInfo {
  status: DataRequestStatus
  fieldsRequested: RequestedField[]
  fieldsCompleted: RequestedField[]
  expiresAt?: string
}

interface KanbanColumnRendererProps {
  stageId: string
  candidates: KanbanCandidate[]
  colorClass: string
  bgClass: string

  // State
  dynamicStages: DynamicStage[]
  searchQuery: string
  draggedCandidate: KanbanCandidate | null | undefined
  dragOverColumn: string | null
  selectedCandidates: Set<string>
  selectedForCompare: Set<string>
  viewedCandidateIds: Set<string>
  favoriteCandidates: Set<string>
  shortListedCandidateIds: Set<string>
  aiSuggestions: AISuggestion[]
  kanbanScoreMin: number
  kanbanStatusFilter: string[]
  kanbanWorkModelFilter: string[]
  kanbanOriginFilter: string[]
  currentJob: CurrentJob
  _jobIdForSL: string | undefined

  // Derived / computed
  getColumnStyle: (stageId: string) => ColumnStyle
  getStageCategory: (stage: DynamicStage) => "system" | "default" | "custom"
  calculateNotaLiaGeral: (candidate: KanbanCandidate) => number | null
  getDataRequestForCandidate: (candidateId: string) => DataRequestInfo | undefined

  // Setters
  setSelectedCandidates: (value: Set<string> | ((prev: Set<string>) => Set<string>)) => void
  setSelectedForCompare: (value: Set<string> | ((prev: Set<string>) => Set<string>)) => void
  setCandidatesData: (value: CandidatesData | ((prev: CandidatesData) => CandidatesData)) => void
  setTransitionInitialPrompt: (prompt: string | undefined) => void
  setTransitionInterviewAlert: (value: { name: string; date: string } | null) => void
  setTransitionAllowStageSelection: (value: boolean) => void
  setDecisionFlowCandidate: (candidate: KanbanCandidate) => void
  setDecisionFlowType: (type: "approve_to_triage" | "approve_to_interview" | "reject_pre_triage" | "reject_post_triage" | "request_urgency" | "reschedule_interview" | "confirm_hire") => void
  setShowDecisionFlowModal: (value: boolean) => void

  // Callbacks
  onDragStart: (e: React.DragEvent, candidate: KanbanCandidate, fromColumn: string) => void
  onDragEnd: (e: React.DragEvent) => void
  onDragOver: (e: React.DragEvent, column: string) => void
  onDrop: (e: React.DragEvent, toColumn: string) => void
  onDragLeave: () => void
  onOpenPreview: (candidate: KanbanCandidate) => void
  onSendEmail: (candidate: KanbanCandidate) => void
  onSendWhatsApp: (candidate: KanbanCandidate) => void
  onScheduleInterview: (candidate: KanbanCandidate) => void
  onToggleFavorite: (candidateId: string) => void
  onToggleShortList: (candidateId: string) => void
  onOpenAnalysis: (candidate: KanbanCandidate) => void
  onOpenScoreModal: (candidate: KanbanCandidate, modalType: "geral" | "triagem" | "cv" | "tecnico" | "ingles" | "b5") => void
  onOpenDecisionFlowModal: (candidate: KanbanCandidate, action: "approve" | "reject") => void
  onSendWSIInvite: (candidate: KanbanCandidate) => void
  onSendFeedback: (candidate: KanbanCandidate) => void
  onApproveFromScreening: (candidate: KanbanCandidate) => void
  onRejectFromScreening: (candidate: KanbanCandidate) => void
  onManageProposal?: (candidate: KanbanCandidate) => void
  onInlineRename: (stageId: string, newName: string) => void
  onInlineToggleActive: (stageId: string, isActive: boolean) => void
  onInlineRemove: (stageId: string) => void
  onInlineMoveLeft: (stageId: string) => void
  onInlineMoveRight: (stageId: string) => void
  onInlineUpdateSLA: (stageId: string, slaHours: number) => void
  onOpenSettings: () => void
  onDataRequestResend: (candidateId: string) => void
  onDataRequestViewDetails: (candidateId: string) => void
  approveSuggestion: (suggestionId: string) => void
  rejectSuggestion: (suggestionId: string) => void
  openTransition: (candidates: KanbanCandidate[], fromStage: string, toStage: string) => void
}

export function KanbanColumnRenderer({
  stageId,
  candidates,
  dynamicStages,
  searchQuery,
  draggedCandidate,
  dragOverColumn,
  selectedCandidates,
  selectedForCompare,
  viewedCandidateIds,
  favoriteCandidates,
  shortListedCandidateIds,
  aiSuggestions,
  kanbanScoreMin,
  kanbanStatusFilter,
  kanbanWorkModelFilter,
  kanbanOriginFilter,
  currentJob,
  _jobIdForSL,
  getColumnStyle,
  getStageCategory,
  calculateNotaLiaGeral,
  getDataRequestForCandidate,
  setSelectedCandidates,
  setSelectedForCompare,
  setCandidatesData,
  setTransitionInitialPrompt,
  setTransitionInterviewAlert,
  setTransitionAllowStageSelection,
  setDecisionFlowCandidate,
  setDecisionFlowType,
  setShowDecisionFlowModal,
  onDragStart,
  onDragEnd,
  onDragOver,
  onDrop,
  onDragLeave,
  onOpenPreview,
  onSendEmail,
  onSendWhatsApp,
  onScheduleInterview,
  onToggleFavorite,
  onToggleShortList,
  onOpenAnalysis,
  onOpenScoreModal,
  onOpenDecisionFlowModal,
  onSendWSIInvite,
  onSendFeedback,
  onApproveFromScreening,
  onRejectFromScreening,
  onManageProposal,
  onInlineRename,
  onInlineToggleActive,
  onInlineRemove,
  onInlineMoveLeft,
  onInlineMoveRight,
  onInlineUpdateSLA,
  onOpenSettings,
  onDataRequestResend,
  onDataRequestViewDetails,
  approveSuggestion,
  rejectSuggestion,
  openTransition,
}: KanbanColumnRendererProps) {
  const t = useTranslations('kanban')
  const dynamicStage = dynamicStages.find((s) => s.id === stageId)
  const stageInfo = getStageByName(stageId)
  const displayTitle = dynamicStage?.displayName || stageInfo?.displayName || stageId

  let sortedCandidates = [...candidates]
  if (stageId === "screening") {
    sortedCandidates = candidates.sort((a, b) => {
      if (a.needsAction && !b.needsAction) return -1
      if (!a.needsAction && b.needsAction) return 1
      return (b.score ?? 0) - (a.score ?? 0)
    })
  }

  const filteredCandidates = sortedCandidates.filter((candidate) => {
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      const matchesSearch =
        candidate.name.toLowerCase().includes(query) ||
        candidate.role?.toLowerCase().includes(query) ||
        candidate.company?.toLowerCase().includes(query) ||
        candidate.location?.toLowerCase().includes(query) ||
        candidate.current_company?.toLowerCase().includes(query)
      if (!matchesSearch) return false
    }

    if (kanbanScoreMin > 0 && candidate.score && candidate.score < kanbanScoreMin) {
      return false
    }

    if (kanbanStatusFilter.length > 0 && candidate.status) {
      const candidateStatus = candidate.status.toLowerCase().replace(/ /g, "_")
      if (!kanbanStatusFilter.includes(candidateStatus)) return false
    }

    if (kanbanWorkModelFilter.length > 0 && candidate.workModel) {
      const workModel = candidate.workModel.toLowerCase()
      if (!kanbanWorkModelFilter.includes(workModel)) return false
    }

    if (kanbanOriginFilter.length > 0) {
      const candidateOrigin = (candidate.origin || "").toLowerCase()
      if (!candidateOrigin || !kanbanOriginFilter.includes(candidateOrigin)) return false
    }

    return true
  })

  const columnStyle = getColumnStyle(stageId)
  const isDropping = dragOverColumn === stageId

  return (
    <KanbanColumnShell
      density="compact"
      isDropping={isDropping}
      onDragOver={(e) => onDragOver(e, stageId)}
      onDragLeave={onDragLeave}
      onDrop={(e) => onDrop(e, stageId)}
      data-testid="kanban-column"
      data-stage-id={stageId}
      header={
      <KanbanColumnHeader
        title={displayTitle}
        count={filteredCandidates.length}
        accentClass={columnStyle.dot}
        width="sm"
        isDropping={isDropping}
        inlineExtras={
          <>
            {stageId === "screening" && (currentJob.backendId || currentJob.id) && (
              <SaturationBadge jobId={String(currentJob.backendId || currentJob.id || '')} />
            )}
            {dynamicStage && (
              <ColumnContextMenu
                stage={dynamicStage}
                stageCategory={getStageCategory(dynamicStage)}
                onRename={onInlineRename}
                onToggleActive={onInlineToggleActive}
                onRemove={onInlineRemove}
                onMoveLeft={onInlineMoveLeft}
                onMoveRight={onInlineMoveRight}
                onUpdateSLA={onInlineUpdateSLA}
                onOpenSettings={onOpenSettings}
                canMoveLeft={
                  dynamicStages.indexOf(dynamicStage) > 0 &&
                  !dynamicStages[dynamicStages.indexOf(dynamicStage) - 1]?.isInitial
                }
                canMoveRight={
                  dynamicStages.indexOf(dynamicStage) < dynamicStages.length - 1 &&
                  !dynamicStages[dynamicStages.indexOf(dynamicStage) + 1]?.isFinal
                }
              />
            )}
          </>
        }
        actions={
          filteredCandidates.length > 0 ? (
            <Checkbox
              checked={filteredCandidates.every((c) => selectedCandidates.has(c.id))}
              onCheckedChange={(checked) => {
                if (checked) {
                  const newSelected = new Set(selectedCandidates)
                  filteredCandidates.forEach((c) => newSelected.add(c.id))
                  setSelectedCandidates(newSelected)
                } else {
                  const newSelected = new Set(selectedCandidates)
                  filteredCandidates.forEach((c) => newSelected.delete(c.id))
                  setSelectedCandidates(newSelected)
                }
              }}
              className="w-3.5 h-3.5 data-[state=checked]:bg-lia-btn-primary-bg data-[state=checked]:border-lia-btn-primary-bg"
              title={t('selectAllInStage', { stage: displayTitle })}
            />
          ) : null
        }
      />
      }
    >
      {/* Cards - Com scroll vertical */}
      <div className="flex-1 overflow-y-auto px-1.5 pb-1 space-y-1">
        {filteredCandidates.map((candidate, index) => (
          <KanbanCardShell
            key={candidate.id}
            density="compact"
            data-testid="candidate-card"
            data-candidate-id={candidate.id}
            data-index={index}
            draggable
            onDragStart={(e) => onDragStart(e, candidate, stageId)}
            onDragEnd={onDragEnd}
            accentLeftClass={
              candidate.needsAction
                ? "border-l-lia-btn-primary-hover"
                : (candidate.status === "triado_aprovado" || candidate.status === "triado") &&
                  stageId === "screening"
                ? "border-l-green-500"
                : undefined
            }
            isDropping={isDropping}
            className={`cursor-move duration-300 ${
              (candidate.status === "triado_aprovado" || candidate.status === "triado") &&
              stageId === "screening"
                ? "bg-status-success/10/30 dark:bg-status-success/20"
                : ""
            }`}
            style={{
              animationDelay: `${index * 50}ms`,
              minHeight: "110px",
              transition: "all 0.3s ease",
            }}
            onMouseEnter={(e) => {
              if (!draggedCandidate) {
                e.currentTarget.style.transform = "translateY(-1px)"
              }
            }}
            onMouseLeave={(e) => {
              if (!draggedCandidate) {
                e.currentTarget.style.transform = "translateY(0)"
              }
            }}
            onClick={() => !draggedCandidate && onOpenPreview(candidate)}
            ribbon={
              candidate.needsAction ? (
                <div className="flex items-center gap-1">
                  <Flag className="w-3 h-3 text-status-warning" />
                  <span className="text-micro font-bold text-lia-text-tertiary">{t('actionRequired')}</span>
                </div>
              ) : null
            }
            footer={
              <KanbanCardInterviewButtons
                candidate={candidate}
                stageId={stageId}
                setTransitionInitialPrompt={setTransitionInitialPrompt}
                setTransitionInterviewAlert={setTransitionInterviewAlert}
                setTransitionAllowStageSelection={setTransitionAllowStageSelection}
                setDecisionFlowCandidate={setDecisionFlowCandidate as (c: unknown) => void}
                setDecisionFlowType={setDecisionFlowType}
                setShowDecisionFlowModal={setShowDecisionFlowModal}
                onOpenDecisionFlowModal={onOpenDecisionFlowModal as (c: unknown, action: "approve" | "reject") => void}
                onApproveFromScreening={onApproveFromScreening as (c: unknown) => void}
                onRejectFromScreening={onRejectFromScreening as (c: unknown) => void}
                openTransition={openTransition as (candidates: unknown[], fromStage: string, toStage: string) => void}
                onManageProposal={onManageProposal ? (onManageProposal as (c: unknown) => void) : undefined}
              />
            }
            footerDivider={false}
          >
            <div className="relative">
              {/* Ações rápidas - Posicionadas no canto direito */}
              <KanbanCardActions
                candidate={candidate}
                shortListedCandidateIds={shortListedCandidateIds}
                favoriteCandidates={favoriteCandidates}
                onOpenPreview={onOpenPreview as (c: unknown) => void}
                onSendEmail={onSendEmail as (c: unknown) => void}
                onSendWhatsApp={onSendWhatsApp as (c: unknown) => void}
                onScheduleInterview={onScheduleInterview as (c: unknown) => void}
                onSendWSIInvite={onSendWSIInvite as (c: unknown) => void}
                onSendFeedback={onSendFeedback as (c: unknown) => void}
                onToggleShortList={onToggleShortList}
                onToggleFavorite={onToggleFavorite}
              />

              {/* Header do Card - Checkbox, Avatar, Nome */}
              <div className="flex items-center gap-1.5 mb-2 pr-6">
                {/* Checkbox pequeno */}
                <input
                  type="checkbox"
                  checked={selectedCandidates.has(candidate.id)}
                  className="w-3 h-3 rounded-xl cursor-pointer flex-shrink-0 border border-lia-border-subtle hover:bg-lia-interactive-hover transition-colors"
                  aria-label={t('selectCandidate', { name: candidate.name })}
                  onClick={(e) => {
                    e.stopPropagation()
                    const newSelected = new Set(selectedCandidates)
                    if (newSelected.has(candidate.id)) {
                      newSelected.delete(candidate.id)
                    } else {
                      newSelected.add(candidate.id)
                    }
                    setSelectedCandidates(newSelected)
                  }}
                  onChange={() => {}}
                />

                {/* D9 — Toggle de comparação de candidatos (ícone distinto + tooltip permanente) */}
                {(() => {
                  const isCompareSelected = selectedForCompare.has(candidate.id)
                  const isCompareLocked = selectedForCompare.size >= 4 && !isCompareSelected
                  return (
                    <button
                      type="button"
                      role="switch"
                      aria-checked={isCompareSelected}
                      aria-label={t('selectForComparison', { name: candidate.name })}
                      title={
                        isCompareLocked
                          ? t('maxCandidatesComparison')
                          : t('compareCandidate')
                      }
                      disabled={isCompareLocked}
                      onClick={(e) => {
                        e.stopPropagation()
                        setSelectedForCompare((prev: Set<string>) => {
                          const next = new Set(prev)
                          if (next.has(candidate.id)) {
                            next.delete(candidate.id)
                          } else if (next.size < 4) {
                            next.add(candidate.id)
                          }
                          return next
                        })
                      }}
                      className={
                        "inline-flex items-center justify-center w-4 h-4 rounded-full flex-shrink-0 border transition-colors motion-reduce:transition-none " +
                        (isCompareSelected
                          ? "bg-wedo-cyan/20 border-wedo-cyan text-wedo-cyan-dark dark:text-wedo-cyan"
                          : "border-lia-border-default text-lia-text-tertiary hover:bg-lia-interactive-hover hover:text-lia-text-secondary") +
                        (isCompareLocked ? " opacity-40 cursor-not-allowed" : " cursor-pointer")
                      }
                    >
                      <GitCompare className="w-2.5 h-2.5" aria-hidden="true" />
                    </button>
                  )
                })()}

                {/* Avatar pequeno com foto */}
                <div className="relative flex-shrink-0">
                  {(() => {
                    const kanbanAvatarUrl =
                      candidate.avatar?.startsWith("http")
                        ? candidate.avatar
                        : undefined
                    return (
                      <Avatar className="w-7 h-7">
                        <AvatarImage src={kanbanAvatarUrl} alt={candidate.name} />
                        <AvatarFallback className="text-micro font-medium text-lia-text-secondary">
                          {candidate.name
                            .split(" ")
                            .map((n: string) => n[0])
                            .join("")
                            .substring(0, 2)}
                        </AvatarFallback>
                      </Avatar>
                    )
                  })()}
                  {viewedCandidateIds.has(candidate.id) && (
                    <div
                      className="absolute -bottom-0.5 -right-0.5 w-3.5 h-3.5 bg-lia-border-default rounded-full flex items-center justify-center border border-white"
                      title={t('profileViewed')}
                    >
                      <Eye className="w-2 h-2 text-white" />
                    </div>
                  )}
                </div>

                {/* Nome do candidato + Data Request Indicator */}
                <div className="flex items-center gap-1 flex-1 min-w-0">
                  <h4 className="font-medium text-xs truncate text-lia-text-primary">
                    {candidate.name}
                  </h4>
                  {(() => {
                    const dataRequest = getDataRequestForCandidate(candidate.id)
                    if (!dataRequest) return null
                    return (
                      <DataRequestIndicator
                        candidateId={candidate.id}
                        status={dataRequest.status}
                        fieldsRequested={dataRequest.fieldsRequested}
                        fieldsCompleted={dataRequest.fieldsCompleted}
                        expiresAt={dataRequest.expiresAt}
                        onResend={onDataRequestResend}
                        onViewDetails={onDataRequestViewDetails}
                        size="sm"
                      />
                    )
                  })()}
                </div>
              </div>

              {/* Scores */}
              <KanbanCardScores
                candidate={candidate}
                calculateNotaLiaGeral={calculateNotaLiaGeral as (c: unknown) => number | null}
                _jobIdForSL={_jobIdForSL}
                onOpenScoreModal={onOpenScoreModal as (c: unknown, modalType: "geral" | "triagem" | "cv" | "tecnico" | "ingles" | "b5") => void}
              />

              {/* Informações do candidato - Alinhadas à esquerda */}
              <div className="space-y-0 mb-1.5">
                <div className="flex items-center gap-1 text-xs text-lia-text-secondary">
                  <Briefcase className="w-2.5 h-2.5 flex-shrink-0" />
                  <span className="truncate">{candidate.role || t('notAvailable')}</span>
                </div>
                <div className="flex items-center gap-1 text-xs text-lia-text-secondary">
                  <Building className="w-2.5 h-2.5 flex-shrink-0" />
                  <span className="truncate">{candidate.current_company || t('notAvailable')}</span>
                </div>
                {candidate.location ? (
                  <div className="flex items-center gap-1 text-xs text-lia-text-secondary">
                    <MapPin className="w-2.5 h-2.5 flex-shrink-0" />
                    <span className="truncate">{candidate.location}</span>
                  </div>
                ) : (
                  <div className="flex items-center gap-1 text-xs text-lia-text-disabled">
                    <MapPin className="w-2.5 h-2.5 flex-shrink-0" />
                    <span className="truncate">{t('notAvailable')}</span>
                  </div>
                )}
              </div>

              {/* Tags de Status Compactas */}
              <KanbanCardStatusBadges
                candidate={candidate}
                stageId={stageId}
                aiSuggestions={aiSuggestions}
                currentJob={currentJob}
                setCandidatesData={setCandidatesData as (v: unknown) => void}
                onOpenAnalysis={onOpenAnalysis as (c: unknown) => void}
                approveSuggestion={approveSuggestion}
                rejectSuggestion={rejectSuggestion}
              />
            </div>
          </KanbanCardShell>
        ))}
      </div>
    </KanbanColumnShell>
  )
}
