"use client"

import React from "react"
import { useTranslations } from "next-intl"
import { Button } from "@/components/ui/button"
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
import { KanbanTableFiltersPanel } from "@/components/pages/job-kanban/KanbanTableFiltersPanel"
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

import { KanbanTablePagination } from "./KanbanTablePagination"
import { KanbanCandidatePreviewPanel } from "./KanbanCandidatePreviewPanel"
import { createKanbanCellRenderer, type KanbanTableCellRendererProps } from "./KanbanTableCellRenderer"
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
  subStatuses?: Array<{ name: string; display_name: string }>
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
  const t = useTranslations('kanban')
  const itemsPerPage = 50


  const renderCustomCell = createKanbanCellRenderer(({
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
    onDirectTransition: async (candidate, toStage, subStatus, jvId) => {
      const id = candidate.id
      await fetch(`/api/backend-proxy/candidates/${encodeURIComponent(id)}/stage`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ stage: toStage, sub_status: subStatus, job_vacancy_id: jvId || jobVacancyId }),
      })
      onTransitionRequired([candidate], (candidate.stageId as string | undefined) || (candidate.stage as string | undefined) || '', toStage)
    },
    onCandidateClick,
  }) as unknown as KanbanTableCellRendererProps)
  return (
    <>
    {/* Painel de Filtros - TABLE */}
    {showTableFiltersPanel && (
      <KanbanTableFiltersPanel
        onShowTableFiltersPanelChange={onShowTableFiltersPanelChange}
        dynamicStages={dynamicStages}
        tableStageFilter={tableStageFilter}
        onTableStageFilterChange={onTableStageFilterChange}
      />
    )}

    {/* Conteúdo da Tabela + Preview — envolvidos em flex explícito */}
    <div className="flex-1 flex overflow-hidden min-w-0">
    <div className="flex-1 overflow-hidden bg-lia-bg-primary dark:bg-lia-bg-primary flex flex-col min-w-0">
      <div className="flex-1 overflow-auto px-4 py-2 flex flex-col">
      {/* Tabela Elegante - Unified Component */}
      {(() => {
        const nameCol = getColumnDefinition('candidate')
        const titleCol = getColumnDefinition('role')
        const companyCol = getColumnDefinition('currentCompany')

        const unifiedColumns: TableColumn[] = [
          { id: 'quickActions', label: t('tableColApproval'), visible: true, sortable: false, align: 'center', width: 120 },
          { id: 'id', label: 'ID', visible: true, sortable: false, width: 55 },
          { id: 'score', label: t('scoreGeral'), visible: true, sortable: true, width: 70 },
          { id: 'liaScore', label: t('scoreTriagem'), visible: true, sortable: true, width: 80 },
          { id: 'fitScore', label: t('scoreCV'), visible: true, sortable: true, width: 60 },
          { id: 'technicalTestScore', label: t('scoreTecnico'), visible: true, sortable: true, width: 75 },
          { id: 'englishTestScore', label: t('scoreIngles'), visible: true, sortable: true, width: 70 },
          { id: 'bigFive', label: t('scoreB5'), visible: true, sortable: false, width: 55 },
          { id: 'name', label: nameCol?.label || t('tableColCandidate'), visible: true, sortable: nameCol?.sortable ?? true, width: 280 },
          { id: 'role', label: titleCol?.label || t('tableColRole'), visible: true, sortable: titleCol?.sortable ?? false, width: 150 },
          { id: 'currentCompany', label: companyCol?.label || t('tableColCompany'), visible: true, sortable: companyCol?.sortable ?? false, width: companyCol?.width || 130 },
          { id: 'stage', label: t('tableColStage'), visible: true, sortable: true, width: 85 },
          { id: 'status', label: t('tableColStatus'), visible: true, sortable: false, width: 85 }
        ]

        return (
          <UnifiedCandidateTable
            candidates={getPaginatedCandidates().candidates as unknown as Parameters<typeof UnifiedCandidateTable>[0]["candidates"]}
            columns={unifiedColumns}
            selectedIds={selectedCandidates}
            sortConfig={tableSortColumn ? {
              field: tableSortColumn,
              direction: tableSortDirection
            } : undefined}
            showCheckboxes={true}
            emptyMessage={t('tableEmptyMessage')}
            enableVirtualScroll={getPaginatedCandidates().candidates.length > 50}
            enableColumnResize={true}
            isInteractive={true}
            jobVacancyId={jobVacancyId}
            onColumnResize={onColumnResize}
            onCandidateClick={onCandidateClick as unknown as Parameters<typeof UnifiedCandidateTable>[0]["onCandidateClick"]}
            onSelectionChange={(newSelection) => onSelectionChange(newSelection)}
            onSortChange={(config) => {
              onSortChange(config)
            }}
            onStatusChange={onStatusChange as unknown as Parameters<typeof UnifiedCandidateTable>[0]["onStatusChange"]}
            onTransitionRequest={onTransitionRequest as unknown as Parameters<typeof UnifiedCandidateTable>[0]["onTransitionRequest"]}
            renderCustomHeader={(columnId: string, defaultLabel: string) => {
              if (columnId === 'quickActions') {
                const isSat = saturationData?.is_saturated || (saturationData?.saturation_percentage ?? 0) >= 90
                return (
                  <span className="flex items-center gap-1 whitespace-nowrap">
                    {defaultLabel}
                    {isSat && saturationData && (
                      <span
                        className={`inline-flex items-center gap-0.5 px-1 py-0.5 rounded-md text-micro font-medium ${
                          saturationData.is_saturated
                            ? 'text-status-error bg-status-error/10 border border-status-error/30'
                            : 'text-status-warning bg-status-warning/10 border border-status-warning/30'
                        }`}
                        title={t('pipelineSaturationTitle', { status: saturationData.is_saturated ? t('pipelineSaturated') : t('pipelineAlmostSaturated'), count: String(saturationData.approved_count), threshold: String(saturationData.saturation_threshold) })}
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
            renderCustomCell={renderCustomCell as unknown as Parameters<typeof UnifiedCandidateTable>[0]["renderCustomCell"]}
            getNeedsAction={((candidate: KanbanCandidate): boolean => {
              const stage = ((candidate.stage as string | undefined) || (candidate.etapa as string | undefined) || 'funil').toLowerCase()
              return stage === 'funil' || stage === 'triagem' || candidate.needsAction === true || (candidate.status as string | undefined) === 'triado_aprovado'
            }) as unknown as Parameters<typeof UnifiedCandidateTable>[0]["getNeedsAction"]}
            renderActions={((candidate: KanbanCandidate): React.ReactNode => {
              const stage: string = ((candidate.stage as string | undefined) || (candidate.etapa as string | undefined) || 'funil').toLowerCase()
              const showApproveReject = stage === 'funil' || stage === 'triagem'
              return (
                <div className="flex items-center justify-center gap-1" onClick={(e) => e.stopPropagation()}>
                  {showApproveReject && (
                    <>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-6 px-2 bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:bg-lia-bg-secondary dark:hover:bg-lia-interactive-active rounded-full text-micro font-semibold"
                        title={t('approveCandidate')}
                        onClick={(e) => {
                          e.stopPropagation()
                          onApproveCandidate(candidate)
                        }}
                      >
                        <ThumbsUp className="w-3 h-3 mr-0.5" />
                        {t('approve')}
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-6 px-2 bg-status-error hover:bg-status-error text-white rounded-full text-micro font-semibold"
                        title={t('rejectCandidate')}
                        onClick={(e) => {
                          e.stopPropagation()
                          const rejectStage = stage as string
                          if (rejectStage === 'screening' || rejectStage === 'triagem') {
                            onRejectFromScreening(candidate)
                          } else {
                            onRejectCandidate(candidate)
                          }
                        }}
                      >
                        <XCircle className="w-3 h-3 mr-0.5" />
                        {t('reject')}
                      </Button>
                    </>
                  )}
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
                        <MoreVertical className="w-4 h-4 text-lia-text-tertiary hover:text-lia-text-primary" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end" className="w-48">
                      <DropdownMenuItem onClick={() => onCandidateClick(candidate)}>
                        <Eye className="w-4 h-4 mr-2" />
                        {t('viewProfile')}
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() => onOpenAnalysis(candidate)}>
                        <Target className="w-4 h-4 mr-2" />
                        {t('cvAnalysis')}
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() => onOpenTriagem(candidate)}>
                        <Brain className="w-4 h-4 mr-2 text-wedo-cyan" />
                        {t('viewScreening')}
                      </DropdownMenuItem>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem onClick={() => onApproveCandidate(candidate)}>
                        <ThumbsUp className="w-4 h-4 mr-2" />
                        {t('approve')}
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() => {
                        if (stage === 'screening' || stage === 'triagem') {
                          onRejectFromScreening(candidate)
                        } else {
                          onRejectCandidate(candidate)
                        }
                      }} className="text-wedo-coral">
                        <XCircle className="w-4 h-4 mr-2" />
                        {t('reject')}
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              )
            }) as unknown as Parameters<typeof UnifiedCandidateTable>[0]["renderActions"]}
            getStageBorderColor={((candidate: KanbanCandidate): string => {
              const stage = ((candidate.stage as string | undefined) || (candidate.etapa as string | undefined) || 'funil').toLowerCase()
              const stageColors: Record<string, string> = {
                'funil': 'var(--lia-text-secondary)',
                'triagem': 'var(--status-warning)',
                'entrevista': 'var(--wedo-purple)',
                'final': 'var(--lia-text-secondary)',
                'aprovados': 'var(--status-success)',
                'reprovados': 'var(--status-error)'
              }
              return stageColors[stage] || 'var(--lia-btn-primary-bg)'
            }) as unknown as Parameters<typeof UnifiedCandidateTable>[0]["getStageBorderColor"]}
            className=""
          />
        )
      })()}

      <div className="flex-1" aria-hidden="true" />
      {/* Paginação */}
      <KanbanTablePagination
        currentPage={currentPage}
        itemsPerPage={itemsPerPage}
        getPaginatedCandidates={getPaginatedCandidates}
        onCurrentPageChange={onCurrentPageChange}
      />
      </div>
    </div>
    {/* Fecha o Conteúdo da Tabela */}

    {/* Preview do Candidato - Painel Lateral Direito (dentro do flex wrapper) */}
    <KanbanCandidatePreviewPanel
      isPreviewOpen={isPreviewOpen}
      previewCandidate={previewCandidate as Record<string, unknown> | null | undefined}
      isPreviewMaximized={isPreviewMaximized}
      onClosePreview={onClosePreview}
      onTogglePreviewMaximize={onTogglePreviewMaximize}
      onNavigateCandidate={onNavigateCandidate}
      onCandidatePageOpen={onCandidatePageOpen as (candidate: Record<string, unknown>) => void}
      onScheduleInterview={onScheduleInterview as (candidate: Record<string, unknown>) => void}
      onAddToVacancy={onAddToVacancy as (candidate: Record<string, unknown>) => void}
      onToggleFavorite={onToggleFavorite as (candidate: Record<string, unknown>) => void}
      favoriteCandidates={favoriteCandidates}
      onSendWSIInvite={onSendWSIInvite as (candidate: Record<string, unknown>) => void}
      onSendEmail={onSendEmail as (candidate: Record<string, unknown>) => void}
      onSendWhatsApp={onSendWhatsApp as (candidate: Record<string, unknown>) => void}
      onSendTriagem={onSendTriagem as (candidate: Record<string, unknown>) => void}
      onSendAgendamento={onSendAgendamento as (candidate: Record<string, unknown>) => void}
      onSendFeedback={onSendFeedback as (candidate: Record<string, unknown>) => void}
      onOpenTriagem={onOpenTriagem as (candidate: Record<string, unknown>) => void}
      candidatesData={candidatesData as Record<string, Record<string, unknown>[]>}
      jobVacancyId={jobVacancyId}
    />
    </div>
    {/* Fecha o wrapper flex (tabela + preview) */}

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
