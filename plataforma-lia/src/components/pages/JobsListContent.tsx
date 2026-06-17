"use client"

import React from"react"
import {
  Briefcase, CheckCircle, CheckCircle2, Target, ChevronsLeftRight,
  Brain, Copy, Share2, UserCheck, X, ChevronRight, Loader2,
  Table as TableIcon, LayoutGrid
} from"lucide-react"
import { Button } from"@/components/ui/button"
import { Chip } from "@/components/ui/chip"
import { ViewToggle } from"@/components/ui/view-toggle"
import { ToolbarButton } from"@/components/ui/toolbar-button"
import { EmptyState } from"@/components/ui/empty-state"
import { BulkActionsBar } from"@/components/ui/bulk-actions-bar"
import { TableFiltersPanel } from"@/components/pages/jobs/TableFiltersPanel"
import { JobPreviewPanel } from"@/components/pages/jobs/JobPreviewPanel"
import { JobsCompactTableView } from"@/components/pages/jobs/JobsCompactTableView"
import { JobsKanbanView } from"@/components/pages/jobs/JobsKanbanView"
// Phase 4H — ATS empty state
import { AtsImportSuggestionCard } from "@/components/jobs/AtsImportSuggestionCard"
import { ColumnConfigPanel } from"@/components/pages/jobs/ColumnConfigPanel"
import { toast } from"sonner"
import type { Job } from"@/components/jobs"
import type { ScreeningConfig } from"@/hooks/recruitment/useScreeningConfig"
import type { JobVacancyMetrics } from"@/services/lia-api"
import { useTranslations } from 'next-intl'
import { useUIPreferencesStore } from"@/stores/ui-preferences-store"

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

interface JobsListContentProps {
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
  toggleTableExpansion: () => void
  openJobCreationChat: (initialMessage?: string) => void
  setSearchTerm: (v: string) => void; jobFilters: JobFiltersLocal; toggleJobFilter: (category: string, key: string, value: unknown) => void
  clearAllJobFilters: () => void; hasActiveFilters: () => boolean
  savedSearches: SavedSearchLocal[]; saveSearchAsTemplate: (name: string) => void
  handleApplySavedSearch: (id: string) => void; handleRenameSavedSearch: (id: string, name: string) => void; handleDeleteSavedSearch: (id: string) => void
  showJobPreview: boolean; previewJob: Job | null
  activePreviewTab:"screening" |"pipeline"; setActivePreviewTab: (tab:"screening" |"pipeline") => void
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
  jobsSortColumn: string | null; jobsSortDirection:"asc" |"desc"
  toggleJobSelection: (id: number) => void; handleJobPreview: (job: Job) => void
  handleJobsSort: (column: string) => void; handleJobsColumnDragStart: (id: string, e: React.DragEvent) => void; handleJobsColumnDragOver: (id: string, e: React.DragEvent) => void
  handleJobsColumnDragLeave: () => void; handleJobsColumnDrop: (id: string, e: React.DragEvent) => void
  handleJobsColumnDragEnd: () => void; startJobsColumnResize: (column: string, e: React.MouseEvent) => void
  toggleUrgentJob: (id: number) => void; togglePinJob: (id: number) => void; toggleFavoriteJob: (id: number) => void
  jobsError?: string | null; loadBackendJobs?: () => Promise<void>
  // Phase 4H — ATS rail filter
  activeFilter?: string
  setShowBulkImportModal?: (open: boolean) => void
  /** Lista completa de vagas (sem filtro) para derivar opções de Localização no painel de filtros (RV-019). */
  allJobs?: Job[]
}

