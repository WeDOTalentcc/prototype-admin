"use client"

import React from "react"
import {
  Briefcase, CheckCircle, CheckCircle2, Target, ChevronsLeftRight,
  Brain, Copy, Share2, UserCheck, X, ChevronLeft, ChevronRight, Loader2
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { EmptyState } from "@/components/ui/empty-state"
import { BulkActionsBar } from "@/components/ui/bulk-actions-bar"
import { LIAToolbarBrainButton } from "@/components/ui/lia-toolbar-brain-button"
import { InlineChatPanel } from "@/components/pages/jobs/InlineChatPanel"
import { TableFiltersPanel } from "@/components/pages/jobs/TableFiltersPanel"
import { JobPreviewPanel } from "@/components/pages/jobs/JobPreviewPanel"
import { JobsCompactTableView } from "@/components/pages/jobs/JobsCompactTableView"
import { ColumnConfigPanel } from "@/components/pages/jobs/ColumnConfigPanel"
import { toast } from "sonner"
import type { Job } from "@/components/jobs"
import type { ScreeningConfig } from "@/hooks/useScreeningConfig"
import type { JobVacancyMetrics } from "@/services/lia-api"

interface JobFiltersLocal {
  status?: { statuses?: string[]; stages?: string[]; priorities?: string[] }
  position?: { workModels?: string[]; levels?: string[]; locations?: string[] }
  team?: { departments?: string[] }
  publishing?: { channels?: string[]; unpublished?: boolean }
  funnel?: { emptyPipeline?: boolean }
  metrics?: { lowConversion?: boolean }
}

interface SavedSearchLocal {
  id: string
  name: string
  query?: string
  createdAt: Date | string
}

interface LiaInlineMessage {
  id: string
  role: "user" | "assistant"
  content: string
  timestamp: Date
  isTyping?: boolean
}

interface ColumnDefLocal {
  id: string
  label: string
  visible: boolean
  category?: string
}

interface ColumnViewLocal {
  id: string
  name: string
}

type RecentItem = {
  id: string
  type: "vaga" | "chat" | "candidato"
  title: string
  subtitle?: string
  meta?: Record<string, string | undefined>
}

interface JobsListContentProps {
  showExpandedLIA: boolean; setShowExpandedLIA: (v: boolean) => void
  showInlineChat: boolean; chatMode: "general" | "job-creation" | null; isChatFullscreen: boolean
  selectedJobsForBatch: Set<number>; filteredJobs: Job[]
  isLoadingJobs: boolean; isTableCollapsed: boolean
  searchTerm: string; selectedDaysFilter: string
  showTableFiltersPanel: boolean; setShowTableFiltersPanel: (v: boolean) => void
  showColumnConfig: boolean; setShowColumnConfig: (v: boolean) => void
  handleToggleColumnConfig: () => void; getActiveJobFiltersCount: () => number
  selectAllJobs: () => void; deselectAllJobs: () => void
  handleJobPublish: () => void; handleJobInsights: () => void
  handleJobDuplicate: () => void; handleJobToggleStatus: () => void
  handleJobAssignRecruiter: () => void; getSelectedJobsHaveActiveStatus: () => boolean
  toggleTableExpansion: () => void; setChatMode: (mode: "general" | "job-creation" | null) => void
  setSearchTerm: (v: string) => void; jobFilters: JobFiltersLocal; toggleJobFilter: (category: string, key: string, value: unknown) => void
  clearAllJobFilters: () => void; hasActiveFilters: () => boolean
  savedSearches: SavedSearchLocal[]; saveSearchAsTemplate: (name: string) => void
  handleApplySavedSearch: (id: string) => void; handleRenameSavedSearch: (id: string, name: string) => void; handleDeleteSavedSearch: (id: string) => void
  inlineChatInitialMessage?: string; liaInlineMessages: LiaInlineMessage[]; liaInlineLoading: boolean
  liaWidth: number; isResizingLIA: boolean; userCollapsedLIA: boolean
  liaPromptValue: string; setLiaPromptValue: (value: string | ((prev: string) => string)) => void
  closeChat: () => void; openGeneralChat: (msg?: string) => void
  openJobCreationChat: (msg?: string) => void; returnToGeneralChat: () => void
  returnToLateralPrompt: () => void; sendLiaInlineMessage: (content: string) => Promise<void>
  setUserCollapsedLIA: (v: boolean) => void; setIsChatFullscreen: (v: boolean) => void
  setIsResizingLIA: (v: boolean) => void; setLiaWidth: (v: number) => void
  setLiaInlineMessages: (msgs: LiaInlineMessage[]) => void
  liaInlineMessagesEndRef: React.RefObject<HTMLDivElement | null>
  onAddRecentItem?: (item: RecentItem) => void
  showJobPreview: boolean; previewJob: Job | null
  activePreviewTab: "screening" | "pipeline"; setActivePreviewTab: (tab: "screening" | "pipeline") => void
  previewWidth: number; setPreviewWidth: (v: number) => void
  setIsResizingPreview: (v: boolean) => void
  setShowJobPreview: (v: boolean) => void; setPreviewJob: (v: Job | null) => void
  handleJobClick: (job: Job) => void
  screeningConfig: ScreeningConfig | undefined; isLoadingScreeningConfig: boolean
  jobMetrics: JobVacancyMetrics | null; isLoadingJobMetrics: boolean
  columnConfig: ColumnDefLocal[]; visibleColumnIds: string[]; savedColumnViews: ColumnViewLocal[]
  toggleColumn: (id: string) => void; applyColumnView: (id: string) => void; deleteColumnView: (id: string) => void
  saveColumnView: (name: string) => void; resetColumnsToDefault: () => void
  statusOrder: readonly string[]; groupedJobs: Record<string, Job[]>
  jobsColumnOrder: string[]; hookToTableColumnMap: Record<string, string>
  jobsColumnWidths: Record<string, number>
  pinnedJobs: Set<number>; urgentJobs: Set<number>; favoriteJobs: Set<number>
  draggedJobColumnId: string | null; dragOverJobColumnId: string | null
  jobsSortColumn: string | null; jobsSortDirection: "asc" | "desc"
  toggleJobSelection: (id: number) => void; handleJobPreview: (job: Job) => void
  handleJobsSort: (column: string) => void; handleJobsColumnDragStart: (id: string, e: React.DragEvent) => void; handleJobsColumnDragOver: (id: string, e: React.DragEvent) => void
  handleJobsColumnDragLeave: () => void; handleJobsColumnDrop: (id: string, e: React.DragEvent) => void
  handleJobsColumnDragEnd: () => void; startJobsColumnResize: (column: string, e: React.MouseEvent) => void
  toggleUrgentJob: (id: number) => void; togglePinJob: (id: number) => void; toggleFavoriteJob: (id: number) => void
}

export function JobsListContent(props: JobsListContentProps) {
  const {
    showExpandedLIA, setShowExpandedLIA, showInlineChat, chatMode, isChatFullscreen,
    selectedJobsForBatch, filteredJobs, isLoadingJobs, isTableCollapsed,
    searchTerm, selectedDaysFilter, showTableFiltersPanel, setShowTableFiltersPanel,
    showColumnConfig, handleToggleColumnConfig, getActiveJobFiltersCount,
    selectAllJobs, deselectAllJobs, handleJobPublish, handleJobInsights,
    handleJobDuplicate, handleJobToggleStatus, handleJobAssignRecruiter,
    getSelectedJobsHaveActiveStatus, toggleTableExpansion, setChatMode,
    setSearchTerm, jobFilters, toggleJobFilter, clearAllJobFilters,
    hasActiveFilters, savedSearches, saveSearchAsTemplate, handleApplySavedSearch,
    handleRenameSavedSearch, handleDeleteSavedSearch,
    inlineChatInitialMessage, liaInlineMessages, liaInlineLoading,
    liaWidth, isResizingLIA, userCollapsedLIA, liaPromptValue, setLiaPromptValue,
    closeChat, openGeneralChat, openJobCreationChat, returnToGeneralChat,
    returnToLateralPrompt, sendLiaInlineMessage, setUserCollapsedLIA,
    setIsChatFullscreen, setIsResizingLIA, setLiaWidth, setLiaInlineMessages,
    liaInlineMessagesEndRef, onAddRecentItem,
    showJobPreview, previewJob, activePreviewTab, setActivePreviewTab,
    previewWidth, setPreviewWidth, setIsResizingPreview, setShowJobPreview,
    setPreviewJob, handleJobClick, screeningConfig, isLoadingScreeningConfig,
    jobMetrics, isLoadingJobMetrics,
    columnConfig, visibleColumnIds, savedColumnViews, toggleColumn,
    applyColumnView, deleteColumnView, saveColumnView, resetColumnsToDefault,
    statusOrder, groupedJobs, jobsColumnOrder, hookToTableColumnMap,
    jobsColumnWidths, pinnedJobs, urgentJobs, favoriteJobs,
    draggedJobColumnId, dragOverJobColumnId, jobsSortColumn, jobsSortDirection,
    toggleJobSelection, handleJobPreview, handleJobsSort,
    handleJobsColumnDragStart, handleJobsColumnDragOver, handleJobsColumnDragLeave,
    handleJobsColumnDrop, handleJobsColumnDragEnd, startJobsColumnResize,
    toggleUrgentJob, togglePinJob, toggleFavoriteJob, setShowColumnConfig,
  } = props

  const bulkActions = [
    { id: 'publish', label: 'Publicar', icon: <Share2 className="w-3.5 h-3.5 text-lia-text-secondary" />, onClick: handleJobPublish },
    { id: 'insights', label: 'Insights', icon: <Brain className="w-3.5 h-3.5 text-wedo-cyan" />, onClick: handleJobInsights },
    { id: 'duplicate', label: 'Duplicar', icon: <Copy className="w-3.5 h-3.5 text-lia-text-secondary" />, onClick: handleJobDuplicate },
    { id: 'toggle_status', label: getSelectedJobsHaveActiveStatus() ? 'Pausar' : 'Ativar',
      icon: getSelectedJobsHaveActiveStatus() ? <X className="w-3.5 h-3.5 text-lia-text-secondary" /> : <CheckCircle2 className="w-3.5 h-3.5 text-lia-text-secondary" />,
      onClick: handleJobToggleStatus },
    { id: 'assign_recruiter', label: 'Recrutador', icon: <UserCheck className="w-3.5 h-3.5 text-lia-text-secondary" />, onClick: handleJobAssignRecruiter },
  ]

  return (
    <div className="flex-1 flex flex-col min-h-0 overflow-hidden">
      {!showExpandedLIA && !showInlineChat && (
        <div className="flex-shrink-0 flex items-center justify-between gap-4 mt-3 mb-2">
          <LIAToolbarBrainButton isOpen={showExpandedLIA} onClick={() => setShowExpandedLIA(true)} />
          <div className="flex items-center gap-3">
            {selectedJobsForBatch.size > 0 && (
              <Badge className="bg-lia-bg-tertiary text-lia-text-primary border-lia-border-default dark:bg-lia-bg-secondary dark:border-lia-border-default text-xs font-bold">
                🎯 {selectedJobsForBatch.size}
              </Badge>
            )}
            {selectedJobsForBatch.size === 0 && filteredJobs.length > 0 && (
              <Button variant="outline" size="sm" onClick={selectAllJobs} className="gap-2 text-xs h-8 px-3">
                <CheckCircle className="w-3 h-3" /> Selecionar Todos
              </Button>
            )}
            <Button
              variant={showTableFiltersPanel ? "primary" : "outline"} size="sm"
              className={`gap-2 text-xs h-8 px-3 ${showTableFiltersPanel ? 'bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover dark:bg-lia-btn-primary-bg dark:hover:bg-lia-btn-primary-hover text-white' : ''}`}
              onClick={() => setShowTableFiltersPanel(!showTableFiltersPanel)} title="Filtrar resultados da tabela"
            >
              <Target className="w-3 h-3" /> Filtros
              {getActiveJobFiltersCount() > 0 && (
                <Badge variant="secondary" className="bg-lia-btn-primary-bg text-lia-btn-primary-text dark:bg-lia-btn-primary-bg ml-1 text-xs font-bold">{getActiveJobFiltersCount()}</Badge>
              )}
            </Button>
            <Button
              variant={showColumnConfig ? "primary" : "outline"} size="sm"
              className={`gap-2 text-xs h-8 px-3 ${showColumnConfig ? 'bg-lia-btn-primary-bg hover:bg-black dark:bg-lia-btn-primary-bg dark:hover:bg-lia-btn-primary-hover text-white' : ''}`}
              onClick={handleToggleColumnConfig} title="Configurar colunas da tabela"
            >
              <ChevronsLeftRight className="w-3 h-3" /> Colunas
              <Badge variant="secondary" className={`ml-1 text-xs ${showColumnConfig ? 'bg-lia-btn-primary-hover text-white dark:bg-lia-bg-tertiary font-bold' : 'bg-lia-bg-tertiary text-lia-text-primary dark:bg-lia-bg-elevated'}`}>6</Badge>
            </Button>
          </div>
        </div>
      )}

      <div className="flex-shrink-0 flex items-center justify-between mb-2">
        <div className="text-xs text-lia-text-primary flex items-center gap-3">
          {(searchTerm || selectedDaysFilter !== 'todas') && (
            <Badge variant="outline" className="text-xs bg-lia-bg-tertiary text-lia-text-primary border-lia-border-default dark:bg-lia-bg-secondary dark:border-lia-border-default font-medium">filtros ativos</Badge>
          )}
        </div>
        <div className="flex items-center gap-2" />
      </div>

      <BulkActionsBar
        selectedCount={selectedJobsForBatch.size} entityLabel="vaga"
        entityIcon={<Briefcase className="w-3.5 h-3.5 text-lia-text-secondary" />}
        onDeselectAll={deselectAllJobs} className="flex-shrink-0 mb-3" actions={bulkActions}
      />

      <div className="flex gap-2 transition-colors motion-reduce:transition-none duration-300 flex-1 min-h-0 overflow-hidden">
        <InlineChatPanel
          showExpandedLIA={showExpandedLIA} showInlineChat={showInlineChat} chatMode={chatMode}
          inlineChatInitialMessage={inlineChatInitialMessage} liaInlineMessages={liaInlineMessages}
          liaInlineLoading={liaInlineLoading} isChatFullscreen={isChatFullscreen} liaWidth={liaWidth}
          isTableCollapsed={isTableCollapsed} isResizingLIA={isResizingLIA} userCollapsedLIA={userCollapsedLIA}
          selectedJobsForBatch={selectedJobsForBatch} liaPromptValue={liaPromptValue}
          onSetLiaPromptValue={setLiaPromptValue} onCloseChat={closeChat}
          onOpenGeneralChat={openGeneralChat} onOpenJobCreationChat={openJobCreationChat}
          onReturnToGeneralChat={returnToGeneralChat} onReturnToLateralPrompt={returnToLateralPrompt}
          onSendMessage={sendLiaInlineMessage} onSetShowExpandedLIA={setShowExpandedLIA}
          onSetUserCollapsedLIA={setUserCollapsedLIA} onSetIsChatFullscreen={setIsChatFullscreen}
          onSetIsResizingLIA={setIsResizingLIA} onSetLiaWidth={setLiaWidth}
          onSetLiaInlineMessages={setLiaInlineMessages} liaInlineMessagesEndRef={liaInlineMessagesEndRef as React.RefObject<HTMLDivElement>}
          onAddRecentItem={onAddRecentItem}
        />

        <TableFiltersPanel
          isOpen={showTableFiltersPanel} onClose={() => setShowTableFiltersPanel(false)}
          searchTerm={searchTerm} onSearchTermChange={setSearchTerm}
          jobFilters={jobFilters} onToggleFilter={toggleJobFilter}
          onClearAllFilters={clearAllJobFilters} getActiveFiltersCount={getActiveJobFiltersCount}
          hasActiveFilters={hasActiveFilters} savedSearches={savedSearches}
          onSaveSearch={saveSearchAsTemplate} onApplySavedSearch={handleApplySavedSearch}
          onRenameSavedSearch={handleRenameSavedSearch} onDeleteSavedSearch={handleDeleteSavedSearch}
        />

        {!(chatMode === 'job-creation' && isChatFullscreen) && (
        <div className={`h-full bg-lia-bg-primary dark:bg-lia-bg-secondary rounded-md transition-[width,height] duration-300 min-w-0 overflow-hidden ${
          isTableCollapsed ? 'w-14 flex-shrink-0' : 'flex-1'
        }`}>
          {isTableCollapsed ? (
            <div className="h-full flex flex-col items-center py-4 gap-3">
              <Button variant="ghost" size="sm" onClick={toggleTableExpansion}
                className="h-10 w-10 p-0 rounded-md hover:bg-lia-bg-tertiary dark:hover:bg-lia-bg-inverse" title="Expandir tabela de vagas">
                <ChevronRight className="w-5 h-5 text-lia-text-primary" />
              </Button>
              <div className="flex flex-col items-center gap-2 text-lia-text-primary">
                <Briefcase className="w-5 h-5" />
                <span className="text-xs font-medium writing-mode-vertical" style={{ writingMode: 'vertical-rl', textOrientation: 'mixed' }} aria-live="polite" aria-atomic="true">
                  Vagas ({filteredJobs.length})
                </span>
              </div>
              {selectedJobsForBatch.size > 0 && (
                <Badge className="bg-lia-btn-primary-bg text-lia-btn-primary-text text-xs px-1.5 py-0.5">{selectedJobsForBatch.size}</Badge>
              )}
            </div>
          ) : (
            <div className="h-full flex flex-col">
              {showInlineChat && (
                <div className="flex-shrink-0 px-3 py-2 bg-lia-bg-secondary dark:bg-lia-bg-secondary flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Briefcase className="w-4 h-4 text-lia-text-primary" />
                    <span className="text-xs font-medium text-lia-text-primary" aria-live="polite" aria-atomic="true">Vagas ({filteredJobs.length})</span>
                  </div>
                  <Button variant="ghost" size="sm" onClick={toggleTableExpansion}
                    className="h-7 w-7 p-0 rounded-md hover:bg-lia-interactive-active dark:hover:bg-lia-bg-inverse" title="Contrair tabela">
                    <ChevronLeft className="w-4 h-4 text-lia-text-primary" />
                  </Button>
                </div>
              )}
              <div className="flex-1 overflow-y-auto" role="status" aria-live="polite" aria-label="Carregando...">
                {isLoadingJobs ? (
                  <div className="flex items-center justify-center py-12" role="status" aria-live="polite" aria-label="Carregando...">
                    <div className="flex items-center gap-2 text-sm text-lia-text-tertiary" role="status" aria-live="polite" aria-label="Carregando...">
                      <Loader2 className="w-5 h-5 animate-spin motion-reduce:animate-none" />
                      <span aria-live="polite" aria-atomic="true">Carregando vagas...</span>
                    </div>
                  </div>
                ) : filteredJobs.length === 0 ? (
                  <EmptyState icon={<Briefcase />} title="Nenhuma vaga cadastrada"
                    description="Crie sua primeira vaga para começar a atrair candidatos."
                    action={{ label: "Criar primeira vaga", onClick: () => setChatMode('job-creation') }} className="h-64" />
                ) : (
                  <JobsCompactTableView
                    isLoading={isLoadingJobs} filteredJobs={filteredJobs}
                    statusOrder={statusOrder} groupedJobs={groupedJobs}
                    jobsColumnOrder={jobsColumnOrder} visibleColumnIds={visibleColumnIds}
                    hookToTableColumnMap={hookToTableColumnMap} jobsColumnWidths={jobsColumnWidths}
                    selectedJobsForBatch={selectedJobsForBatch} pinnedJobs={pinnedJobs}
                    urgentJobs={urgentJobs} favoriteJobs={favoriteJobs}
                    draggedJobColumnId={draggedJobColumnId} dragOverJobColumnId={dragOverJobColumnId}
                    jobsSortColumn={jobsSortColumn} jobsSortDirection={jobsSortDirection}
                    onSelectAll={selectAllJobs} onDeselectAll={deselectAllJobs}
                    onToggleJobSelection={toggleJobSelection} onJobPreview={handleJobPreview}
                    onJobClick={handleJobClick} onToggleUrgent={toggleUrgentJob}
                    onTogglePin={togglePinJob} onToggleFavorite={toggleFavoriteJob}
                    onSort={handleJobsSort} onColumnDragStart={handleJobsColumnDragStart}
                    onColumnDragOver={handleJobsColumnDragOver} onColumnDragLeave={handleJobsColumnDragLeave}
                    onColumnDrop={handleJobsColumnDrop} onColumnDragEnd={handleJobsColumnDragEnd}
                    onColumnResize={startJobsColumnResize}
                  />
                )}
              </div>
            </div>
          )}
        </div>
        )}

        <JobPreviewPanel
          showJobPreview={showJobPreview} previewJob={previewJob}
          activePreviewTab={activePreviewTab} onTabChange={setActivePreviewTab}
          previewWidth={previewWidth} onResize={setPreviewWidth}
          onResizeStart={() => setIsResizingPreview(true)} onResizeEnd={() => setIsResizingPreview(false)}
          onClose={() => { setShowJobPreview(false); setPreviewJob(null); setActivePreviewTab('screening') }}
          onJobClick={handleJobClick} screeningConfig={screeningConfig}
          isLoadingScreeningConfig={isLoadingScreeningConfig}
          jobMetrics={jobMetrics} isLoadingJobMetrics={isLoadingJobMetrics}
        />

        <ColumnConfigPanel
          open={showColumnConfig} onClose={() => setShowColumnConfig(false)}
          columnConfig={columnConfig} visibleColumnIds={visibleColumnIds}
          savedColumnViews={savedColumnViews} toggleColumn={toggleColumn}
          applyColumnView={applyColumnView} deleteColumnView={deleteColumnView}
          saveColumnView={saveColumnView} resetColumnsToDefault={resetColumnsToDefault}
          onToast={(msg) => toast.success(msg)}
        />
      </div>
    </div>
  )
}
