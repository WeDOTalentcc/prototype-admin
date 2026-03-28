"use client"

import React from "react"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Checkbox } from "@/components/ui/checkbox"
import { ScoreIconButton } from "@/components/ui/score-icon-button"
import { ScoreBreakdownBadgeLazy } from "@/components/score/ScoreBreakdownBadge"
import { AISuggestionBadge } from "@/components/ai"
import {
  StatusBadge,
  ChannelBadge,
  SourceBadge,
  WarningBadge,
  DateTimeBadge,
  OriginBadge,
  AwaitingBadge,
} from "@/components/ui/status-badge"
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
} from "lucide-react"
import { getStageByName, isApplicationSource } from "@/lib/recruitment-stages"
import { getSuggestionForCandidate } from "@/hooks/useCandidateSuggestions"
import { formatScorePercent } from "@/lib/design-tokens"

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
  candidates: any[]
  colorClass: string
  bgClass: string

  // State
  dynamicStages: DynamicStage[]
  searchQuery: string
  draggedCandidate: any
  dragOverColumn: string | null
  selectedCandidates: Set<string>
  selectedForCompare: Set<string>
  viewedCandidateIds: Set<string>
  favoriteCandidates: Set<string>
  shortListedCandidateIds: Set<string>
  aiSuggestions: any[]
  kanbanScoreMin: number
  kanbanStatusFilter: string[]
  kanbanWorkModelFilter: string[]
  kanbanOriginFilter: string[]
  currentJob: any
  _jobIdForSL: string | undefined

  // Derived / computed
  getColumnStyle: (stageId: string) => ColumnStyle
  getStageCategory: (stage: DynamicStage) => "system" | "default" | "custom"
  calculateNotaLiaGeral: (candidate: any) => number | null
  getDataRequestForCandidate: (candidateId: string) => DataRequestInfo | undefined

  // Setters
  setSelectedCandidates: (value: Set<string> | ((prev: Set<string>) => Set<string>)) => void
  setSelectedForCompare: (value: Set<string> | ((prev: Set<string>) => Set<string>)) => void
  setCandidatesData: (value: any | ((prev: any) => any)) => void
  setTransitionInitialPrompt: (prompt: string | undefined) => void
  setTransitionInterviewAlert: (value: { name: string; date: string } | null) => void
  setTransitionAllowStageSelection: (value: boolean) => void
  setDecisionFlowCandidate: (candidate: any) => void
  setDecisionFlowType: (type: "approve_to_triage" | "approve_to_interview" | "reject_pre_triage" | "reject_post_triage" | "request_urgency" | "reschedule_interview" | "confirm_hire") => void
  setShowDecisionFlowModal: (value: boolean) => void

  // Callbacks
  onDragStart: (e: React.DragEvent, candidate: any, fromColumn: string) => void
  onDragEnd: (e: React.DragEvent) => void
  onDragOver: (e: React.DragEvent, column: string) => void
  onDrop: (e: React.DragEvent, toColumn: string) => void
  onDragLeave: () => void
  onOpenPreview: (candidate: any) => void
  onSendEmail: (candidate: any) => void
  onSendWhatsApp: (candidate: any) => void
  onScheduleInterview: (candidate: any) => void
  onToggleFavorite: (candidateId: string) => void
  onToggleShortList: (candidateId: string) => void
  onOpenAnalysis: (candidate: any) => void
  onOpenScoreModal: (candidate: any, modalType: "geral" | "triagem" | "cv" | "tecnico" | "ingles" | "b5") => void
  onOpenDecisionFlowModal: (candidate: any, action: "approve" | "reject") => void
  onSendWSIInvite: (candidate: any) => void
  onSendFeedback: (candidate: any) => void
  onApproveFromScreening: (candidate: any) => void
  onRejectFromScreening: (candidate: any) => void
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
  openTransition: (candidates: any[], fromStage: string, toStage: string) => void
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
  const dynamicStage = dynamicStages.find((s) => s.id === stageId)
  const stageInfo = getStageByName(stageId)
  const displayTitle = dynamicStage?.displayName || stageInfo?.displayName || stageId

  let sortedCandidates = [...candidates]
  if (stageId === "screening") {
    sortedCandidates = candidates.sort((a, b) => {
      if (a.needsAction && !b.needsAction) return -1
      if (!a.needsAction && b.needsAction) return 1
      return b.score - a.score
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
        candidate.currentCompany?.toLowerCase().includes(query)
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
    <div
      className={`flex flex-col flex-1 bg-white rounded-md min-w-[275px] max-w-[368px] border border-gray-200 transition-all duration-300 ${
        isDropping ? "ring-2 ring-gray-400 bg-gray-50/20" : ""
      } h-[calc(100vh-16rem)]`}
      onDragOver={(e) => onDragOver(e, stageId)}
      onDragLeave={onDragLeave}
      onDrop={(e) => onDrop(e, stageId)}
    >
      {/* Header da Coluna - Fixo */}
      <div className="flex-shrink-0 p-2.5 pb-1.5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5 group">
            <div
              className={`w-2 h-2 rounded-full ${columnStyle.dot} transition-transform duration-300 ${
                isDropping ? "scale-150" : ""
              }`}
            ></div>
            <h3 className={`font-medium text-xs ${columnStyle.header}`}>{displayTitle}</h3>
            <span className="text-micro text-gray-800 dark:text-gray-200 bg-gray-100 dark:bg-gray-800 px-1.5 py-0.5 rounded-full">
              {filteredCandidates.length}
            </span>
            {stageId === "screening" && (currentJob.backendId || currentJob.id) && (
              <SaturationBadge jobId={(currentJob.backendId || currentJob.id).toString()} />
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
          </div>
          {filteredCandidates.length > 0 && (
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
              className="w-3.5 h-3.5 data-[state=checked]:bg-gray-900 data-[state=checked]:border-gray-900"
              title={`Selecionar todos da etapa ${displayTitle}`}
            />
          )}
        </div>
      </div>

      {/* Cards - Com scroll vertical */}
      <div className="flex-1 overflow-y-auto px-1.5 pb-1 space-y-1">
        {filteredCandidates.map((candidate, index) => (
          <div
            key={candidate.id}
            draggable
            onDragStart={(e) => onDragStart(e, candidate, stageId)}
            onDragEnd={onDragEnd}
            className={`bg-white dark:bg-gray-800 rounded-md border relative overflow-hidden ${
              candidate.needsAction
                ? "border-l-4 border-l-gray-800 border-gray-200 dark:border-gray-700"
                : (candidate.status === "triado_aprovado" || candidate.status === "triado") &&
                  stageId === "screening"
                ? "border-l-4 border-l-green-500 border-gray-200 dark:border-gray-700 bg-status-success/10/30 dark:bg-status-success/20"
                : "border-gray-200 dark:border-gray-700"
            } hover:transition-all duration-300 cursor-move group`}
            style={{animationDelay: `${index * 50}ms`,
              minHeight: "110px",
              transition: "all 0.3s ease",
              animation: isDropping ? "pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite" : undefined}}
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
          >
            {/* Tarja de Ação Necessária - Cinza puro */}
            {candidate.needsAction && (
              <div className="px-2 py-0.5 border-b bg-gray-100">
                <div className="flex items-center gap-1">
                  <Flag className="w-3 h-3 text-status-warning" />
                  <span className="text-micro font-bold text-gray-500">Ação Necessária</span>
                </div>
              </div>
            )}

            <div className="p-2 relative">
              {/* Ações rápidas - Posicionadas no canto direito */}
              <div className="absolute right-2 top-8 flex flex-col gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity z-10">
                {/* Menu de opções - Primeiro */}
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <button
                      className="p-1 hover:bg-gray-100 rounded transition-opacity bg-white/80"
                      onClick={(e) => e.stopPropagation()}
                      title="Mais opções"
                      aria-label="Mais opções do candidato"
                    >
                      <MoreVertical className="w-3 h-3 text-gray-600" aria-hidden="true" />
                    </button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent side="right" align="start" sideOffset={8} className="w-48">
                    <DropdownMenuItem
                      onClick={(e) => {
                        e.stopPropagation()
                        onSendEmail(candidate)
                      }}
                      className="text-xs text-gray-800 dark:text-gray-200 hover:bg-gray-50 cursor-pointer"
                    >
                      <Mail className="w-3.5 h-3.5 mr-2 text-gray-500" />
                      Enviar Email
                    </DropdownMenuItem>
                    <DropdownMenuItem
                      onClick={(e) => {
                        e.stopPropagation()
                        onSendWhatsApp(candidate)
                      }}
                      className="text-xs text-gray-800 dark:text-gray-200 hover:bg-gray-50 cursor-pointer"
                    >
                      <MessageCircle className="w-3.5 h-3.5 mr-2 text-gray-500" />
                      Enviar WhatsApp
                    </DropdownMenuItem>
                    <DropdownMenuItem
                      onClick={(e) => {
                        e.stopPropagation()
                        onScheduleInterview(candidate)
                      }}
                      className="text-xs text-gray-800 dark:text-gray-200 hover:bg-gray-50 cursor-pointer"
                    >
                      <Calendar className="w-3.5 h-3.5 mr-2 text-gray-500" />
                      Agendar Entrevista
                    </DropdownMenuItem>
                    <DropdownMenuItem
                      onClick={(e) => {
                        e.stopPropagation()
                        onSendWSIInvite(candidate)
                      }}
                      className="text-xs text-gray-800 dark:text-gray-200 hover:bg-gray-50 cursor-pointer"
                    >
                      <ClipboardList className="w-3.5 h-3.5 mr-2 text-gray-500" />
                      Triagem WSI
                    </DropdownMenuItem>
                    <DropdownMenuItem
                      onClick={(e) => {
                        e.stopPropagation()
                        onSendFeedback(candidate)
                      }}
                      className="text-xs text-gray-800 dark:text-gray-200 hover:bg-gray-50 cursor-pointer"
                    >
                      <MessageSquareText className="w-3.5 h-3.5 mr-2 text-gray-500" />
                      Enviar Feedback
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem
                      onClick={(e) => {
                        e.stopPropagation()
                        onToggleShortList(candidate.id)
                      }}
                      className="text-xs text-gray-800 dark:text-gray-200 hover:bg-gray-50 cursor-pointer"
                    >
                      <Bookmark
                        className={`w-3.5 h-3.5 mr-2 ${
                          shortListedCandidateIds.has(candidate.id)
                            ? "fill-gray-900 text-gray-900 dark:fill-gray-50 dark:text-gray-50"
                            : "text-gray-500"
                        }`}
                      />
                      {shortListedCandidateIds.has(candidate.id)
                        ? "Remover da Short List"
                        : "Adicionar à Short List"}
                    </DropdownMenuItem>
                    <DropdownMenuItem
                      onClick={(e) => {
                        e.stopPropagation()
                        onToggleFavorite(candidate.id)
                      }}
                      className="text-xs text-gray-800 dark:text-gray-200 hover:bg-gray-50 cursor-pointer"
                    >
                      <Heart
                        className={`w-3.5 h-3.5 mr-2 ${
                          favoriteCandidates.has(candidate.id)
                            ? "fill-red-500 text-status-error"
                            : "text-gray-500"
                        }`}
                      />
                      {favoriteCandidates.has(candidate.id)
                        ? "Remover dos Favoritos"
                        : "Adicionar a Favoritos"}
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>

                {/* Botão de Preview */}
                <button
                  className="p-1 hover:bg-gray-100 rounded transition-colors bg-white/80"
                  onClick={(e) => {
                    e.stopPropagation()
                    onOpenPreview(candidate)
                  }}
                  title="Ver detalhes do candidato"
                  aria-label={`Ver detalhes de ${candidate.name}`}
                >
                  <Eye className="w-3.5 h-3.5 text-gray-800 dark:text-gray-200" aria-hidden="true" />
                </button>
              </div>

              {/* Header do Card - Checkbox, Avatar, Nome */}
              <div className="flex items-center gap-1.5 mb-2 pr-6">
                {/* Checkbox pequeno */}
                <input
                  type="checkbox"
                  checked={selectedCandidates.has(candidate.id)}
                  className="w-3 h-3 rounded cursor-pointer flex-shrink-0 border border-gray-200"
                  aria-label={`Selecionar candidato ${candidate.name}`}
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

                {/* D9 — Checkbox para comparação de candidatos */}
                <input
                  type="checkbox"
                  className="w-3 h-3 rounded cursor-pointer flex-shrink-0 border border-gray-300 accent-gray-900"
                  checked={selectedForCompare.has(candidate.id)}
                  onChange={(e) => {
                    setSelectedForCompare((prev: Set<string>) => {
                      const next = new Set(prev)
                      if (e.target.checked) {
                        if (next.size < 4) next.add(candidate.id)
                      } else {
                        next.delete(candidate.id)
                      }
                      return next
                    })
                  }}
                  onClick={(e) => e.stopPropagation()}
                  aria-label={`Selecionar ${candidate.name} para comparação`}
                  title={
                    selectedForCompare.size >= 4 && !selectedForCompare.has(candidate.id)
                      ? "Máximo de 4 candidatos para comparação"
                      : "Comparar candidato"
                  }
                />

                {/* Avatar pequeno com foto */}
                <div className="relative flex-shrink-0">
                  {(() => {
                    const getKanbanAvatarUrl = (id: string, name: string): string => {
                      let hash = 0
                      const str = id + name
                      for (let i = 0; i < str.length; i++) {
                        const char = str.charCodeAt(i)
                        hash = ((hash << 5) - hash) + char
                        hash = hash & hash
                      }
                      const avatarIndex = Math.abs(hash % 70) + 1
                      const gender = Math.abs(hash % 2) === 0 ? "men" : "women"
                      return `https://randomuser.me/api/portraits/thumb/${gender}/${avatarIndex}.jpg`
                    }
                    const kanbanAvatarUrl =
                      candidate.avatar?.startsWith("http")
                        ? candidate.avatar
                        : getKanbanAvatarUrl(candidate.id || "", candidate.name || "")
                    return (
                      <Avatar className="w-7 h-7">
                        <AvatarImage src={kanbanAvatarUrl} alt={candidate.name} />
                        <AvatarFallback className="text-micro font-medium text-gray-600">
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
                      className="absolute -bottom-0.5 -right-0.5 w-3.5 h-3.5 bg-gray-300 rounded-full flex items-center justify-center border border-white"
                      title="Perfil visualizado"
                    >
                      <Eye className="w-2 h-2 text-white" />
                    </div>
                  )}
                </div>

                {/* Nome do candidato + Data Request Indicator */}
                <div className="flex items-center gap-1 flex-1 min-w-0">
                  <h4 className="font-medium text-xs truncate text-gray-950 dark:text-gray-50">
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

              {/* Scores - Todos os 6 indicadores (Geral, Triagem, CV, Técnico, Inglês, B5) */}
              {(() => {
                const geralScore = calculateNotaLiaGeral(candidate)
                const triagemScore = candidate.liaScore ?? candidate.score
                const cvScore = candidate.skillsMatch || candidate.fitScore
                const tecnicoScore = candidate.technicalTestScore
                const inglesScore = candidate.englishTestScore
                const b5Data = candidate.bigFive || candidate.bigFiveScores
                const b5Score = b5Data
                  ? Math.round(
                      (Object.values(b5Data).reduce(
                        (a: number, b: any) => a + (typeof b === "number" ? b : 0),
                        0
                      ) as number) / Object.values(b5Data).length
                    )
                  : null

                const scores = [
                  { id: "geral", icon: Gauge, value: geralScore, label: "Geral", alwaysClickable: false },
                  { id: "triagem", icon: BrainCircuit, value: triagemScore, label: "Triagem", alwaysClickable: true },
                  { id: "cv", icon: Target, value: cvScore, label: "CV", alwaysClickable: true },
                  { id: "tecnico", icon: Code, value: tecnicoScore, label: "Técnico", alwaysClickable: false },
                  { id: "ingles", icon: Globe, value: inglesScore, label: "Inglês", alwaysClickable: false },
                  { id: "b5", icon: Fingerprint, value: b5Score, label: "B5", alwaysClickable: false },
                ]

                return (
                  <div className="flex items-center gap-1.5 mb-1.5 flex-wrap">
                    {scores.map(({ id, icon: Icon, value, label, alwaysClickable }) => (
                      <ScoreIconButton
                        key={id}
                        id={id}
                        icon={Icon}
                        value={value}
                        formattedValue={value ? formatScorePercent(value, 0) : undefined}
                        label={label}
                        alwaysClickable={alwaysClickable}
                        onClick={() =>
                          onOpenScoreModal(
                            candidate,
                            id as "geral" | "triagem" | "cv" | "tecnico" | "ingles" | "b5"
                          )
                        }
                      />
                    ))}
                    {/* E1 — Score clicável: badge lazy com detalhamento da rubrica */}
                    {geralScore != null && _jobIdForSL && candidate.id && (
                      <ScoreBreakdownBadgeLazy
                        score={geralScore}
                        jobId={_jobIdForSL}
                        candidateId={String(candidate.id)}
                        size="sm"
                      />
                    )}
                  </div>
                )
              })()}

              {/* Informações do candidato - Alinhadas à esquerda */}
              <div className="space-y-0 mb-1.5">
                <div className="flex items-center gap-1 text-xs">
                  <Briefcase className="w-2.5 h-2.5 flex-shrink-0" />
                  <span className="truncate">{candidate.role}</span>
                </div>
                <div className="flex items-center gap-1 text-xs">
                  <Building className="w-2.5 h-2.5 flex-shrink-0" />
                  <span className="truncate">{candidate.currentCompany || "Não informado"}</span>
                </div>
                <div className="flex items-center gap-1 text-xs">
                  <MapPin className="w-2.5 h-2.5 flex-shrink-0" />
                  <span className="truncate">{candidate.location}</span>
                </div>
              </div>

              {/* Tags de Status Compactas */}
              <div className="mt-2 flex flex-wrap gap-1">
                {/* AI Suggestion Badge */}
                {(() => {
                  const suggestion = getSuggestionForCandidate(aiSuggestions, candidate.id)
                  if (suggestion) {
                    return (
                      <div onClick={(e) => e.stopPropagation()}>
                        <AISuggestionBadge
                          suggestion={suggestion}
                          onApprove={(id) => Promise.resolve(approveSuggestion(id))}
                          onReject={(id) => Promise.resolve(rejectSuggestion(id))}
                          compact
                        />
                      </div>
                    )
                  }
                  return null
                })()}

                {/* FUNIL - Candidatos sem triagem ainda */}
                {stageId === "sourcing" && (
                  <>
                    <StatusBadge
                      stageId={stageId}
                      variant="standard"
                      icon={User}
                      label={
                        candidate.source === "linkedin"
                          ? "Aplicou via LinkedIn"
                          : candidate.source === "website"
                          ? "Aplicou no site"
                          : candidate.source === "lia_database"
                          ? "Mapeado pela LIA"
                          : "Adicionado manual"
                      }
                    />
                    <StatusBadge
                      stageId={stageId}
                      variant="accent"
                      icon={BrainCircuit}
                      label="LIA iniciará triagem"
                      pulse
                    />
                  </>
                )}

                {/* TRIAGEM - Candidatos em contato com LIA */}
                {stageId === "screening" && (
                  <>
                    {candidate.needsAction || candidate.status === "triado_aprovado" ? (
                      <>
                        <StatusBadge
                          stageId={stageId}
                          variant="dark"
                          icon={CheckCircle}
                          label="Triagem concluída"
                        />
                        <StatusBadge
                          stageId={stageId}
                          variant="accent"
                          icon={Target}
                          label="Decisão pendente"
                          pulse
                          onClick={() => onOpenAnalysis(candidate)}
                          title="Clique para ver análise completa"
                        />
                      </>
                    ) : (
                      <StatusBadge
                        stageId={stageId}
                        variant="outlined"
                        icon={MessageCircle}
                        label={
                          candidate.liatriagem === "respondendo"
                            ? "Respondendo agora"
                            : "Conversa em andamento"
                        }
                      />
                    )}
                    <ChannelBadge channel={candidate.contactChannelId || "whatsapp"} />
                  </>
                )}

                {/* ENTREVISTA */}
                {(stageId === "interview_hr" ||
                  stageId === "interview_technical" ||
                  stageId === "interview_manager") && (
                  <>
                    {candidate.agendada ? (
                      <>
                        <StatusBadge
                          stageId={stageId}
                          variant="scheduled"
                          icon={CalendarCheck}
                          label="Entrevista confirmada"
                        />
                        {candidate.interviewDate && (
                          <DateTimeBadge date={candidate.interviewDate} />
                        )}
                        <ChannelBadge channel={candidate.typeOfInterview || "teams"} />
                      </>
                    ) : (
                      <StatusBadge
                        stageId={stageId}
                        variant="accent"
                        icon={Clock}
                        label="Aguardando agendamento"
                        pulse
                      />
                    )}
                    {candidate.interviewCompleted && !candidate.interviewFeedback && (
                      <StatusBadge
                        stageId={stageId}
                        variant="accent"
                        icon={Clock}
                        label="Feedback pendente"
                        pulse
                      />
                    )}
                  </>
                )}

                {/* FINAL */}
                {stageId === "offer" && (
                  <>
                    <StatusBadge stageId={stageId} variant="standard" icon={Star} label="Finalista" />
                    {candidate.proposal ? (
                      <>
                        <StatusBadge
                          stageId={stageId}
                          variant="dark"
                          icon={FileText}
                          label="Proposta enviada"
                        />
                        {!candidate.proposalResponse && (
                          <StatusBadge
                            stageId={stageId}
                            variant="accent"
                            icon={Clock}
                            label="Aguardando resposta"
                            pulse
                          />
                        )}
                      </>
                    ) : (
                      <StatusBadge
                        stageId={stageId}
                        variant="accent"
                        icon={Clock}
                        label="Aguardando aprovação"
                        pulse
                      />
                    )}
                    {candidate.negotiating && (
                      <StatusBadge
                        stageId={stageId}
                        variant="outlined"
                        icon={MessageCircle}
                        label="Em negociação"
                      />
                    )}
                  </>
                )}

                {/* CONTRATADOS */}
                {stageId === "hired" && (
                  <>
                    <StatusBadge stageId={stageId} variant="hired" icon={Trophy} label="Contratado" />
                    {candidate.startDate && (
                      <StatusBadge
                        stageId={stageId}
                        variant="standard"
                        icon={Calendar}
                        label={`Início: ${new Date(candidate.startDate).toLocaleDateString("pt-BR", {
                          day: "2-digit",
                          month: "2-digit",
                        })}`}
                      />
                    )}
                    {candidate.sub_status && (
                      <StatusBadge stageId={stageId} subStatus={candidate.sub_status} />
                    )}
                  </>
                )}

                {/* REPROVADOS */}
                {stageId === "rejected" && (
                  <>
                    <StatusBadge
                      stageId={stageId}
                      variant="rejected"
                      icon={XCircle}
                      label={
                        candidate.rejectionReason === "withdrew"
                          ? "Desistiu"
                          : candidate.rejectionStage === "screening"
                          ? "Reprovado triagem"
                          : candidate.rejectionStage === "interview"
                          ? "Reprovado entrevista"
                          : "Reprovado"
                      }
                    />
                    {candidate.feedbackSent && (
                      <StatusBadge
                        stageId={stageId}
                        variant="dark"
                        icon={CheckCircle}
                        label="Feedback enviado"
                      />
                    )}
                  </>
                )}

                {/* PROPOSTA RECUSADA */}
                {stageId === "offer_declined" && (
                  <>
                    <StatusBadge
                      stageId={stageId}
                      variant="rejected"
                      icon={XCircle}
                      label="Proposta recusada"
                    />
                    {candidate.feedbackSent && (
                      <StatusBadge
                        stageId={stageId}
                        variant="dark"
                        icon={CheckCircle}
                        label="Feedback enviado"
                      />
                    )}
                  </>
                )}

                {/* Badge de Warning - Dias parado */}
                {(candidate.warning || candidate.warningDays) && (
                  <WarningBadge days={candidate.daysPaused} message={candidate.warningDays} />
                )}

                {/* Badge de expectativa salarial */}
                {candidate.expectativa && (
                  <StatusBadge
                    stageId={stageId}
                    variant={
                      candidate.expectativa === "no budget"
                        ? "dark"
                        : candidate.expectativa === "acima do budget"
                        ? "outlined"
                        : "standard"
                    }
                    icon={DollarSign}
                    label={candidate.expectativa}
                  />
                )}

                {/* Badge de Origem */}
                {candidate.origin && <OriginBadge origin={candidate.origin} />}

                {/* Badge Aguardando (fila de saturação) + Override */}
                {(candidate.status === "awaiting_screening" ||
                  candidate.sub_status === "awaiting_screening" ||
                  candidate.subStatus === "awaiting_screening") && (
                  <>
                    <AwaitingBadge />
                    {(currentJob?.backendId || currentJob?.id) && (
                      <OverrideApproveButton
                        candidateId={candidate.id}
                        candidateName={candidate.name}
                        vacancyId={(currentJob.backendId || currentJob.id).toString()}
                        onApproved={(cId: string) => {
                          setCandidatesData((prev: any) => {
                            const updated = { ...prev }
                            Object.keys(updated).forEach((key) => {
                              updated[key] = updated[key].map((c: any) =>
                                c.id === cId
                                  ? { ...c, status: "triado_aprovado", sub_status: undefined, subStatus: undefined }
                                  : c
                              )
                            })
                            return updated
                          })
                        }}
                      />
                    )}
                  </>
                )}

                {/* Tag de Origem */}
                <SourceBadge
                  source={candidate.source || "website"}
                  isApplication={isApplicationSource(candidate.source || "website")}
                />

                {/* Sub-Status Badge */}
                {candidate.sub_status && !["hired", "rejected", "offer_declined"].includes(stageId) && (
                  <StatusBadge stageId={stageId} subStatus={candidate.sub_status} />
                )}
              </div>
            </div>

            {/* Container de Ações */}
            {(stageId === "sourcing" ||
              stageId === "screening" ||
              stageId.startsWith("interview_") ||
              stageId === "offer") && (
              <div className="border-t border-gray-100 p-2 max-h-0 overflow-hidden opacity-0 group-hover:max-h-20 group-hover:opacity-100 transition-all duration-200 ease-out relative z-20 bg-gray-50">
                {/* Botões para FUNIL */}
                {stageId === "sourcing" && (
                  <div className="flex gap-1">
                    <button
                      className="flex-1 flex items-center justify-center gap-1 px-2 py-1.5 bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200 rounded-full text-micro font-medium transition-colors"
                      onClick={(e) => {
                        e.stopPropagation()
                        onOpenDecisionFlowModal(candidate, "approve")
                      }}
                    >
                      <ThumbsUp className="w-3 h-3" aria-hidden="true" />
                      <span>Aprovar</span>
                    </button>
                    <button
                      className="flex-1 flex items-center justify-center gap-1 px-2 py-1.5 bg-status-error hover:bg-status-error text-white rounded-full text-micro font-medium transition-colors"
                      onClick={(e) => {
                        e.stopPropagation()
                        onOpenDecisionFlowModal(candidate, "reject")
                      }}
                    >
                      <XCircle className="w-3 h-3" aria-hidden="true" />
                      <span>Reprovar</span>
                    </button>
                  </div>
                )}

                {/* Botões para TRIAGEM */}
                {stageId === "screening" && (
                  <div className="flex gap-1">
                    <button
                      className="flex-1 flex items-center justify-center gap-1 px-2 py-1.5 bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200 rounded-full text-micro font-medium transition-colors"
                      onClick={(e) => {
                        e.stopPropagation()
                        onApproveFromScreening(candidate)
                      }}
                    >
                      <ThumbsUp className="w-3 h-3" aria-hidden="true" />
                      <span>Aprovar</span>
                    </button>
                    <button
                      className="flex-1 flex items-center justify-center gap-1 px-2 py-1.5 bg-status-error hover:bg-status-error text-white rounded-full text-micro font-medium transition-colors"
                      onClick={(e) => {
                        e.stopPropagation()
                        onRejectFromScreening(candidate)
                      }}
                    >
                      <XCircle className="w-3 h-3" aria-hidden="true" />
                      <span>Reprovar</span>
                    </button>
                  </div>
                )}

                {/* Botões para ENTREVISTA */}
                {(stageId === "interview_hr" ||
                  stageId === "interview_technical" ||
                  stageId === "interview_manager") && (
                  <div className="flex gap-1">
                    {candidate.agendada ? (
                      <>
                        <button
                          className="flex-1 flex items-center justify-center gap-1.5 px-2 py-1.5 bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200 rounded-full text-micro font-medium transition-colors"
                          onClick={(e) => {
                            e.stopPropagation()
                            const teamsUrl =
                              candidate.teamsLink || "https://teams.microsoft.com/l/meetup-join/..."
                            window.open(teamsUrl, "_blank")
                          }}
                          title={`Entrar na reunião - ${
                            candidate.interviewDate ||
                            new Date(candidate.agendada).toLocaleDateString("pt-BR")
                          }`}
                        >
                          <Video className="w-3 h-3 text-gray-600" />
                          <span>
                            {candidate.interviewDate ||
                              new Date(candidate.agendada).toLocaleDateString("pt-BR", {
                                day: "numeric",
                                month: "short",
                                hour: "2-digit",
                                minute: "2-digit",
                              })}
                          </span>
                        </button>
                        <button
                          className="flex-1 flex items-center justify-center gap-1 px-2 py-1.5 bg-status-warning hover:bg-status-warning text-white rounded-full text-micro font-medium transition-colors"
                          onClick={(e) => {
                            e.stopPropagation()
                            const dateStr =
                              candidate.interviewDate ||
                              new Date(candidate.agendada).toLocaleDateString("pt-BR", {
                                day: "numeric",
                                month: "long",
                                hour: "2-digit",
                                minute: "2-digit",
                              })
                            setTransitionInitialPrompt(
                              `O recrutador quer alterar o horário da entrevista de ${candidate.name} agendada para ${dateStr}. Peça a nova data e horário preferido e confirme o reagendamento com o candidato.`
                            )
                            setTransitionInterviewAlert({ name: candidate.name, date: dateStr })
                            openTransition([candidate], stageId, stageId)
                          }}
                          title="Alterar horário da entrevista"
                        >
                          <Calendar className="w-3 h-3" />
                          <span>Alterar</span>
                        </button>
                        <button
                          className="flex-shrink-0 flex items-center justify-center gap-1 px-2 py-1.5 bg-status-error/10 hover:bg-status-error/15 text-status-error border border-status-error/30 rounded-full text-micro font-medium transition-colors"
                          onClick={(e) => {
                            e.stopPropagation()
                            const dateStr =
                              candidate.interviewDate ||
                              new Date(candidate.agendada).toLocaleDateString("pt-BR", {
                                day: "numeric",
                                month: "long",
                                hour: "2-digit",
                                minute: "2-digit",
                              })
                            setTransitionInitialPrompt(
                              `O recrutador quer cancelar a entrevista de ${candidate.name} agendada para ${dateStr}. Pergunte para qual etapa ele quer mover o candidato (ou se mantém na mesma) e confirme o cancelamento.`
                            )
                            setTransitionAllowStageSelection(true)
                            setTransitionInterviewAlert({ name: candidate.name, date: dateStr })
                            openTransition([candidate], stageId, stageId)
                          }}
                          title="Cancelar entrevista"
                        >
                          <XCircle className="w-3 h-3" />
                          <span>Cancelar</span>
                        </button>
                      </>
                    ) : (
                      <>
                        <button
                          className="flex-1 flex items-center justify-center gap-1 px-2 py-1.5 bg-status-warning hover:bg-status-warning text-white rounded-full text-micro font-medium transition-colors"
                          onClick={(e) => {
                            e.stopPropagation()
                            setDecisionFlowCandidate(candidate)
                            setDecisionFlowType("request_urgency")
                            setShowDecisionFlowModal(true)
                          }}
                        >
                          <AlertCircle className="w-3 h-3" />
                          <span>Urgência</span>
                        </button>
                        <button
                          className="flex-1 flex items-center justify-center gap-1 px-2 py-1.5 bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200 rounded-full text-micro font-medium transition-colors"
                          onClick={(e) => {
                            e.stopPropagation()
                            setDecisionFlowCandidate(candidate)
                            setDecisionFlowType("reschedule_interview")
                            setShowDecisionFlowModal(true)
                          }}
                        >
                          <Calendar className="w-3 h-3" />
                          <span>Alterar Horário</span>
                        </button>
                      </>
                    )}
                  </div>
                )}

                {stageId === "offer" && (
                  <button
                    className="w-full flex items-center justify-center gap-1 px-2 py-1.5 bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:hover:bg-gray-200 dark:text-gray-900 rounded-full text-micro transition-colors"
                    onClick={(e) => {
                      e.stopPropagation()
                    }}
                  >
                    <FileText className="w-3 h-3" />
                    <span>Gerenciar Proposta</span>
                  </button>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