export function JobsListContent(props: JobsListContentProps) {
  const {
    selectedJobsForBatch, filteredJobs, isLoadingJobs, isTableCollapsed,
    searchTerm, selectedDaysFilter, showTableFiltersPanel, setShowTableFiltersPanel,
    showColumnConfig, handleToggleColumnConfig, getActiveJobFiltersCount,
    selectAllJobs, deselectAllJobs, handleJobPublish, handleJobInsights,
    handleJobDuplicate, handleJobToggleStatus, handleJobAssignRecruiter,
    getSelectedJobsHaveActiveStatus, toggleTableExpansion,
    openJobCreationChat,
    setSearchTerm, jobFilters, toggleJobFilter, clearAllJobFilters,
    hasActiveFilters, savedSearches, saveSearchAsTemplate, handleApplySavedSearch,
    handleRenameSavedSearch, handleDeleteSavedSearch,
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
    jobsError, loadBackendJobs,
    activeFilter, setShowBulkImportModal,
    allJobs,
  } = props

  const t = useTranslations('jobs')
  const tView = useTranslations('jobsView')
  const jobsViewMode = useUIPreferencesStore((s) => s.jobsViewMode)
  const setJobsViewMode = useUIPreferencesStore((s) => s.setJobsViewMode)

  const bulkActions = [
    { id: 'publish', label: t('publish'), icon: <Share2 className="w-3.5 h-3.5 text-lia-text-secondary" />, onClick: handleJobPublish },
    { id: 'insights', label: t('insights'), icon: <Brain className="w-3.5 h-3.5 text-wedo-cyan-text" />, onClick: handleJobInsights },
    { id: 'duplicate', label: t('duplicate'), icon: <Copy className="w-3.5 h-3.5 text-lia-text-secondary" />, onClick: handleJobDuplicate },
    { id: 'toggle_status', label: getSelectedJobsHaveActiveStatus() ? t('pause') : t('activate'),
      icon: getSelectedJobsHaveActiveStatus() ? <X className="w-3.5 h-3.5 text-lia-text-secondary" /> : <CheckCircle2 className="w-3.5 h-3.5 text-lia-text-secondary" />,
      onClick: handleJobToggleStatus },
    { id: 'assign_recruiter', label: t('recruiter'), icon: <UserCheck className="w-3.5 h-3.5 text-lia-text-secondary" />, onClick: handleJobAssignRecruiter },
  ]

  return (
    <div className="flex-1 flex flex-col min-h-0 overflow-hidden">
      <div className="flex-shrink-0 flex items-center justify-end gap-4 mt-3 mb-2">
          <div className="flex items-center gap-2">
            <ViewToggle
              value={jobsViewMode}
              onChange={(v) => setJobsViewMode(v as 'table' | 'kanban')}
              ariaLabel={tView('toggleAriaLabel')}
              size="md"
              options={[
                { value: 'table', label: tView('table'), icon: TableIcon },
                { value: 'kanban', label: tView('kanban'), icon: LayoutGrid },
              ]}
            />
            {selectedJobsForBatch.size > 0 && (
              <Chip density="relaxed" variant="neutral" muted className="bg-lia-bg-tertiary text-lia-text-primary border-lia-border-default dark:bg-lia-bg-secondary dark:border-lia-border-default">
                🎯 {selectedJobsForBatch.size}
              </Chip>
            )}
            {selectedJobsForBatch.size === 0 && filteredJobs.length > 0 && (
              <ToolbarButton
                size="md"
                onClick={selectAllJobs}
                icon={<CheckCircle />}
              >
                {t('selectAll')}
              </ToolbarButton>
            )}
            <ToolbarButton
              size="md"
              active={showTableFiltersPanel}
              onClick={() => setShowTableFiltersPanel(!showTableFiltersPanel)}
              title={t('filterResults')}
              icon={<Target />}
              trailing={
                getActiveJobFiltersCount() > 0 ? (
                  <Chip density="relaxed" variant="neutral" muted className="ml-1">{getActiveJobFiltersCount()}</Chip>
                ) : null
              }
            >
              {t('filters')}
            </ToolbarButton>
            <ToolbarButton
              size="md"
              active={showColumnConfig}
              onClick={handleToggleColumnConfig}
              title={t('configureColumns')}
              icon={<ChevronsLeftRight />}
              trailing={
                <Chip variant="neutral" muted className={`ml-1 text-xs ${showColumnConfig ? 'bg-lia-bg-tertiary text-lia-text-primary dark:bg-lia-bg-elevated' : 'bg-lia-bg-tertiary text-lia-text-primary dark:bg-lia-bg-elevated'}`}>{visibleColumnIds.length}</Chip>
              }
            >
              {t('columns')}
            </ToolbarButton>
          </div>
        </div>

      <div className="flex-shrink-0 flex items-center justify-between mb-2">
        <div className="text-xs text-lia-text-primary flex items-center gap-3">
          {(searchTerm || selectedDaysFilter !== 'todas') && (
            <Chip density="relaxed" variant="neutral" className="bg-lia-bg-tertiary text-lia-text-primary border-lia-border-default dark:bg-lia-bg-secondary dark:border-lia-border-default font-medium">{t('activeFilters')}</Chip>
          )}
        </div>
        <div className="flex items-center gap-2" />
      </div>

      {jobsViewMode === 'table' && (
        <BulkActionsBar
          selectedCount={selectedJobsForBatch.size} entityLabel={t('newJob')}
          entityIcon={<Briefcase className="w-3.5 h-3.5 text-lia-text-secondary" />}
          onDeselectAll={deselectAllJobs} className="flex-shrink-0 mb-3" actions={bulkActions}
        />
      )}

      <div className="flex gap-2 transition-colors motion-reduce:transition-none duration-300 flex-1 min-h-0 overflow-hidden">
        <TableFiltersPanel
          isOpen={showTableFiltersPanel} onClose={() => setShowTableFiltersPanel(false)}
          searchTerm={searchTerm} onSearchTermChange={setSearchTerm}
          jobFilters={jobFilters} onToggleFilter={toggleJobFilter}
          onClearAllFilters={clearAllJobFilters} getActiveFiltersCount={getActiveJobFiltersCount}
          hasActiveFilters={hasActiveFilters} savedSearches={savedSearches}
          onSaveSearch={saveSearchAsTemplate} onApplySavedSearch={handleApplySavedSearch}
          onRenameSavedSearch={handleRenameSavedSearch} onDeleteSavedSearch={handleDeleteSavedSearch}
          allJobs={allJobs}
        />

        <div className={`h-full bg-lia-bg-primary dark:bg-lia-bg-secondary rounded-xl transition-[width,height] duration-300 min-w-0 overflow-hidden ${
          isTableCollapsed && jobsViewMode === 'table' ? 'w-14 flex-shrink-0' : 'flex-1'
        }`}>
          {jobsViewMode === 'kanban' ? (
            jobsError && !isLoadingJobs ? (
              <div className="flex items-center justify-center py-12">
                <div className="text-center">
                  <p className="text-sm text-red-400 mb-3">{jobsError}</p>
                  {loadBackendJobs && (
                    <Button variant="outline" size="sm" onClick={() => loadBackendJobs()}>
                      {t('tryAgain')}
                    </Button>
                  )}
                </div>
              </div>
            ) : isLoadingJobs ? (
              <div className="flex items-center justify-center py-12" role="status" aria-live="polite" aria-label={t('loadingAriaLabel')}>
                <div className="flex items-center gap-2 text-sm text-lia-text-tertiary">
                  <Loader2 className="w-5 h-5 animate-spin motion-reduce:animate-none" />
                  <span>{t('loadingJobs')}</span>
                </div>
              </div>
            ) : filteredJobs.length === 0 ? (
              <EmptyState
                icon={<Briefcase />}
                title={t('emptyTitle')}
                description={t('emptyDescription')}
                action={{ label: t('emptyAction'), onClick: () => openJobCreationChat() }}
                className="h-64"
              />
            ) : (
              <div className="h-full p-2">
                <JobsKanbanView jobs={filteredJobs} onJobClick={handleJobClick} />
              </div>
            )
          ) : isTableCollapsed ? (
            <div className="h-full flex flex-col items-center py-4 gap-3">
              <Button variant="ghost" size="sm" onClick={toggleTableExpansion}
                className="h-10 w-10 p-0 rounded-lg hover:bg-lia-bg-tertiary dark:hover:bg-lia-bg-inverse" title={t('expandTable')}>
                <ChevronRight className="w-5 h-5 text-lia-text-primary" />
              </Button>
              <div className="flex flex-col items-center gap-2 text-lia-text-primary">
                <Briefcase className="w-5 h-5" />
                <span className="text-xs font-medium writing-mode-vertical" style={{ writingMode: 'vertical-rl', textOrientation: 'mixed' }} aria-live="polite" aria-atomic="true">
                  {t('jobsCount', { count: filteredJobs.length })}
                </span>
              </div>
              {selectedJobsForBatch.size > 0 && (
                <Chip density="relaxed" variant="neutral" muted className="px-1.5 py-0.5">{selectedJobsForBatch.size}</Chip>
              )}
            </div>
          ) : (
            <div className="h-full flex flex-col">
              <div className="flex-1 overflow-y-auto" role="status" aria-live="polite" aria-label={t('loadingAriaLabel')}>
                {jobsError && !isLoadingJobs ? (
                  <div className="flex items-center justify-center py-12">
                    <div className="text-center">
                      <p className="text-sm text-red-400 mb-3">{jobsError}</p>
                      {loadBackendJobs && (
                        <Button variant="outline" size="sm" onClick={() => loadBackendJobs()}>
                          {t('tryAgain')}
                        </Button>
                      )}
                    </div>
                  </div>
                ) : isLoadingJobs ? (
                  <div className="flex items-center justify-center py-12" role="status" aria-live="polite" aria-label={t('loadingAriaLabel')}>
                    <div className="flex items-center gap-2 text-sm text-lia-text-tertiary" role="status" aria-live="polite" aria-label={t('loadingAriaLabel')}>
                      <Loader2 className="w-5 h-5 animate-spin motion-reduce:animate-none" />
                      <span aria-live="polite" aria-atomic="true">{t('loadingJobs')}</span>
                    </div>
                  </div>
                ) : filteredJobs.length === 0 ? (
                  // Phase 4H — ATS empty state takes priority over generic
                  activeFilter === 'ats' ? (
                    <AtsImportSuggestionCard
                      onImport={() => setShowBulkImportModal?.(true)}
                    />
                  ) : (
                    <EmptyState icon={<Briefcase />} title={t('emptyTitle')}
                      description={t('emptyDescription')}
                      action={{ label: t('emptyAction'), onClick: () => openJobCreationChat() }} className="h-64" />
                  )
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
