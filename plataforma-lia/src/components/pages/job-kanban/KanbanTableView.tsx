"use client"

import React from "react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
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
import {
  UnifiedCandidateTable,
  type TableColumn,
  type TableSortConfig,
  getColumnDefinition,
  getDefaultTableColumns,
  InteractiveSubStatusCell,
} from "@/components/tables"
import { KanbanColumnConfigPanel } from "@/components/pages/job-kanban/KanbanColumnConfigPanel"
import {
  DataRequestIndicator,
} from "@/components/ui/data-request-indicator"
import {
  Filter, X, Brain, Target, Code, Globe, Fingerprint, Gauge,
  ThumbsUp, XCircle, Flag, Eye, ChevronDown, CheckCircle,
  MoreVertical, Video, Copy, BrainCircuit,
  AlertTriangle,
} from "lucide-react"
import { textStyles, badgeStyles, formatScorePercent } from "@/lib/design-tokens"
import { getUrgencyLevel } from "@/components/kanban/utils/status-utils"
import type { CandidateLocal } from "@/services/lia-api"

type QueryInsight = {
  match_level?: string
  subquery?: string
}

type KanbanCandidate = CandidateLocal & {
  pearch_insights?: {
    overall_summary?: string
    query_insights?: QueryInsight[]
  }
}

interface DynamicStageItem {
  id: string
  name: string
  displayName: string
  color?: string
}

interface SaturationData {
  is_saturated: boolean
  approved_count: number
  saturation_threshold: number
  saturation_percentage: number
}

interface PaginatedResult {
  candidates: KanbanCandidate[]
  total: number
  totalPages: number
}

interface KanbanTableViewProps {
  // Visibility / mode
  showSuperChat: boolean

  // Filter panel state
  showTableFiltersPanel: boolean
  onShowTableFiltersPanelChange: (value: boolean) => void

  // Stage filter
  dynamicStages: DynamicStageItem[]
  tableStageFilter: string[]
  onTableStageFilterChange: (value: string[]) => void

  // Sort state
  tableSortColumn: string
  tableSortDirection: 'asc' | 'desc'
  onSortChange: (config: TableSortConfig) => void

  // Pagination
  currentPage: number
  onCurrentPageChange: (page: number) => void
  getPaginatedCandidates: () => PaginatedResult

  // Column config
  showColumnConfig: boolean
  onShowColumnConfigChange: (value: boolean) => void
  tableColumns: TableColumn[]
  onTableColumnsChange: (columns: TableColumn[]) => void

  // Selection
  selectedCandidates: Set<string>
  onSelectionChange: (newSelection: Set<string>) => void

  // Job data
  jobVacancyId?: string
  saturationData: SaturationData | null

  // Candidate actions
  onColumnResize: (columnId: string, width: number) => void
  onCandidateClick: (candidate: KanbanCandidate) => void
  onStatusChange: (candidateId: string, newSubStatus: string, stage: string, jobVacancyId?: string) => Promise<boolean>
  onTransitionRequest: (candidate: KanbanCandidate, fromStage: string, toStage: string) => void
  onTransitionRequired: (candidates: KanbanCandidate[], fromStage: string, toStage: string) => void

  // Callbacks para células customizadas
  calculateNotaLiaGeral: (candidate: KanbanCandidate) => number | null
  getLiaAlerts: (candidate: KanbanCandidate) => Record<string, unknown>[]
  viewedCandidateIds: Set<string>
  onOpenTriagem: (candidate: KanbanCandidate) => void
  onOpenAnalysis: (candidate: KanbanCandidate) => void
  onSetSelectedCandidateForModal: (candidate: KanbanCandidate) => void
  onSetActiveModal: (modal: string) => void
  onSetShowBigFiveModal: (show: boolean) => void
  onSetScoreModalCandidate: (candidate: KanbanCandidate) => void
  getDataRequestForCandidate: (candidateId: string) => Record<string, unknown> | null | undefined
  onDataRequestResend: (candidateId: string) => void
  onDataRequestViewDetails: (candidateId: string) => void
  onApproveFromScreening: (candidate: KanbanCandidate) => void
  onRejectFromScreening: (candidate: KanbanCandidate) => void
  onApproveCandidate: (candidate: KanbanCandidate) => void
  onRejectCandidate: (candidate: KanbanCandidate) => void
  openDecisionFlowModal: (candidate: KanbanCandidate, action: 'approve' | 'reject') => void

  // Interview management
  onSetTransitionInitialPrompt: (prompt: string) => void
  onSetTransitionAllowStageSelection: (allow: boolean) => void
  onSetTransitionInterviewAlert: (alert: { name: string; date: string }) => void
  openTransition: (candidates: KanbanCandidate[], fromStage: string, toStage: string) => void

  // Preview panel
  isPreviewOpen: boolean
  previewCandidate: KanbanCandidate | null | undefined
  isPreviewMaximized: boolean
  onClosePreview: () => void
  onTogglePreviewMaximize: () => void
  onNavigateCandidate: (index: number) => void
  onCandidatePageOpen: (candidate: KanbanCandidate) => void
  onScheduleInterview: (candidate: KanbanCandidate) => void
  onAddToVacancy: (candidate: KanbanCandidate) => void
  onToggleFavorite: (candidate: KanbanCandidate) => void
  favoriteCandidates: Set<string>
  onSendWSIInvite: (candidate: KanbanCandidate) => void
  onSendEmail: (candidate: KanbanCandidate) => void
  onSendWhatsApp: (candidate: KanbanCandidate) => void
  onSendTriagem: (candidate: KanbanCandidate) => void
  onSendAgendamento: (candidate: KanbanCandidate) => void
  onSendFeedback: (candidate: KanbanCandidate) => void
  candidatesData: Record<string, KanbanCandidate[]>
}

const CandidatePreviewDynamic = React.lazy(() =>
  import("@/components/candidate-preview").then(m => ({ default: m.CandidatePreview }))
)

export function KanbanTableView({
  showTableFiltersPanel,
  onShowTableFiltersPanelChange,
  dynamicStages,
  tableStageFilter,
  onTableStageFilterChange,
  tableSortColumn,
  tableSortDirection,
  onSortChange,
  currentPage,
  onCurrentPageChange,
  getPaginatedCandidates,
  showColumnConfig,
  onShowColumnConfigChange,
  tableColumns,
  onTableColumnsChange,
  selectedCandidates,
  onSelectionChange,
  jobVacancyId,
  saturationData,
  onColumnResize,
  onCandidateClick,
  onStatusChange,
  onTransitionRequest,
  onTransitionRequired,
  calculateNotaLiaGeral,
  getLiaAlerts,
  viewedCandidateIds,
  onOpenTriagem,
  onOpenAnalysis,
  onSetSelectedCandidateForModal,
  onSetActiveModal,
  onSetShowBigFiveModal,
  onSetScoreModalCandidate,
  getDataRequestForCandidate,
  onDataRequestResend,
  onDataRequestViewDetails,
  onApproveFromScreening,
  onRejectFromScreening,
  onApproveCandidate,
  onRejectCandidate,
  openDecisionFlowModal,
  onSetTransitionInitialPrompt,
  onSetTransitionAllowStageSelection,
  onSetTransitionInterviewAlert,
  openTransition,
  isPreviewOpen,
  previewCandidate,
  isPreviewMaximized,
  onClosePreview,
  onTogglePreviewMaximize,
  onNavigateCandidate,
  onCandidatePageOpen,
  onScheduleInterview,
  onAddToVacancy,
  onToggleFavorite,
  favoriteCandidates,
  onSendWSIInvite,
  onSendEmail,
  onSendWhatsApp,
  onSendTriagem,
  onSendAgendamento,
  onSendFeedback,
  candidatesData,
}: KanbanTableViewProps) {
  const itemsPerPage = 50

  return (
    <>
    {/* Painel de Filtros - TABLE */}
    {showTableFiltersPanel && (
      <div className="flex-shrink-0 w-72 transition-colors duration-300">
        <Card className="h-[calc(100vh-12rem)] flex flex-col overflow-hidden border border-lia-border-subtle dark:border-lia-border-subtle rounded-md">
          {/* Header do Painel de Filtros */}
          <div className="flex-shrink-0 p-4 border-b border-lia-border-subtle">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Filter className="w-4 h-4 text-gray-600" />
                <h3 className={textStyles.title}>
                  Filtros Avançados
                </h3>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onShowTableFiltersPanelChange(false)}
                className="h-7 w-7 p-0 hover:bg-gray-100"
              >
                <X className="w-4 h-4 text-gray-600" />
              </Button>
            </div>
            <p className={`${textStyles.description} mt-1`}>
              Refine os candidatos exibidos
            </p>
          </div>

          {/* Conteúdo dos Filtros - Scrollable */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {/* Filtro por Etapa */}
            <div className="space-y-2">
              <label className="text-xs font-medium text-gray-800 dark:text-lia-text-primary">
                Etapa do Pipeline
              </label>
              <div className="space-y-1.5">
                {dynamicStages.map((stage) => (
                  <label key={stage.id} className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={tableStageFilter.includes(stage.id)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          onTableStageFilterChange([...tableStageFilter, stage.id])
                        } else {
                          onTableStageFilterChange(tableStageFilter.filter(s => s !== stage.id))
                        }
                      }}
                      className="w-3.5 h-3.5 rounded-md border-lia-border-default text-gray-900 focus:ring-gray-900/20"
                    />
                    <span className="text-xs text-gray-600">
                      {stage.displayName}
                    </span>
                  </label>
                ))}
              </div>
            </div>

            {/* Filtro por Score LIA */}
            <div className="space-y-2">
              <label className="text-xs font-medium text-gray-800 dark:text-lia-text-primary">
                Score LIA Mínimo
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="range"
                  min="0"
                  max="100"
                  defaultValue="0"
                  className="flex-1 h-1.5 bg-gray-200 rounded-md appearance-none cursor-pointer accent-gray-900"
                />
                <span className="text-xs text-gray-600 w-8 text-right">0%</span>
              </div>
            </div>

            {/* Filtro por Status */}
            <div className="space-y-2">
              <label className="text-xs font-medium text-gray-800 dark:text-lia-text-primary">
                Status
              </label>
              <div className="space-y-1.5">
                {['Novo', 'Em análise', 'Aguardando aprovação', 'Triado aprovado', 'Negociação'].map((status) => (
                  <label key={status} className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      className="w-3.5 h-3.5 rounded-md border-lia-border-default text-gray-900 focus:ring-gray-900/20"
                    />
                    <span className="text-xs text-gray-600">
                      {status}
                    </span>
                  </label>
                ))}
              </div>
            </div>

            {/* Filtro por Modelo de Trabalho */}
            <div className="space-y-2">
              <label className="text-xs font-medium text-gray-800 dark:text-lia-text-primary">
                Modelo de Trabalho
              </label>
              <div className="space-y-1.5">
                {['Remoto', 'Híbrido', 'Presencial'].map((modelo) => (
                  <label key={modelo} className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      className="w-3.5 h-3.5 rounded-md border-lia-border-default text-gray-900 focus:ring-gray-900/20"
                    />
                    <span className="text-xs text-gray-600">
                      {modelo}
                    </span>
                  </label>
                ))}
              </div>
            </div>
          </div>

          {/* Footer com Ações */}
          <div className="flex-shrink-0 p-4 border-t border-lia-border-subtle bg-gray-50">
            <div className="flex gap-2">
              <button
                onClick={() => {
                  onTableStageFilterChange([])
                }}
                className="flex-1 px-3 py-2 text-xs font-medium text-gray-600 bg-lia-bg-primary border border-lia-border-subtle rounded-md hover:bg-gray-50 transition-colors"

              >
                Limpar
              </button>
              <button
                onClick={() => onShowTableFiltersPanelChange(false)}
                className="flex-1 px-3 py-2 text-xs font-medium text-white rounded-md transition-colors bg-gray-800"
              >
                Aplicar
              </button>
            </div>
          </div>
        </Card>
      </div>
    )}

    {/* Conteúdo da Tabela */}
    <div className="flex-1 overflow-hidden bg-gray-50 dark:bg-gray-950 flex flex-col min-w-0">
      <div className="flex-1 overflow-auto px-4 py-2">
      {/* Tabela Elegante - Unified Component */}
      {(() => {
        const nameCol = getColumnDefinition('candidate')
        const titleCol = getColumnDefinition('role')
        const companyCol = getColumnDefinition('currentCompany')

        const unifiedColumns: TableColumn[] = [
          { id: 'quickActions', label: 'Aprovação', visible: true, sortable: false, align: 'center', width: 120 },
          { id: 'id', label: 'ID', visible: true, sortable: false, width: 55 },
          { id: 'score', label: 'Geral', visible: true, sortable: true, width: 70 },
          { id: 'liaScore', label: 'Triagem', visible: true, sortable: true, width: 80 },
          { id: 'fitScore', label: 'CV', visible: true, sortable: true, width: 60 },
          { id: 'technicalTestScore', label: 'Técnico', visible: true, sortable: true, width: 75 },
          { id: 'englishTestScore', label: 'Inglês', visible: true, sortable: true, width: 70 },
          { id: 'bigFive', label: 'B5', visible: true, sortable: false, width: 55 },
          { id: 'name', label: nameCol?.label || 'Candidato', visible: true, sortable: nameCol?.sortable ?? true, width: 280 },
          { id: 'role', label: titleCol?.label || 'Cargo', visible: true, sortable: titleCol?.sortable ?? false, width: 150 },
          { id: 'currentCompany', label: companyCol?.label || 'Empresa', visible: true, sortable: companyCol?.sortable ?? false, width: companyCol?.width || 130 },
          { id: 'stage', label: 'Etapa', visible: true, sortable: true, width: 85 },
          { id: 'status', label: 'Status', visible: true, sortable: false, width: 85 }
        ]

        return (
          <UnifiedCandidateTable
            candidates={getPaginatedCandidates().candidates}
            columns={unifiedColumns}
            selectedIds={selectedCandidates}
            sortConfig={tableSortColumn ? {
              field: tableSortColumn,
              direction: tableSortDirection
            } : undefined}
            showCheckboxes={true}
            emptyMessage="Nenhum candidato nesta etapa"
            enableColumnResize={true}
            isInteractive={true}
            jobVacancyId={jobVacancyId}
            onColumnResize={onColumnResize}
            onCandidateClick={onCandidateClick}
            onSelectionChange={(newSelection) => onSelectionChange(newSelection)}
            onSortChange={(config) => {
              onSortChange(config)
            }}
            onStatusChange={onStatusChange}
            onTransitionRequest={onTransitionRequest}
            renderCustomHeader={(columnId: string, defaultLabel: string) => {
              if (columnId === 'quickActions') {
                const isSat = saturationData?.is_saturated || (saturationData?.saturation_percentage ?? 0) >= 90
                return (
                  <span className="flex items-center gap-1 whitespace-nowrap">
                    {defaultLabel}
                    {isSat && saturationData && (
                      <span
                        className={`inline-flex items-center gap-0.5 px-1 py-0.5 rounded-md text-micro font-medium font-['Open_Sans'] ${
                          saturationData.is_saturated
                            ? 'text-status-error bg-status-error/10 border border-status-error/30'
                            : 'text-status-warning bg-status-warning/10 border border-status-warning/30'
                        }`}
                        title={`Pipeline ${saturationData.is_saturated ? 'Saturado' : 'Quase saturado'} (${saturationData.approved_count}/${saturationData.saturation_threshold})`}
                      >
                        <AlertTriangle className="w-2.5 h-2.5" />
                        {saturationData.approved_count}/{saturationData.saturation_threshold}
                      </span>
                    )}
                  </span>
                )
              }
              return null
            }}
            renderCustomCell={(candidate: KanbanCandidate, columnId: string) => {
              const ranking = calculateNotaLiaGeral(candidate)
              const alerts = getLiaAlerts(candidate)
              const urgency = getUrgencyLevel(ranking)

              switch (columnId) {
                case 'id':
                  return (
                    <div className="text-xs font-mono text-gray-600 dark:text-lia-text-tertiary">
                      {candidate.candidateCode || candidate.id?.substring(0, 6).toUpperCase()}
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
 <span className={`text-xs font-semibold ${hasNotaGeral ? 'text-gray-950' : 'text-gray-400 dark:text-gray-600'}`}>
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
                      <Brain className={`w-3.5 h-3.5 ${hasTriagem ? 'text-wedo-cyan' : 'text-gray-400'}`} strokeWidth={2} />
 <span className={`text-xs font-semibold ${hasTriagem ? 'text-gray-950' : 'text-gray-400 dark:text-gray-600'}`}>
                        {hasTriagem ? formatScorePercent(triagemValue, 0) : '—'}
                      </span>
                    </div>
                  )

                case 'fitScore':
                  const hasFitScore = (candidate.skillsMatch !== null && candidate.skillsMatch !== undefined && candidate.skillsMatch > 0) || (candidate.fitScore !== null && candidate.fitScore !== undefined && candidate.fitScore > 0)
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
 <span className={`text-xs font-semibold ${hasFitScore ? 'text-gray-950' : 'text-gray-400 dark:text-gray-600'}`}>
                        {hasFitScore ? formatScorePercent(fitValue, 0) : '—'}
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
                        <span className="text-xs font-semibold text-gray-950 dark:text-gray-50">
                          {formatScorePercent(candidate.technicalTestScore, 0)}
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
                        <span className="text-xs font-semibold text-gray-950 dark:text-gray-50">
                          {formatScorePercent(candidate.englishTestScore, 0)}
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
 <span className={`text-xs font-semibold ${hasBigFive ? 'text-gray-950' : 'text-gray-400 dark:text-gray-600'}`}>
                        {hasBigFive && bigFiveAvg !== null ? bigFiveAvg : '—'}
                      </span>
                    </div>
                  )

                case 'quickActions':
                  const quickActionStage = (candidate.stage || candidate.etapa || 'funil').toLowerCase()
                  const isAlreadyDecided = quickActionStage === 'aprovados' || quickActionStage === 'reprovados'
                  const showNeedsAction = candidate.needsAction === true

                  if (isAlreadyDecided) {
                    return null
                  }

                  return (
                    <div className="relative flex items-center justify-center">
                      {/* Indicador "Ação Necessária" - aparece quando não está em hover */}
                      {showNeedsAction && (
                        <div className="flex items-center gap-1 group-hover:hidden transition-opacity">
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
                          className="w-7 h-7 rounded-full flex items-center justify-center hover:opacity-80 transition-opacity bg-gray-800"
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
                          className="w-7 h-7 rounded-full flex items-center justify-center hover:opacity-80 transition-opacity bg-wedo-coral"
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
                  const avatarUrl = candidate.avatar?.startsWith('http') ? candidate.avatar : getAvatarUrl(candidate.id || '', candidate.name || '')
                  const isDemo = !candidate.avatar?.startsWith('http') || candidate.isDemo
                  return (
                    <div className="flex items-center gap-2">
                      <div className="relative">
                        <Avatar className="w-8 h-8">
                          <AvatarImage src={avatarUrl} alt={candidate.name} />
                          <AvatarFallback>{candidate.name.split(' ').map((n: string) => n[0]).join('')}</AvatarFallback>
                        </Avatar>
                        {viewedCandidateIds.has(candidate.id) && (
                          <div className="absolute -bottom-0.5 -right-0.5 w-4 h-4 bg-gray-300 rounded-full flex items-center justify-center border border-white" title="Perfil visualizado">
                            <Eye className="w-2.5 h-2.5 text-white" />
                          </div>
                        )}
                      </div>
                      <div className="flex items-center gap-1.5">
                        {isDemo && (
                          <span className="text-micro font-medium text-gray-400 dark:text-gray-500">[D]</span>
                        )}
                        <span className="font-medium text-sm text-gray-950 dark:text-gray-50">
                          {candidate.name}
                        </span>
                        {(() => {
                          const dataRequest = getDataRequestForCandidate(candidate.id)
                          if (!dataRequest) return null
                          return (
                            <DataRequestIndicator
                              candidateId={candidate.id}
                              status={dataRequest.status}
                              fieldsRequested={dataRequest.fieldsRequested}
                              fieldsCompleted={dataRequest.fieldsCompleted}
                              expiresAt={dataRequest.expiresAt || undefined}
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
                    <div className="text-xs text-gray-950 dark:text-gray-50">
                      {candidate.role || candidate.position || 'UX Designer'}
                    </div>
                  )

                case 'currentCompany':
                  return (
                    <div className="text-xs text-gray-950 dark:text-gray-50">
                      {candidate.currentCompany || (candidate.source === 'LinkedIn' ? 'TechCorp' : 'Digital Agency')}
                    </div>
                  )

                case 'stage': {
                  const stageDropdownStages = dynamicStages.map(s => ({ id: s.id, name: s.name, displayName: s.displayName, color: s.color }))
                  const currentStageObj = stageDropdownStages.find(s => s.id === (candidate.stageId || candidate.stage))
                  return (
                    <Popover>
                      <PopoverTrigger asChild>
                        <button className="inline-flex items-center gap-1 group/stage" onClick={(e) => e.stopPropagation()}>
                          <Badge
                            className="text-xs font-semibold border-0 whitespace-nowrap text-gray-950 dark:text-gray-50 cursor-pointer"
                            style={{backgroundColor: currentStageObj?.color || 'var(--gray-200)'}}
                          >
                            {currentStageObj?.displayName || candidate.stage}
                          </Badge>
                          <ChevronDown className="w-3 h-3 text-gray-400 group-hover/stage:text-gray-600 transition-colors" />
                        </button>
                      </PopoverTrigger>
                      <PopoverContent className="w-44 p-1.5" align="start" sideOffset={4}>
                        <div className="space-y-0.5">
                          {stageDropdownStages.map((stage) => {
                            const isCurrent = stage.id === (candidate.stageId || candidate.stage)
                            return (
                              <button
                                key={stage.id}
                                className={`w-full flex items-center gap-2 px-2 py-1.5 rounded-md text-xs transition-colors ${
                                  isCurrent
                                    ? 'bg-gray-100 dark:bg-lia-bg-secondary font-bold'
                                    : 'hover:bg-gray-50 dark:hover:bg-gray-800/50'
                                }`}

                                onClick={() => {
                                  if (!isCurrent) {
                                    onTransitionRequired([candidate], candidate.stageId || candidate.stage, stage.id)
                                  }
                                }}
                              >
                                <div
                                  className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                                  style={{backgroundColor: stage.color}}
                                />
                                <span className="flex-1 text-left text-gray-800 dark:text-lia-text-primary truncate">
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
                        candidateId={candidate.id}
                        candidateName={candidate.name}
                        stage={candidate.stage}
                        subStatus={candidate.sub_status || candidate.status}
                        jobVacancyId={jobVacancyId}
                        onStatusChange={onStatusChange}
                      />
                      {hasScheduledInterview && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            const stage = candidate.stageId || candidate.stage || 'interview_hr'
                            const dateStr = candidate.interviewDate || new Date(candidate.agendada).toLocaleDateString('pt-BR', { day: 'numeric', month: 'long', hour: '2-digit', minute: '2-digit' })
                            onSetTransitionInitialPrompt(`O recrutador quer gerenciar a entrevista de ${candidate.name} agendada para ${dateStr}. Pergunte se quer alterar o horário (peça nova data/hora) ou cancelar. Se cancelar, pergunte para qual etapa quer mover o candidato.`)
                            onSetTransitionAllowStageSelection(true)
                            onSetTransitionInterviewAlert({ name: candidate.name, date: dateStr })
                            openTransition([candidate], stage, stage)
                          }}
                          className="w-5 h-5 rounded-md flex items-center justify-center text-wedo-cyan-dark hover:bg-wedo-cyan/10 dark:hover:bg-wedo-cyan-dark/20 transition-colors flex-shrink-0"
                          title={`Gerenciar entrevista — ${candidate.interviewDate || new Date(candidate.agendada).toLocaleDateString('pt-BR')}`}
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
                  ) : <span className="text-xs text-gray-400">—</span>

                case 'is_decision_maker':
                  return candidate.is_decision_maker ? (
                    <Badge className="text-xs bg-wedo-purple/15 text-wedo-purple">Decision Maker</Badge>
                  ) : <span className="text-xs text-gray-400">—</span>

                case 'is_top_universities':
                  return candidate.is_top_universities ? (
                    <Badge className="text-xs bg-gray-100 dark:bg-lia-bg-secondary text-gray-700 dark:text-lia-text-secondary">Top University</Badge>
                  ) : <span className="text-xs text-gray-400">—</span>

                case 'is_hiring':
                  return candidate.is_hiring ? (
                    <Badge className="text-xs bg-wedo-orange/15 text-wedo-orange">Contratando</Badge>
                  ) : <span className="text-xs text-gray-400">—</span>

                case 'headline':
                  return <span className="text-xs text-gray-800 dark:text-lia-text-primary truncate">{candidate.headline || ''}</span>

                case 'expertise':
                  const expertiseArray = candidate.expertise
                  return <span className="text-xs text-gray-800 dark:text-lia-text-primary truncate">{Array.isArray(expertiseArray) ? expertiseArray.join(', ') : (expertiseArray || '')}</span>

                case 'linkedin_followers_count':
                  return candidate.linkedin_followers_count ? (
                    <span className="text-xs text-gray-800 dark:text-lia-text-primary">{candidate.linkedin_followers_count.toLocaleString('pt-BR')}</span>
                  ) : <span className="text-xs text-gray-400">—</span>

                case 'linkedin_connections_count':
                  return candidate.linkedin_connections_count ? (
                    <span className="text-xs text-gray-800 dark:text-lia-text-primary">{candidate.linkedin_connections_count.toLocaleString('pt-BR')}</span>
                  ) : <span className="text-xs text-gray-400">—</span>

                case 'outreach_message':
                  return candidate.outreach_message ? (
                    <div className="flex items-center gap-1">
                      <span className="text-xs text-gray-800 dark:text-lia-text-primary truncate max-w-sidebar-content">{candidate.outreach_message.slice(0, 50)}...</span>
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          navigator.clipboard.writeText(candidate.outreach_message!)
                        }}
                        className="p-0.5 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-md"
                        title="Copiar mensagem"
                      >
                        <Copy className="w-3 h-3 text-gray-500" />
                      </button>
                    </div>
                  ) : <span className="text-xs text-gray-400">—</span>

                case 'best_personal_email':
                  return candidate.best_personal_email ? (
                    <a href={`mailto:${candidate.best_personal_email}`} className="text-xs text-gray-700 hover:text-gray-900 hover:underline truncate dark:text-lia-text-secondary dark:hover:text-gray-100">
                      {candidate.best_personal_email}
                    </a>
                  ) : <span className="text-xs text-gray-400">—</span>

                case 'phone_types':
                  if (!candidate.phone_types || Object.keys(candidate.phone_types).length === 0) {
                    return <span className="text-xs text-gray-400">—</span>
                  }
                  const activePhoneTypes = Object.entries(candidate.phone_types)
                    .filter(([_, active]) => active)
                    .map(([type]) => type)
                  return <span className="text-xs text-gray-800 dark:text-lia-text-primary">{activePhoneTypes.join(', ') || '—'}</span>

                case 'estimated_age':
                  return candidate.estimated_age ? (
                    <span className="text-xs text-gray-800 dark:text-lia-text-primary">{candidate.estimated_age} anos</span>
                  ) : <span className="text-xs text-gray-400">—</span>

                case 'match_reasoning':
                  return candidate.pearch_insights?.match_reasoning ? (
                    <span className="text-xs text-gray-800 dark:text-lia-text-primary truncate" title={candidate.pearch_insights.match_reasoning}>
                      {candidate.pearch_insights.match_reasoning.slice(0, 60)}...
                    </span>
                  ) : <span className="text-xs text-gray-400">—</span>

                case 'overall_summary':
                  return candidate.pearch_insights?.overall_summary ? (
                    <span className="text-xs text-gray-800 dark:text-lia-text-primary truncate" title={candidate.pearch_insights.overall_summary}>
                      {candidate.pearch_insights.overall_summary.slice(0, 60)}...
                    </span>
                  ) : <span className="text-xs text-gray-400">—</span>

                case 'query_insights':
                  const queryInsightsData = candidate.pearch_insights?.query_insights
                  if (!queryInsightsData || queryInsightsData.length === 0) {
                    return <span className="text-xs text-gray-400">—</span>
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
                          <span className={`${textStyles.caption} dark:!text-gray-400 truncate max-w-[150px]`} title={insight.subquery}>
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
                    <span className="text-xs text-gray-800 dark:text-lia-text-primary truncate">{candidate.pearch_insights.overall_summary.slice(0, 50)}...</span>
                  ) : <span className="text-xs text-gray-400">—</span>

                case 'middle_name':
                  return candidate.middle_name ? (
                    <span className="text-xs text-gray-800 dark:text-lia-text-primary truncate">{candidate.middle_name}</span>
                  ) : <span className="text-xs text-gray-400">—</span>

                case 'best_business_email':
                  return candidate.best_business_email ? (
                    <a href={`mailto:${candidate.best_business_email}`} className="text-xs text-gray-700 hover:text-gray-900 hover:underline truncate dark:text-lia-text-secondary dark:hover:text-gray-100">
                      {candidate.best_business_email}
                    </a>
                  ) : <span className="text-xs text-gray-400">—</span>

                case 'personal_emails':
                  const personalEmails = candidate.personal_emails
                  if (!personalEmails || personalEmails.length === 0) {
                    return <span className="text-xs text-gray-400">—</span>
                  }
                  return (
                    <span className="text-xs text-gray-800 dark:text-lia-text-primary truncate" title={personalEmails.join(', ')}>
                      {personalEmails.length === 1 ? personalEmails[0] : `${personalEmails[0]} (+${personalEmails.length - 1})`}
                    </span>
                  )

                case 'business_emails':
                  const businessEmails = candidate.business_emails
                  if (!businessEmails || businessEmails.length === 0) {
                    return <span className="text-xs text-gray-400">—</span>
                  }
                  return (
                    <span className="text-xs text-gray-800 dark:text-lia-text-primary truncate" title={businessEmails.join(', ')}>
                      {businessEmails.length === 1 ? businessEmails[0] : `${businessEmails[0]} (+${businessEmails.length - 1})`}
                    </span>
                  )

                case 'company_followers_count':
                  return candidate.company_followers_count != null ? (
                    <span className="text-xs text-gray-800 dark:text-lia-text-primary">{candidate.company_followers_count.toLocaleString('pt-BR')}</span>
                  ) : <span className="text-xs text-gray-400">—</span>

                case 'company_keywords':
                  const companyKeywords = candidate.company_keywords
                  if (!companyKeywords || companyKeywords.length === 0) {
                    return <span className="text-xs text-gray-400">—</span>
                  }
                  return (
                    <div className="flex flex-wrap gap-1">
                      {companyKeywords.slice(0, 3).map((keyword: string, idx: number) => (
                        <Badge key={idx} variant="outline" className="text-micro px-1 py-0 bg-gray-50 text-gray-700 dark:bg-lia-bg-elevated dark:text-lia-text-secondary">
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
                  const hasTriagemData = candidate.triagemHistory || candidate.screeningHistory || candidateStage.toLowerCase() !== 'funil'
                  return (
                    <div className="flex items-center justify-center gap-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        className={`h-7 w-7 p-0 ${hasAnalysisData ? 'text-gray-700 hover:text-gray-900 hover:bg-gray-100' : 'text-gray-400 cursor-not-allowed'}`}
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
                        className={`h-7 w-7 p-0 ${hasTriagemData ? 'text-gray-700 hover:text-gray-900 hover:bg-gray-100' : 'text-gray-400 cursor-not-allowed'}`}
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
                            className="p-1.5 rounded-md hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                            title="Mais ações"
                          >
                            <MoreVertical className="w-4 h-4 text-gray-500" />
                          </button>
                        </PopoverTrigger>
                        <PopoverContent align="end" className="w-48 p-1">
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              onOpenAnalysis(candidate)
                            }}
                            className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-800 dark:text-lia-text-primary hover:bg-gray-100 dark:hover:bg-gray-800 rounded-md"
                          >
                            <Eye className="w-4 h-4" />
                            Ver perfil completo
                          </button>
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              onOpenTriagem(candidate)
                            }}
                            className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-800 dark:text-lia-text-primary hover:bg-gray-100 dark:hover:bg-gray-800 rounded-md"
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
                            className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-800 dark:text-lia-text-primary hover:bg-gray-100 dark:hover:bg-gray-800 rounded-md"
                          >
                            <Fingerprint className="w-4 h-4 text-gray-600" />
                            Ver BigFive
                          </button>
                          <div className="my-1 border-t border-lia-border-subtle dark:border-lia-border-subtle" />
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              const cStage = (candidate.stage || candidate.etapa || 'funil').toLowerCase()
                              if (cStage === 'screening' || cStage === 'triagem') {
                                onApproveFromScreening(candidate)
                              } else {
                                openDecisionFlowModal(candidate, 'approve')
                              }
                            }}
                            className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-800 dark:text-lia-text-primary hover:bg-gray-100 dark:hover:bg-gray-800 rounded-md"
                          >
                            <ThumbsUp className="w-4 h-4" />
                            Aprovar
                          </button>
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              const cStage = (candidate.stage || candidate.etapa || 'funil').toLowerCase()
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
            }}
            getNeedsAction={(candidate: KanbanCandidate) => {
              const stage = (candidate.stage || candidate.etapa || 'funil').toLowerCase()
              return stage === 'funil' || stage === 'triagem' || candidate.needsAction === true || candidate.status === 'triado_aprovado'
            }}
            renderActions={(candidate: KanbanCandidate) => {
              const stage = (candidate.stage || candidate.etapa || 'funil').toLowerCase()
              const showApproveReject = stage === 'funil' || stage === 'triagem'
              return (
                <div className="flex items-center justify-center gap-1" onClick={(e) => e.stopPropagation()}>
                  {showApproveReject && (
                    <>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-6 px-2 bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200 rounded-full text-micro font-semibold"
                        title="Aprovar candidato"
                        onClick={(e) => {
                          e.stopPropagation()
                          onApproveCandidate(candidate)
                        }}
                      >
                        <ThumbsUp className="w-3 h-3 mr-0.5" />
                        Aprovar
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-6 px-2 bg-status-error hover:bg-status-error text-white rounded-full text-micro font-semibold"
                        title="Reprovar candidato"
                        onClick={(e) => {
                          e.stopPropagation()
                          if (stage === 'screening' || stage === 'triagem') {
                            onRejectFromScreening(candidate)
                          } else {
                            onRejectCandidate(candidate)
                          }
                        }}
                      >
                        <XCircle className="w-3 h-3 mr-0.5" />
                        Reprovar
                      </Button>
                    </>
                  )}
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
                        <MoreVertical className="w-4 h-4 text-gray-500 hover:text-gray-800 dark:text-lia-text-primary" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end" className="w-48">
                      <DropdownMenuItem onClick={() => onCandidateClick(candidate)}>
                        <Eye className="w-4 h-4 mr-2" />
                        Ver Perfil
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() => onOpenAnalysis(candidate)}>
                        <Target className="w-4 h-4 mr-2" />
                        Análise CV
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() => onOpenTriagem(candidate)}>
                        <Brain className="w-4 h-4 mr-2 text-wedo-cyan" />
                        Ver Triagem
                      </DropdownMenuItem>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem onClick={() => onApproveCandidate(candidate)}>
                        <ThumbsUp className="w-4 h-4 mr-2" />
                        Aprovar
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() => {
                        if (stage === 'screening' || stage === 'triagem') {
                          onRejectFromScreening(candidate)
                        } else {
                          onRejectCandidate(candidate)
                        }
                      }} className="text-wedo-coral">
                        <XCircle className="w-4 h-4 mr-2" />
                        Reprovar
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              )
            }}
            getStageBorderColor={(candidate: KanbanCandidate) => {
              const stage = (candidate.stage || candidate.etapa || 'funil').toLowerCase()
              const stageColors: Record<string, string> = {
                'funil': 'var(--gray-600)',
                'triagem': 'var(--status-warning)',
                'entrevista': 'var(--wedo-purple)',
                'final': 'var(--gray-600)',
                'aprovados': 'var(--status-success)',
                'reprovados': 'var(--status-error)'
              }
              return stageColors[stage] || 'var(--gray-950)'
            }}
            className="max-h-[calc(100vh-22rem)]"
          />
        )
      })()}

      {/* Paginação */}
      {getPaginatedCandidates().totalPages > 1 && (
        <div className="bg-white dark:bg-lia-bg-primary rounded-md p-3">
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-600 dark:text-lia-text-tertiary">
              Mostrando {((currentPage - 1) * itemsPerPage) + 1} - {Math.min(currentPage * itemsPerPage, getPaginatedCandidates().total)} de {getPaginatedCandidates().total} candidatos
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => onCurrentPageChange(1)}
                disabled={currentPage === 1}
                className="h-8"
              >
                Primeira
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => onCurrentPageChange(Math.max(1, currentPage - 1))}
                disabled={currentPage === 1}
                className="h-8"
              >
                Anterior
              </Button>

              {/* Page numbers */}
              <div className="flex items-center gap-1">
                {Array.from({ length: getPaginatedCandidates().totalPages }, (_, i) => i + 1)
                  .filter(page => {
                    // Show first page, last page, current page, and pages around current
                    return page === 1 ||
                           page === getPaginatedCandidates().totalPages ||
                           (page >= currentPage - 1 && page <= currentPage + 1)
                  })
                  .map((page, index, array) => (
                    <React.Fragment key={page}>
                      {/* Show ellipsis if there's a gap */}
                      {index > 0 && page - array[index - 1] > 1 && (
                        <span className="px-2 text-gray-600">...</span>
                      )}
                      <Button
                        variant={currentPage === page ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => onCurrentPageChange(page)}
                        className="h-8 w-8 p-0"
                      >
                        {page}
                      </Button>
                    </React.Fragment>
                  ))
                }
              </div>

              <Button
                variant="outline"
                size="sm"
                onClick={() => onCurrentPageChange(Math.min(getPaginatedCandidates().totalPages, currentPage + 1))}
                disabled={currentPage === getPaginatedCandidates().totalPages}
                className="h-8"
              >
                Próxima
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => onCurrentPageChange(getPaginatedCandidates().totalPages)}
                disabled={currentPage === getPaginatedCandidates().totalPages}
                className="h-8"
              >
                Última
              </Button>
            </div>
          </div>
        </div>
      )}
      </div>
    </div>
    {/* Fecha o Conteúdo da Tabela */}

    {/* Preview do Candidato - Painel Lateral Direito */}
    {isPreviewOpen && previewCandidate && (
      <div className={`flex-shrink-0 transition-colors duration-300 ${isPreviewMaximized ? 'w-[600px]' : 'w-panel-lg'}`}>
        <div className="bg-white dark:bg-lia-bg-secondary rounded-md border border-lia-border-subtle dark:border-lia-border-subtle h-[calc(100vh-6rem)] overflow-hidden">
        <React.Suspense fallback={null}>
          <CandidatePreviewDynamic
            candidate={previewCandidate}
            isOpen={isPreviewOpen}
            onClose={onClosePreview}
            isMaximized={isPreviewMaximized}
            onToggleMaximize={onTogglePreviewMaximize}
            candidates={(() => {
              const currentColumn = Object.keys(candidatesData).find(col =>
                candidatesData[col].some((c) => c.id === previewCandidate?.id)
              )
              return currentColumn ? candidatesData[currentColumn] : []
            })()}
            currentIndex={(() => {
              const currentColumn = Object.keys(candidatesData).find(col =>
                candidatesData[col].some((c) => c.id === previewCandidate?.id)
              )
              return currentColumn ? candidatesData[currentColumn].findIndex((c) => c.id === previewCandidate?.id) : 0
            })()}
            onNavigateCandidate={onNavigateCandidate}
            onOpenFullPage={onCandidatePageOpen}
            onScheduleInterview={onScheduleInterview}
            onAddToVacancy={onAddToVacancy}
            onToggleFavorite={onToggleFavorite}
            onWSIScreening={onSendWSIInvite}
            onOpenTriagemDetails={onOpenTriagem}
            isFavorite={previewCandidate ? favoriteCandidates.has(previewCandidate.id) : false}
            onSendEmail={(candidate) => onSendEmail(candidate)}
            onSendWhatsApp={(candidate) => onSendWhatsApp(candidate)}
            onSendTriagem={(candidate) => onSendTriagem(candidate)}
            onSendAgendamento={(candidate) => onSendAgendamento(candidate)}
            onSendFeedback={(candidate) => onSendFeedback(candidate)}
            jobId={jobVacancyId}
          />
        </React.Suspense>
        </div>
      </div>
    )}

    {/* Column Configuration Sidebar - Lado Direito */}
    <KanbanColumnConfigPanel
      open={showColumnConfig}
      onClose={() => onShowColumnConfigChange(false)}
      tableColumns={tableColumns}
      onTableColumnsChange={onTableColumnsChange}
      onResetColumns={() => onTableColumnsChange(getDefaultTableColumns())}
    />
    </>
  )
}
